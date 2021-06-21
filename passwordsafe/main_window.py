# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import threading
from enum import IntEnum
from gettext import gettext as _

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk

import passwordsafe.config_manager
from passwordsafe.create_database import CreateDatabase
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.notification import Notification  # noqa: F401, pylint: disable=unused-import
from passwordsafe.recent_files_page import RecentFilesPage  # noqa: F401, pylint: disable=unused-import
from passwordsafe.save_dialog import SaveDialog
from passwordsafe.settings_dialog import SettingsDialog
from passwordsafe.unlock_database import UnlockDatabase
from passwordsafe.welcome_page import WelcomePage  # noqa: F401, pylint: disable=unused-import
from passwordsafe.widgets.create_database_headerbar import (  # noqa: F401, pylint: disable=unused-import
    CreateDatabaseHeaderbar,
)
from passwordsafe.widgets.recent_files_headerbar import (  # noqa: F401, pylint: disable=unused-import
    RecentFilesHeaderbar,
)
from passwordsafe.widgets.unlock_database_headerbar import (  # noqa: F401, pylint: disable=unused-import
    UnlockDatabaseHeaderbar,
)


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/main_window.ui")
class MainWindow(Adw.ApplicationWindow):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    class View(IntEnum):
        WELCOME = 0
        RECENT_FILES = 1
        UNLOCK_DATABASE = 2
        UNLOCKED_DATABASE = 3
        CREATE_DATABASE = 4

    __gtype_name__ = "MainWindow"

    database_manager = NotImplemented
    _notification = Notification()
    unlocked_db = None

    _create_database_bin = Gtk.Template.Child()
    create_database_headerbar = Gtk.Template.Child()
    _main_overlay = Gtk.Template.Child()
    _main_view = Gtk.Template.Child()
    _recent_files_page = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _headerbar_stack = Gtk.Template.Child()
    _unlock_database_bin = Gtk.Template.Child()
    unlock_database_headerbar = Gtk.Template.Child()
    unlocked_db_bin = Gtk.Template.Child()

    mobile_layout = GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE
    )
    _view = View.WELCOME

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.application = self.get_application()

        self._main_overlay.add_overlay(self._notification)

        self.assemble_window()
        self.setup_actions()

        if Gio.Application.get_default().development_mode is True:
            passwordsafe.config_manager.set_development_backup_mode(True)

    def send_notification(self, notification: str) -> None:
        self._notification.send_notification(notification)

    def set_headerbar(self, headerbar: Adw.HeaderBar) -> None:
        self.add_headerbar(headerbar)
        self._headerbar_stack.set_visible_child(headerbar)

    def add_headerbar(self, headerbar: Adw.HeaderBar) -> None:
        if not self._headerbar_stack.get_page(headerbar):
            self._headerbar_stack.add_child(headerbar)

    def assemble_window(self) -> None:
        window_size = passwordsafe.config_manager.get_window_size()
        self.set_default_size(window_size[0], window_size[1])

        self.load_custom_css()
        self.apply_theme()
        self.invoke_initial_screen()

        if Gio.Application.get_default().development_mode:
            self.add_css_class("devel")

    def load_custom_css(self) -> None:
        """Load passwordsafe.css and enable it."""
        display = Gdk.Display.get_default()

        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("org/gnome/PasswordSafe/passwordsafe.css")

        self.get_style_context().add_provider_for_display(
            display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def apply_theme(self) -> None:
        """Set the bright/dark theme depending on the configuration"""
        gtk_settings = Gtk.Settings.get_default()

        gtk_settings.set_property(
            "gtk-application-prefer-dark-theme",
            passwordsafe.config_manager.get_dark_theme(),
        )

    def do_size_allocate(self, width: int, height: int, baseline: int) -> None:  # pylint: disable=arguments-differ
        # pylint: disable=arguments-differ
        """Handler for resizing event. It is used to check if
        the layout needs to be updated.

        :param GdkEvent event: event
        """
        new_mobile_layout = width < 700
        if new_mobile_layout != self.props.mobile_layout:
            self.props.mobile_layout = new_mobile_layout

        Adw.ApplicationWindow.do_size_allocate(self, width, height, baseline)

    def invoke_initial_screen(self) -> None:
        """Present the first start screen if required or autoload files

        If the configuration is set to automatically load the last
        opened safe, this function does that. If it is not set to
        autoload, it presents a list of recently loaded files (or
        displays the empty welcome page if there are no recently
        loaded files).
        """
        if self.application.file_list:
            # file_list is appended to when we invoke the app with
            # files as cmd line parameters. (it is also appended to
            # whenever we open a file via app.open_database action). If it is
            # populated, simply load those files and don't show any
            # screens.
            for g_file in self.application.file_list:
                self.start_database_opening_routine(g_file.get_path())
            return

        if passwordsafe.config_manager.get_first_start_screen():
            # simply load the last opened file
            filepath = None
            gfile: Gio.File = Gio.File.new_for_uri(
                passwordsafe.config_manager.get_last_opened_database()
            )
            if Gio.File.query_exists(gfile):
                filepath = gfile.get_path()
                logging.debug("Opening last opened database: %s", filepath)
                self.start_database_opening_routine(filepath)
                return

        # Display the screen with last opened files (or welcome page)
        if not passwordsafe.config_manager.get_last_opened_list():
            logging.debug("No recent files saved")
            self.view = self.View.WELCOME
            return

        if self._recent_files_page.is_empty:
            logging.debug("No recent files")
            self.view = self.View.WELCOME
            return

        self.view = self.View.RECENT_FILES

    #
    # Open Database Methods
    #

    def on_open_database_action(
        self, _action: Gio.Action, _param: GLib.Variant
    ) -> None:
        """Callback function to open a safe."""
        # pylint: disable=too-many-locals
        opening_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for opening an existing keepass safe kdbx file
            _("Choose a Keepass safe"),
            self,
            Gtk.FileChooserAction.OPEN,
            None,
            None,
        )

        keepass_filter = Gtk.FileFilter()
        keepass_filter.add_mime_type("application/x-keepass2")
        keepass_filter.add_pattern("*.kdbx")
        # NOTE: KeePass + version number is a proper name, do not translate
        keepass_filter.set_name(_("KeePass 3.1/4 Database"))
        opening_dialog.add_filter(keepass_filter)

        binary_filter = Gtk.FileFilter()
        binary_filter.add_mime_type("application/octet-stream")
        binary_filter.set_name(_("Any file type"))
        opening_dialog.add_filter(binary_filter)

        opening_dialog.connect(
            "response",
            self._on_open_filechooser_response,
            opening_dialog,
        )
        opening_dialog.show()

    def _on_open_filechooser_response(
        self,
        dialog: Gtk.Dialog,
        response: Gtk.ResponseType,
        _dialog: Gtk.Dialog,
    ) -> None:
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            db_gfile = dialog.get_file()
            db_filename = db_gfile.get_path()
            logging.debug("File selected: %s", db_filename)

            self.start_database_opening_routine(db_filename)
        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection canceled")

    def start_database_opening_routine(self, filepath: str) -> None:
        """Start opening a safe file"""
        unlock_db = UnlockDatabase(self, filepath)
        self._unlock_database_bin.props.child = unlock_db
        unlock_db.grab_focus()
        self.view = self.View.UNLOCK_DATABASE

    #
    # Create Database Methods
    #

    def on_new_database_action(self, _action: Gio.Action, _param: GLib.Variant) -> None:
        """Callback function to create a new safe."""
        creation_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for creating a new keepass safe kdbx file
            _("Choose location for Keepass safe"),
            self,
            Gtk.FileChooserAction.SAVE,
            _("_Create"),
            None,
        )
        creation_dialog.set_current_name(_("Safe") + ".kdbx")
        creation_dialog.set_modal(True)

        filter_text = Gtk.FileFilter()
        # NOTE: KeePass + version number is a proper name, do not translate
        filter_text.set_name(_("KeePass 3.1/4 Database"))
        filter_text.add_mime_type("application/x-keepass2")
        creation_dialog.add_filter(filter_text)

        creation_dialog.connect(
            "response", self._on_create_filechooser_response, creation_dialog
        )
        creation_dialog.show()

    def _on_create_filechooser_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType, _dialog: Gtk.Dialog
    ) -> None:
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            filepath = dialog.get_file().get_path()

            self._spinner.start()
            self._main_view.set_visible_child(self._spinner)

            creation_thread = threading.Thread(
                target=self.create_new_database, args=[filepath]
            )
            creation_thread.daemon = True
            creation_thread.start()

    def create_new_database(self, filepath: str) -> None:
        """invoked in a separate thread to create a new safe."""

        # Copy our stock database file to `filepath`
        stock_db_file: Gio.File = Gio.File.new_for_uri(
            "resource:///org/gnome/PasswordSafe/database.kdbx"
        )
        new_db_file: Gio.File = Gio.File.new_for_path(filepath)
        stock_db_file.copy(new_db_file, Gio.FileCopyFlags.OVERWRITE)

        tab_title: str = os.path.basename(filepath)
        try:
            self.database_manager = DatabaseManager(filepath, "liufhre86ewoiwejmrcu8owe")
        except Exception as err:  # pylint: disable=broad-except
            logging.debug("Could not create safe: %s", err)
            self.send_notification(_("Could not create new Safe"))
        else:
            GLib.idle_add(self.start_database_creation_routine, tab_title)

    def start_database_creation_routine(self, tab_title):
        self._spinner.stop()
        create_database = CreateDatabase(self, self.database_manager)
        self._create_database_bin.props.child = create_database
        self.view = self.View.CREATE_DATABASE

    def _on_save_dialog_response(self, dialog, response, args):
        widget, database = args
        dialog.close()
        if response == Gtk.ResponseType.YES:
            database.cleanup()
            database.save_database()
        elif response == Gtk.ResponseType.NO:
            database.cleanup()

    def save_window_size(self):
        width = self.get_width()
        height = self.get_height()
        logging.debug("Saving window geometry: (%s, %s)", width, height)
        passwordsafe.config_manager.set_window_size([width, height])

    def do_close_request(self) -> bool:  # pylint: disable=arguments-differ
        """This is invoked when the window close button is pressed.

        Only the app.quit action is called. This action cleans up stuff
        and will invoke the on_application_shutdown() method.

        The true value returned ensures that the destroy method is not
        called yet.
        """
        self.application.activate_action("quit")
        return True

    def setup_actions(self):
        sort_action = self.application.settings.create_action("sort-order")
        self.add_action(sort_action)

        selection_action = Gio.SimpleAction.new("db.selection", GLib.VariantType("s"))
        self.add_action(selection_action)
        selection_action.connect("activate", self.execute_database_action)

        about_action = Gio.SimpleAction.new("about", None)
        self.add_action(about_action)
        about_action.connect("activate", self.on_about_action)

        settings_action = Gio.SimpleAction.new("settings", None)
        self.add_action(settings_action)
        settings_action.connect("activate", self.on_settings_action)

        new_database_action = Gio.SimpleAction.new("new_database", None)
        self.add_action(new_database_action)
        new_database_action.connect("activate", self.on_new_database_action)

        open_database_action = Gio.SimpleAction.new("open_database", None)
        self.add_action(open_database_action)
        open_database_action.connect("activate", self.on_open_database_action)

        actions = [
            "db.save",
            "db.save_dirty",
            "db.lock",
            "db.add_entry",
            "db.add_group",
            "db.settings",
            "db.search",
            "go_back",
            "element.delete",
            "entry.duplicate",
            "entry.references",
            "element.properties",
        ]

        # The save_dirty action differs to save in that it is set as disabled
        # by default, and it is used by the main menu to determine if the button
        # should be set to sensitive.
        for action in actions:
            simple_action = Gio.SimpleAction.new(action, None)
            if action == "db.save_dirty":
                simple_action.set_enabled(False)

            simple_action.connect("activate", self.execute_database_action)
            self.add_action(simple_action)

    def execute_database_action(self, action, param):
        # pylint: disable=too-many-branches
        action_db = self.unlocked_db
        if action_db is None:
            return

        action_db.start_database_lock_timer()
        name = action.props.name

        if name == "element.delete":
            action_db.on_element_delete_action()
        elif name == "entry.duplicate":
            action_db.on_entry_duplicate_action()
        elif name == "entry.references":
            action_db.show_references_dialog()
        elif name == "element.properties":
            action_db.show_properties_dialog()
        elif name == "db.settings":
            action_db.show_database_settings()
        elif name == "db.selection":
            action_db.selection_mode_headerbar.on_selection_action(param)
        elif name in ["db.save", "db.save_dirty"]:
            action_db.save_safe()
        elif name == "db.lock":
            action_db.lock_safe()
        elif name == "go_back":
            action_db.go_back()
        elif name in ["db.add_entry", "db.add_group"]:
            if (
                action_db.props.database_locked
                or action_db.props.selection_mode
                or action_db.in_edit_page
                or action_db.props.search_active
            ):
                return

            if name == "db.add_entry":
                action_db.on_add_entry_action()
            else:
                action_db.on_add_group_action()

        elif name == "db.search":
            if not (
                action_db.props.database_locked
                or action_db.props.selection_mode
                or action_db.in_edit_page
            ):
                action_db.props.search_active = True

    def on_about_action(self, _action: Gio.Action, _param: GLib.Variant) -> None:
        """Invoked when we click "about" in the main menu"""
        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/PasswordSafe/about_dialog.ui"
        )
        about_dialog = builder.get_object("about_dialog")
        about_dialog.set_transient_for(self)
        about_dialog.show()

    def on_settings_action(self, _action: Gio.Action, _param: GLib.Variant) -> None:
        SettingsDialog(self).present()

    @Gtk.Template.Callback()
    def on_back_button_pressed(
        self,
        _gesture: Gtk.GestureClick,
        _n_press: int,
        _event_x: float,
        _event_y: float,
    ) -> None:
        self.lookup_action("go_back").activate()

    @property
    def view(self) -> View:
        return self._view

    @view.setter  # type: ignore
    def view(self, new_view: View) -> None:
        stack = self._main_view
        headerbar_stack = self._headerbar_stack

        self._view = new_view

        if new_view == self.View.WELCOME:
            stack.props.visible_child_name = "welcome"
            headerbar_stack.props.visible_child_name = "recent_files"
        elif new_view == self.View.RECENT_FILES:
            stack.props.visible_child_name = "recent_files"
            headerbar_stack.props.visible_child_name = "recent_files"
        elif new_view == self.View.UNLOCK_DATABASE:
            stack.props.visible_child_name = "unlock_database"
            headerbar_stack.props.visible_child_name = "unlock_database"
        elif new_view == self.View.UNLOCKED_DATABASE:
            stack.props.visible_child_name = "unlocked"
        elif new_view == self.View.CREATE_DATABASE:
            stack.props.visible_child_name = "create_database"
            headerbar_stack.props.visible_child_name = "create_database"
