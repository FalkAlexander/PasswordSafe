# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, Gtk

import passwordsafe.config_manager as config
from passwordsafe import const
from passwordsafe.main_window import MainWindow
from passwordsafe.save_dialog import SaveDialog

if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.unlocked_database import UnlockedDatabase


class Application(Gtk.Application):

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
        if self.window.unlocked_db:
            self.window.unlocked_db.cleanup()

        Gtk.Application.do_shutdown(self)

    def setup_actions(self):
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit_action)
        self.add_action(quit_action)

    def on_quit_action(self, _action: Gio.Action, _param: GLib.Variant) -> None:
        database = self.window.unlocked_db
        is_database_dirty = database.database_manager.is_dirty

        if not database:
            GLib.idle_add(self.quit)

        if is_database_dirty:
            if config.get_save_automatically():
                database.save_database()
                GLib.idle_add(self.quit)
                return

            save_dialog = SaveDialog(self.window)
            save_dialog.connect("response", self._on_save_dialog_response)
            save_dialog.show()

        else:
            GLib.idle_add(self.quit)

    def _on_save_dialog_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType
    ) -> None:
        dialog.close()

        if response == Gtk.ResponseType.YES:  # Save
            database = self.window.unlocked_db
            database.database_manager.save_database()
            GLib.idle_add(self.quit)

        elif response == Gtk.ResponseType.NO:  # Discard
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
