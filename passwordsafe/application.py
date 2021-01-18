# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from gettext import gettext as _
from typing import Any, Dict, List, Optional

from gi.repository import Gio, GLib, Gtk, Handy

import passwordsafe.config_manager as config
from passwordsafe.main_window import MainWindow
from passwordsafe.quit_dialog import QuitDialog
from passwordsafe.save_dialog import SaveDialog
from passwordsafe.settings_dialog import SettingsDialog

if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.unlocked_database import UnlockedDatabase


class Application(Gtk.Application):

    _save_handler_ids: Dict[UnlockedDatabase, int] = {}
    window: MainWindow = None
    file_list: List[Gio.File] = []
    development_mode = False
    application_id = "org.gnome.PasswordSafe"
    settings = Gio.Settings.new(application_id)

    def __init__(self, *args, **_kwargs):
        app_flags = Gio.ApplicationFlags.HANDLES_OPEN
        super().__init__(*args, application_id=self.application_id, flags=app_flags)

        self.set_resource_base_path("/org/gnome/PasswordSafe")

        # debug level logging option
        self.add_main_option("debug", ord("d"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE,
                             "Enable debug logging",
                             None)

    def do_startup(self):  # pylint: disable=arguments-differ
        Gtk.Application.do_startup(self)
        GLib.set_application_name('Password Safe')
        GLib.set_prgname("Password Safe")

        Handy.init()
        self.connect("open", self.file_open_handler)
        self.connect("shutdown", self._on_shutdown_action)
        self.assemble_application_menu()

    def do_handle_local_options(        # pylint: disable=arguments-differ
        self, options: GLib.VariantDict
    ) -> int:
        """
        :returns int: If you have handled your options and want to exit
            the process, return a non-negative option, 0 for success, and
            a positive value for failure. To continue, return -1 to let
            the default option processing continue.
        """
        #  convert GVariantDict -> GVariant -> dict
        options = options.end().unpack()

        # set up logging depending on the verbosity level
        loglevel = logging.INFO
        if self.development_mode or 'debug' in options:
            loglevel = logging.DEBUG
            # Don't clutter our log output with debug msg of the
            # pykeepass module it is very noisy.
            pykeepass_logger = logging.getLogger("pykeepass")
            pykeepass_logger.setLevel(logging.INFO)

        logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s",
                            datefmt='%d-%m-%y %H:%M:%S', level=loglevel)

        return -1

    def do_activate(self):  # pylint: disable=arguments-differ
        if self.window:
            # Window exists already eg if we invoke us a 2nd time.
            # Just present the existing one.
            self.window.present()
            return
        self.window = MainWindow(
            application=self, title="Password Safe",
            icon_name=self.application_id)

        self.add_menubutton_popover_actions()
        self.window.add_row_popover_actions()
        self.window.add_database_menubutton_popover_actions()
        self.window.add_selection_actions()
        self.add_global_accelerators()

        self.window.present()

    def assemble_application_menu(self):
        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.on_settings_menu_clicked)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_menu_clicked)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)

        self.add_action(settings_action)
        self.add_action(about_action)
        self.add_action(quit_action)

    def on_settings_menu_clicked(self, action, param):
        SettingsDialog(self.window).on_settings_menu_clicked(action, param)

    def on_about_menu_clicked(self, _action: Gio.SimpleAction, _param: None) -> None:
        """Invoked when we click "about" in the main menu"""
        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/PasswordSafe/about_dialog.ui"
        )
        about_dialog = builder.get_object("about_dialog")
        about_dialog.set_transient_for(self.window)
        about_dialog.show()

    def on_quit(self, _action: Optional[Gio.SimpleAction] = None,
                _data: Any = None) -> None:
        unsaved_databases_list = []
        self.window.databases_to_save.clear()

        for database in self.window.opened_databases:
            if (database.database_manager.is_dirty
                    and not database.database_manager.save_running):
                unsaved_databases_list.append(database)

        if config.get_save_automatically():
            if not unsaved_databases_list:
                GLib.idle_add(self.quit)

            for database in unsaved_databases_list:
                self._save_handler_ids[database] = database.database_manager.connect(
                    "save-notification",
                    self._on_automatic_save_callback,
                    database,
                    unsaved_databases_list,
                )
                database.save_database(True)
            return

        if len(unsaved_databases_list) == 1:
            database = unsaved_databases_list[0]
            save_dialog = SaveDialog(self.window)
            save_dialog.connect("response", self._on_save_dialog_response, database)
            save_dialog.show()

        elif len(unsaved_databases_list) > 1:
            # Multiple unsaved files, ask which to save
            quit_dialog = QuitDialog(self.window, unsaved_databases_list)
            quit_dialog.connect("response", self._on_quit_dialog_response)
            quit_dialog.show()

        else:
            GLib.idle_add(self.quit)

    def _on_quit_dialog_response(self,
                                 dialog: Gtk.Dialog,
                                 response: Gtk.ResponseType) -> None:
        dialog.close()
        if response != Gtk.ResponseType.OK:
            self.window.databases_to_save.clear()
            return

        for database in self.window.databases_to_save:
            database.save_database()

        GLib.idle_add(self.quit)

    def _on_save_dialog_save_notification(
        self, _db_manager: DatabaseManager, value: bool, database: UnlockedDatabase
    ) -> None:
        database.database_manager.disconnect(self._save_handler_ids[database])
        self._save_handler_ids.pop(database)
        if value:
            GLib.idle_add(self.quit)
        else:
            self.window.notify(_("Unable to Quit: Could not save Safe"))

    def _on_save_dialog_response(self,
                                 dialog: Gtk.Dialog,
                                 response: Gtk.ResponseType,
                                 database: UnlockedDatabase) -> None:
        dialog.close()
        if response == Gtk.ResponseType.YES:  # Save
            self._save_handler_ids[database] = database.database_manager.connect(
                "save-notification", self._on_save_dialog_save_notification, database
            )
            database.database_manager.save_database(True)

        elif response == Gtk.ResponseType.NO:  # Discard
            GLib.idle_add(self.quit)

    def _on_automatic_save_callback(
        self,
        _db_manager: DatabaseManager,
        saved: bool,
        database: UnlockedDatabase,
        unsaved_database_list: List[UnlockedDatabase],
    ) -> None:
        """Makes sure all safes that were scheduled for autmatic save
        are correctly saved. Quits when all safes are saved."""
        database.database_manager.disconnect(self._save_handler_ids[database])
        self._save_handler_ids.pop(database)
        if saved and database in unsaved_database_list:
            unsaved_database_list.remove(database)

        if not unsaved_database_list:
            GLib.idle_add(self.quit)

    def _on_shutdown_action(self, _action: Gio.SimpleAction) -> None:
        """Activated on shutdown signal. Cleans all remaining processes."""
        self.window.save_window_size()
        for database in self.window.opened_databases:
            database.cleanup()

    def add_menubutton_popover_actions(self):
        new_action = Gio.SimpleAction.new("new", None)
        new_action.connect("activate", self.window.create_filechooser)
        self.add_action(new_action)

        open_action = Gio.SimpleAction.new("open", None)
        open_action.connect("activate", self.window.open_filechooser)
        self.add_action(open_action)

    def file_open_handler(self, _application, g_file_list, _amount, _ukwn):
        for g_file in g_file_list:
            self.file_list.append(g_file)
            if self.window is not None:
                self.window.start_database_opening_routine(g_file.get_path())

        self.do_activate()

    def add_global_accelerators(self):
        self.window.add_global_accelerator_actions()
        self.set_accels_for_action("app.settings", ["<primary>comma"])
        self.set_accels_for_action("app.open", ["<primary>o"])
        self.set_accels_for_action("app.new", ["<primary><Shift>n"])
        self.set_accels_for_action("app.db.save", ["<primary>s"])
        self.set_accels_for_action("app.db.lock", ["<primary>l"])
        self.set_accels_for_action("app.db.add_entry", ["<primary>n"])
        self.set_accels_for_action("app.db.add_group", ["<primary>g"])
        self.set_accels_for_action("app.undo", ["<primary>z"])
        self.set_accels_for_action("app.redo", ["<primary>y"])
        self.set_accels_for_action("app.go_back", ["Escape"])
        self.set_accels_for_action("app.quit", ["<primary>q"])
