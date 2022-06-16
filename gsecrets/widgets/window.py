# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from enum import IntEnum
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, GObject, Gtk

import gsecrets.config_manager
from gsecrets.create_database import CreateDatabase
from gsecrets.database_manager import DatabaseManager
from gsecrets.save_dialog import SaveDialog
from gsecrets.settings_dialog import SettingsDialog
from gsecrets.unlock_database import UnlockDatabase


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/window.ui")
class Window(Adw.ApplicationWindow):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    class View(IntEnum):
        WELCOME = 0
        UNLOCK_DATABASE = 2
        UNLOCKED_DATABASE = 3
        CREATE_DATABASE = 4

    __gtype_name__ = "Window"

    unlocked_db = None

    _create_database_bin = Gtk.Template.Child()
    _main_view = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _toast_overlay = Gtk.Template.Child()
    _unlock_database_bin = Gtk.Template.Child()
    unlocked_db_bin = Gtk.Template.Child()

    mobile_layout = GObject.Property(type=bool, default=False)
    _view = View.WELCOME

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.application = self.get_application()

        self.assemble_window()
        self.setup_actions()

        if self.application.development_mode is True:
            gsecrets.config_manager.set_development_backup_mode(True)

    def send_notification(self, notification: str) -> None:
        toast = Adw.Toast.new(notification)
        self._toast_overlay.add_toast(toast)

    def assemble_window(self) -> None:
        window_size = gsecrets.config_manager.get_window_size()
        self.set_default_size(window_size[0], window_size[1])

        self.apply_theme()

        if self.props.application.development_mode:
            self.add_css_class("devel")

    def apply_theme(self) -> None:
        """Set the bright/dark theme depending on the configuration"""
        manager = Adw.StyleManager.get_default()
        if not manager.props.system_supports_color_schemes:
            dark_theme = gsecrets.config_manager.get_dark_theme()
            if dark_theme:
                manager.props.color_scheme = Adw.ColorScheme.PREFER_DARK
            else:
                manager.props.color_scheme = Adw.ColorScheme.DEFAULT

    def do_enable_debugging(  # pylint: disable=arguments-differ
        self, toggle: bool
    ) -> bool:
        if not self.application.development_mode:
            logging.warning("The inspector is not enabled in non-development builds")
            return False

        return Adw.ApplicationWindow.do_enable_debugging(self, toggle)

    def do_size_allocate(
        self, width: int, height: int, baseline: int
    ) -> None:  # pylint: disable=arguments-differ
        # pylint: disable=arguments-differ
        """Handler for resizing event. It is used to check if
        the layout needs to be updated."""
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
        if gsecrets.config_manager.get_first_start_screen():
            # simply load the last opened file
            filepath = None
            gfile: Gio.File = Gio.File.new_for_uri(
                gsecrets.config_manager.get_last_opened_database()
            )
            if gfile.query_exists():
                filepath = gfile.get_path()
                logging.debug("Opening last opened database: %s", filepath)
                self.start_database_opening_routine(filepath)
                return

        # Display the screen with last opened files (or welcome page)
        if not gsecrets.config_manager.get_last_opened_list():
            logging.debug("No recent files saved")
            self.view = self.View.WELCOME
            return

        self.view = self.View.WELCOME

    #
    # Open Database Methods
    #

    def on_open_database_action(self, _action: Gio.Action, param: GLib.Variant) -> None:
        """Callback function to open a safe."""
        # pylint: disable=too-many-locals
        if param and (path := param.get_string()):
            self._open_database_in_window(path)
            return

        opening_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for opening an existing keepass safe kdbx file
            _("Select Safe"),
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
            if db_gfile is None:
                logging.debug("No file selected")
                return

            db_filename = db_gfile.get_path()
            logging.debug("File selected: %s", db_filename)

            self._open_database_in_window(db_filename)

        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection canceled")

    def _open_database_in_window(self, filepath):
        if self.unlocked_db:
            auto_save = gsecrets.config_manager.get_save_automatically()
            is_dirty = self.unlocked_db.database_manager.is_dirty
            is_current = self.unlocked_db.database_manager.path == filepath
            is_locked = self.unlocked_db.database_manager.props.locked

            if is_locked:
                if is_dirty and not is_current:
                    app = self.props.application
                    window = app.new_window()
                    window.start_database_opening_routine(filepath)
                    window.present()
                else:
                    if is_current:
                        self.view = self.View.UNLOCK_DATABASE
                        return

                    if auto_save:
                        self.unlocked_db.auto_save_database()

                    self.unlocked_db.do_dispose()
                    self.unlocked_db = None
                    self.start_database_opening_routine(filepath)

            else:
                if not is_current:
                    app = self.props.application
                    window = app.new_window()
                    window.start_database_opening_routine(filepath)
                    window.present()
                else:
                    self.send_notification(_("Safe is already open"))

        else:
            self.start_database_opening_routine(filepath)

    def start_database_opening_routine(self, filepath: str) -> None:
        """Start opening a safe file"""
        # TODO Use a Gio.File instead of a path.
        database = Gio.File.new_for_path(filepath)
        unlock_db = UnlockDatabase(self, database)
        self._unlock_database_bin.props.child = unlock_db
        self.view = self.View.UNLOCK_DATABASE

    #
    # Create Database Methods
    #

    def on_new_database_action(self, _action: Gio.Action, _param: GLib.Variant) -> None:
        """Callback function to create a new safe."""
        creation_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for creating a new keepass safe kdbx file
            _("Create Safe"),
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
            gfile = dialog.get_file()
            if gfile is None:
                logging.debug("No file selected")
                return

            filepath = gfile.get_path()
            if self.unlocked_db:
                auto_save = gsecrets.config_manager.get_save_automatically()
                is_dirty = self.unlocked_db.database_manager.is_dirty
                is_open = self.application.is_safe_open(filepath)
                is_locked = self.unlocked_db.database_manager.props.locked

                if is_open:
                    self.send_notification(
                        _("Cannot create Safe: Safe is already open")
                    )
                    return

                if is_locked:
                    if is_dirty and not auto_save:
                        app = self.props.application
                        window = app.new_window()
                        window.create_new_database(filepath)
                        window.present()
                    else:
                        if auto_save:
                            self.unlocked_db.auto_save_database()

                        self.unlocked_db.do_dispose()
                        self.unlocked_db = None
                        self.create_new_database(filepath)
                else:
                    app = self.props.application
                    window = app.new_window()
                    window.create_new_database(filepath)
                    window.present()

            else:
                self.create_new_database(filepath)

    def create_new_database(self, filepath: str) -> None:
        """Copy stock database onto filepath."""
        self._spinner.start()
        self._main_view.set_visible_child_name("spinner")

        stock_db_file: Gio.File = Gio.File.new_for_uri(
            "resource:///org/gnome/World/Secrets/database.kdbx"
        )
        new_db_file: Gio.File = Gio.File.new_for_path(filepath)

        def unlock_callback(database_manager, result):
            try:
                database_manager.unlock_finish(result)
            except GLib.Error as err:
                logging.debug("Could not unlock safe: %s", err.message)
                self.invoke_initial_screen()
                self.send_notification(_("Could not create new Safe"))
            else:
                create_database = CreateDatabase(self, database_manager)
                self._create_database_bin.props.child = create_database
                self.view = self.View.CREATE_DATABASE
            finally:
                self._spinner.stop()

        def copy_callback(gfile, result):
            try:
                gfile.copy_finish(result)
            except GLib.Error as err:
                logging.debug("Could not copy new database: %s", err.message)
                self.invoke_initial_screen()
                self.send_notification(_("Could not create new Safe"))
                self._spinner.stop()
            else:
                database_manager = DatabaseManager(filepath)
                database_manager.unlock_async(
                    "liufhre86ewoiwejmrcu8owe",
                    callback=unlock_callback,
                )

        stock_db_file.copy_async(
            new_db_file,
            Gio.FileCopyFlags.OVERWRITE,
            GLib.PRIORITY_DEFAULT,
            None,
            None,
            None,
            copy_callback,
        )

    def save_window_size(self):
        width = self.get_width()
        height = self.get_height()
        logging.debug("Saving window geometry: (%s, %s)", width, height)
        gsecrets.config_manager.set_window_size([width, height])

    def do_close_request(self) -> bool:  # pylint: disable=arguments-differ
        """This is invoked when the window close button is pressed.

        Only the app.quit action is called. This action cleans up stuff
        and will invoke the on_application_shutdown() method.

        Return: True to stop other handlers from being invoked for the signal.
        """
        if not self.unlocked_db:
            self.save_window_size()
            return False

        is_database_dirty = self.unlocked_db.database_manager.is_dirty

        def on_save(dbm, result):
            try:
                dbm.save_finish(result)
            except GLib.Error as err:
                logging.error("Could not save Safe: %s", err.message)
                self.send_notification(_("Could not save Safe"))
            else:
                self.save_window_size()
                self.destroy()

        if is_database_dirty:
            if gsecrets.config_manager.get_save_automatically():
                self.unlocked_db.database_manager.save_async(on_save)
                return True  # Do not close the window until saved

            save_dialog = SaveDialog(self)
            save_dialog.show()
            return True

        self.save_window_size()
        return False

    def do_unrealize(self):  # pylint: disable=arguments-differ
        if self.unlocked_db:
            self.unlocked_db.cleanup()

        Gtk.Widget.do_unrealize(self)

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

        open_database_action = Gio.SimpleAction.new(
            "open_database", GLib.VariantType("s")
        )
        self.add_action(open_database_action)
        open_database_action.connect("activate", self.on_open_database_action)

        actions = [
            "db.save",
            "db.save_dirty",
            "db.lock",
            "db.add_entry",
            "db.add_group",
            "db.settings",
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

        # We don't want to allow actions if the db is locked.
        # TODO Actions should be disabled instead.
        if name == "db.lock":
            action_db.lock_safe()
        elif action_db.props.database_locked:
            return

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
            action_db.save_database()
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

    def on_about_action(self, _action: Gio.Action, _param: GLib.Variant) -> None:
        """Invoked when we click "about" in the main menu"""
        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/World/Secrets/about_dialog.ui"
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

        self._view = new_view

        if new_view == self.View.WELCOME:
            stack.props.visible_child_name = "welcome"
        elif new_view == self.View.UNLOCK_DATABASE:
            stack.props.visible_child_name = "unlock_database"
        elif new_view == self.View.UNLOCKED_DATABASE:
            stack.props.visible_child_name = "unlocked"
        elif new_view == self.View.CREATE_DATABASE:
            stack.props.visible_child_name = "create_database"
