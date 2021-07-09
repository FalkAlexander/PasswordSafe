# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import threading
from gettext import gettext as _

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk

import passwordsafe.config_manager
from passwordsafe.container_page import ContainerPage
from passwordsafe.create_database import CreateDatabase
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.notification import Notification
from passwordsafe.recent_files_page import RecentFilesPage
from passwordsafe.save_dialog import SaveDialog
from passwordsafe.settings_dialog import SettingsDialog
from passwordsafe.unlock_database import UnlockDatabase
from passwordsafe.unlocked_database import UnlockedDatabase
from passwordsafe.welcome_page import WelcomePage
from passwordsafe.widgets.recent_files_headerbar import RecentFilesHeaderbar
from passwordsafe.widgets.create_database_headerbar import (  # noqa: F401, pylint: disable=unused-import
    CreateDatabaseHeaderbar,
)


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/main_window.ui")
class MainWindow(Adw.ApplicationWindow):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    __gtype_name__ = "MainWindow"

    database_manager = NotImplemented
    opened_databases: list[UnlockedDatabase] = []
    databases_to_save: list[UnlockedDatabase] = []
    _notification = Notification()

    container = Gtk.Template.Child()
    create_database_headerbar = Gtk.Template.Child()
    _main_overlay = Gtk.Template.Child()
    _main_view = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _headerbar_stack = Gtk.Template.Child()

    mobile_layout = GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.application = self.get_application()
        self.welcome_page = WelcomePage()
        self.recent_files_page = RecentFilesPage()

        self._main_view.add_child(self.welcome_page)
        self._main_view.add_child(self.recent_files_page)
        self._main_overlay.add_overlay(self._notification)

        self._recent_files_headerbar = RecentFilesHeaderbar()
        self.add_headerbar(self._recent_files_headerbar)

        self.assemble_window()
        self.setup_actions()

        if Gio.Application.get_default().development_mode is True:
            passwordsafe.config_manager.set_development_backup_mode(True)

    def send_notification(self, notification: str) -> None:
        self._notification.send_notification(notification)

    def set_headerbar(self, headerbar: Adw.HeaderBar | None = None) -> None:
        if headerbar is None:
            self._headerbar_stack.set_visible_child(self._recent_files_headerbar)
            return

        self.add_headerbar(headerbar)
        self._headerbar_stack.set_visible_child(headerbar)

    def add_headerbar(self, headerbar: Adw.HeaderBar) -> None:
        if not self._headerbar_stack.get_page(headerbar):
            self._headerbar_stack.add_child(headerbar)

    def assemble_window(self) -> None:
        window_size = passwordsafe.config_manager.get_window_size()
        self.set_default_size(window_size[0], window_size[1])

        self.set_headerbar()
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
        self.display_recent_files_list()

    def display_recent_files_list(self) -> None:
        """Shows the list of recently opened files or invokes welcome page"""
        if not passwordsafe.config_manager.get_last_opened_list():
            logging.debug("No recent files saved")
            self.display_welcome_page()
            return

        recent_files_page = RecentFilesPage()

        if recent_files_page.is_empty:
            logging.debug("No recent files")
            self.display_welcome_page()
            return

        self._main_view.set_visible_child(self.recent_files_page)

    def display_welcome_page(self) -> None:
        """Shown when there is no autoloading and no recent files to display"""
        self._main_view.set_visible_child(self.welcome_page)
        self._headerbar_stack.set_visible_child_name("recent_files_headerbar")

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

            database_already_opened = False

            for database in self.opened_databases:
                if database.database_manager.database_path == db_filename:
                    database_already_opened = True
                    page_num = self.container.page_num(database.parent_widget)
                    self.container.set_current_page(page_num)
                    self.send_notification(_("Safe already opened"))

            if database_already_opened is False:
                self.start_database_opening_routine(db_filename)
        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection canceled")

    def start_database_opening_routine(self, filepath: str) -> None:
        """Start opening a safe file"""
        headerbar = self.create_database_headerbar
        tab_title: str = os.path.basename(filepath)
        UnlockDatabase(self, self.create_tab(tab_title, headerbar), filepath)
        self._main_view.set_visible_child(self.container)

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
        self.database_manager = DatabaseManager(filepath, "liufhre86ewoiwejmrcu8owe")
        GLib.idle_add(self.start_database_creation_routine, tab_title)

    def start_database_creation_routine(self, tab_title):
        self._main_view.set_visible_child(self.container)
        self._spinner.stop()
        headerbar = self.create_database_headerbar
        parent_widget = self.create_tab(tab_title, headerbar)
        back_button = headerbar.back_button
        create_database = CreateDatabase(
            self, parent_widget, self.database_manager, back_button
        )
        self.set_headerbar(headerbar)
        parent_widget.append(create_database)

    def create_tab(self, title, headerbar):
        page_instance = ContainerPage(
            headerbar, Gio.Application.get_default().development_mode
        )

        tab_hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        tab_label = Gtk.Label.new(title)
        tab_hbox.prepend(tab_label)

        close_button = Gtk.Button.new_from_icon_name("window-close-symbolic")

        close_button.set_has_frame(False)
        close_button.set_focus_on_click(False)
        close_button.connect("clicked", self.on_tab_close_button_clicked, page_instance)

        tab_hbox.append(close_button)

        self.container.append_page(page_instance, tab_hbox)
        self.container.set_current_page(self.container.page_num(page_instance))
        self.update_tab_bar_visibility()

        return page_instance

    def update_tab_bar_visibility(self):
        if self.container.get_n_pages() > 1:
            self.container.set_show_tabs(True)
        else:
            self.container.set_show_tabs(False)

        if not self.container.get_n_pages():
            self.display_recent_files_list()
        elif not self.container.is_visible():
            self._main_view.set_visible_child(self.container)

    def close_tab(self, child_widget, database=None):
        """Remove a tab from the container.

        If database is defined, it is removed from the list of
        opened_databases

        :param GtkWidget child_widget: tab to close
        :param UnlockedDatabase database: database to remove
        """
        page_num = self.container.page_num(child_widget)
        self.container.remove_page(page_num)
        self.update_tab_bar_visibility()

        if database:
            self.opened_databases.remove(database)

    def on_tab_close_button_clicked(self, _sender, widget):
        page_num = self.container.page_num(widget)

        for database in self.opened_databases:
            if database.window.container.page_num(database.parent_widget) == page_num:
                if database.database_manager.is_dirty:
                    if passwordsafe.config_manager.get_save_automatically():
                        database.cleanup()
                        database.save_database()
                    else:
                        save_dialog = SaveDialog(self)
                        save_dialog.connect(
                            "response",
                            self._on_save_dialog_response,
                            [widget, database],
                        )
                        save_dialog.show()
                else:
                    database.cleanup()
                    self.close_tab(widget, database)

                return

        self.close_tab(widget)

    def _on_save_dialog_response(self, dialog, response, args):
        widget, database = args
        dialog.close()
        if response == Gtk.ResponseType.YES:
            database.cleanup()
            self.close_tab(widget, database)
            database.save_database()
        elif response == Gtk.ResponseType.NO:
            database.cleanup()
            self.close_tab(widget, database)

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

    def find_action_db(self) -> UnlockedDatabase | None:
        """Finds current displayed tab for executing an action."""
        action_db = None

        for database in self.opened_databases:
            if (
                self.tab_visible(database.parent_widget)
                and not database.database_manager.props.locked
            ):
                action_db = database

        return action_db

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
        action_db = self.find_action_db()
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

    def tab_visible(self, tab):
        """Checks that the tab is visible

        :returns: True if the tab is visible
        :rtype: bool
        """
        current_page = self.container.get_current_page()
        return self.container.page_num(tab) == current_page

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
