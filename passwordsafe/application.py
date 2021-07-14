# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, Gtk

import passwordsafe.config_manager as config
from passwordsafe import const
from passwordsafe.main_window import MainWindow
from passwordsafe.quit_dialog import QuitDialog
from passwordsafe.save_dialog import SaveDialog

if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.unlocked_database import UnlockedDatabase


class Application(Gtk.Application):

    _save_handler_ids: dict[UnlockedDatabase, int] = {}
    window: MainWindow = None
    file_list: list[Gio.File] = []
    development_mode = const.IS_DEVEL
    application_id = const.APP_ID
    settings = Gio.Settings.new(application_id)

    def __init__(self, *args, **_kwargs):
        super().__init__(
            *args,
            application_id=self.application_id,
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            resource_base_path="/org/gnome/PasswordSafe",
        )

        # debug level logging option
        self.add_main_option(
            "debug",
            ord("d"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Enable debug logging",
            None,
        )

    def do_startup(self):  # pylint: disable=arguments-differ
        Gtk.Application.do_startup(self)
        Adw.init()

    def do_open(self, gfile_list, _n_files, _hint):  # pylint: disable=arguments-differ
        for gfile in gfile_list:
            if not gfile.query_exists():
                print(_("Error: File {} does not exist").format(gfile.get_path()))
                if self.window is None:
                    self.quit()

            self.file_list.append(gfile)
            if self.window is not None:
                self.window.start_database_opening_routine(gfile.get_path())

        self.do_activate()

    def do_handle_local_options(  # pylint: disable=arguments-differ
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
        if self.development_mode or "debug" in options:
            loglevel = logging.DEBUG
            # Don't clutter our log output with debug msg of the
            # pykeepass module it is very noisy.
            pykeepass_logger = logging.getLogger("pykeepass")
            pykeepass_logger.setLevel(logging.INFO)

        logging.basicConfig(
            format="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%d-%m-%y %H:%M:%S",
            level=loglevel,
        )

        return -1

    def do_activate(self):  # pylint: disable=arguments-differ
        # If the window exists already e.g. if we invoke us a 2nd time,
        # we just present the existing one.
        if self.window:
            self.window.present()
            return

        self.window = MainWindow(application=self)

        self.setup_actions()
        self.add_global_accelerators()

        self.window.present()

    def do_shutdown(self) -> None:  # pylint: disable=arguments-differ
        """Activated on shutdown. Cleans all remaining processes."""
        self.window.save_window_size()
        for database in self.window.opened_databases:
            database.cleanup()

        Gtk.Application.do_shutdown(self)

    def setup_actions(self):
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit_action)
        self.add_action(quit_action)

    def on_quit_action(self, _action: Gio.Action, _param: GLib.Variant) -> None:
        unsaved_databases_list = []
        self.window.databases_to_save.clear()

        for database in self.window.opened_databases:
            if (
                database.database_manager.is_dirty
                and not database.database_manager.save_running
            ):
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

    def _on_quit_dialog_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType
    ) -> None:
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
            self.window.send_notification(_("Unable to Quit: Could not save Safe"))

    def _on_save_dialog_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType, database: UnlockedDatabase
    ) -> None:
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
        unsaved_database_list: list[UnlockedDatabase],
    ) -> None:
        """Makes sure all safes that were scheduled for autmatic save
        are correctly saved. Quits when all safes are saved."""
        database.database_manager.disconnect(self._save_handler_ids[database])
        self._save_handler_ids.pop(database)
        if saved and database in unsaved_database_list:
            unsaved_database_list.remove(database)

        if not unsaved_database_list:
            GLib.idle_add(self.quit)

    def add_global_accelerators(self):
        self.set_accels_for_action("win.settings", ["<primary>comma"])
        self.set_accels_for_action("win.open_database", ["<primary>o"])
        self.set_accels_for_action("win.new_database", ["<primary>n"])
        self.set_accels_for_action("win.db.save", ["<primary>s"])
        self.set_accels_for_action("win.db.search", ["<primary>f"])
        self.set_accels_for_action("win.db.lock", ["<primary>l"])
        self.set_accels_for_action("win.db.add_entry", ["<primary>e"])
        self.set_accels_for_action("win.db.add_group", ["<primary>g"])
        self.set_accels_for_action("win.go_back", ["Escape"])
        self.set_accels_for_action("win.entry.copy_password", ["<primary><Shift>c"])
        self.set_accels_for_action("win.entry.copy_user", ["<primary><Shift>b"])
        self.set_accels_for_action("window.close", ["<primary>q"])
