# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import ntpath
import os
import threading
from datetime import datetime
from gettext import gettext as _
from pathlib import Path

from gi.repository import Gio, GLib, Gtk, Pango
from pykeepass.exceptions import (
    CredentialsError,
    HeaderChecksumError,
    PayloadChecksumError,
)

import passwordsafe.config_manager
from passwordsafe.config_manager import UnlockMethod
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.unlocked_database import UnlockedDatabase


class KeyFileFilter(Gtk.FileFilter):
    """Filter out Keyfiles in the file chooser dialog"""

    def __init__(self):
        super().__init__()

        self.set_name(_("Keyfile"))
        self.add_mime_type("application/octet-stream")
        self.add_mime_type("application/x-keepass2")
        self.add_mime_type("text/plain")
        self.add_mime_type("application/x-iwork-keynote-sffkey")


class UnlockDatabase:
    # pylint: disable=too-many-instance-attributes

    builder = NotImplemented
    parent_widget = NotImplemented
    database_filepath = NotImplemented
    hdy_page = NotImplemented
    unlock_database_stack_switcher = NotImplemented
    keyfile_path = NotImplemented
    composite_keyfile_path = NotImplemented
    overlay = NotImplemented
    unlock_thread = NotImplemented

    def __init__(self, window, widget, filepath):
        self.window = window
        self.parent_widget = widget
        self.database_filepath = filepath

        self.database_manager = None
        self._password = None
        self._unlock_method = None

        self._on_database_locked_changed()

    #
    # Headerbar
    #

    def _set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")
        headerbar.set_subtitle(os.path.basename(self.database_filepath))

        if self.window.tab_visible(self.parent_widget):
            self.window.set_headerbar(headerbar)

        self.parent_widget.set_headerbar(headerbar)
        back_button = self.builder.get_object("back_button")
        back_button.connect("clicked", self._on_headerbar_back_button_clicked)

    #
    # Password stack
    #

    def _assemble_stack(self):
        stack = self.builder.get_object("unlock_database_stack")

        self.unlock_database_stack_switcher = self.builder.get_object("unlock_database_stack_switcher")

        pairs = passwordsafe.config_manager.get_last_used_composite_key()
        uri = Gio.File.new_for_path(self.database_filepath).get_uri()
        if passwordsafe.config_manager.get_remember_composite_key() and pairs:
            keyfile_path = None

            for pair in pairs:
                if pair[0] == uri:
                    keyfile_path = pair[1]

            if keyfile_path is not None:
                composite_unlock_select_button = self.builder.get_object("composite_unlock_select_button")
                label = Gtk.Label()
                label.set_text(ntpath.basename(keyfile_path))
                label.set_ellipsize(Pango.EllipsizeMode.END)
                composite_unlock_select_button.set_label(label)

                self.composite_keyfile_path = keyfile_path

        if passwordsafe.config_manager.get_remember_unlock_method():
            stack.set_visible_child(stack.get_child_by_name(passwordsafe.config_manager.get_unlock_method() + "_unlock"))

        # Responsive Container
        self.hdy_page = self.builder.get_object("unlock_database_clamp")

        self.parent_widget.append(self.hdy_page)

        self._connect_events(stack)

    def _connect_events(self, stack):
        password_unlock_button = self.builder.get_object("password_unlock_button")
        password_unlock_button.connect(
            "clicked", self._on_password_unlock_button_clicked)

        keyfile_unlock_button = self.builder.get_object("keyfile_unlock_button")
        keyfile_unlock_button.connect(
            "clicked", self._on_keyfile_unlock_button_clicked)

        composite_unlock_button = self.builder.get_object("composite_unlock_button")
        composite_unlock_button.connect(
            "clicked", self._on_composite_unlock_button_clicked)

        keyfile_unlock_select_button = self.builder.get_object("keyfile_unlock_select_button")
        keyfile_unlock_select_button.connect(
            "clicked", self._on_keyfile_unlock_select_button_clicked)

        composite_unlock_select_button = self.builder.get_object("composite_unlock_select_button")
        composite_unlock_select_button.connect(
            "clicked", self._on_composite_unlock_select_button_clicked)

        password_unlock_entry = self.builder.get_object("password_unlock_entry")
        if stack.get_visible_child_name() == "password_unlock":
            password_unlock_entry.grab_focus()
        password_unlock_entry.connect(
            "activate", self._on_password_unlock_button_clicked)

        composite_unlock_entry = self.builder.get_object("composite_unlock_entry")
        composite_unlock_entry.connect(
            "activate", self._on_composite_unlock_button_clicked)
        if stack.get_visible_child_name() == "composite_unlock":
            composite_unlock_entry.grab_focus()

    #
    # Events
    #

    def _on_headerbar_back_button_clicked(self, _widget: Gtk.Button) -> None:
        database: UnlockedDatabase | None = None
        if self.database_manager:
            for db in self.window.opened_databases:
                db_path: str = db.database_manager.database_path
                if db_path == self.database_manager.database_path:
                    if passwordsafe.config_manager.get_save_automatically():
                        db.save_database()

                    db.cleanup()
                    database = db

        self.window.set_headerbar()
        self.window.close_tab(self.parent_widget, database)

    # Password Unlock

    def _on_password_unlock_button_clicked(self, _widget):
        password_unlock_entry = self.builder.get_object("password_unlock_entry")

        for db in self.window.opened_databases:
            if (db.database_manager.database_path == self.database_filepath
                    and not db.database_locked):
                page_num = self.window.container.page_num(db.parent_widget)
                self.window.container.set_current_page(page_num)
                self.window.close_tab(self.parent_widget)
                self.window.send_notification(_("Safe already opened"))
                return

        entered_pwd = password_unlock_entry.get_text()
        if not entered_pwd:
            return

        if self.database_manager:
            if (entered_pwd == self.database_manager.password
                    and self.database_manager.keyfile_hash is NotImplemented):
                self.parent_widget.remove(self.hdy_page)
                self.database_manager.props.locked = False
            else:
                self._password_unlock_failed()
        else:
            self._unlock_method = UnlockMethod.PASSWORD
            self._password = entered_pwd
            self._open_database()

    # Keyfile Unlock

    def _on_keyfile_unlock_select_button_clicked(self, _widget):
        """cb invoked when we unlock a database via keyfile"""
        keyfile_chooser_dialog = Gtk.FileChooserNative.new(
            _("Choose a keyfile"), self.window, Gtk.FileChooserAction.OPEN, None, None
        )
        keyfile_chooser_dialog.add_filter(KeyFileFilter())

        keyfile_chooser_dialog.connect(
            "response", self.on_dialog_response, keyfile_chooser_dialog
        )
        keyfile_chooser_dialog.show()

    def on_dialog_response(self,
                           dialog: Gtk.Dialog,
                           response: Gtk.ResponseType,
                           _dialog: Gtk.Dialog) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            self.keyfile_path = dialog.get_file().get_path()
            logging.debug("Keyfile selected: %s", self.keyfile_path)

            keyfile_button = self.builder.get_object("keyfile_unlock_select_button")
            style_context = keyfile_button.get_style_context()
            style_context.remove_class("destructive-action")
            style_context.add_class("suggested-action")
            keyfile_button.set_label(os.path.basename(self.keyfile_path))

            # After selecting a keyfile, simulate a keypress on the unlock button
            keyfile_unlock_button = self.builder.get_object("keyfile_unlock_button")
            keyfile_unlock_button.emit("clicked")

        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection canceled")

    def _on_keyfile_unlock_button_clicked(self, _widget):
        if self.database_manager:
            if (self.keyfile_path is not NotImplemented
                    and self.database_manager.keyfile_hash == self.database_manager.create_keyfile_hash(self.keyfile_path)):
                self.parent_widget.remove(self.hdy_page)
                self.keyfile_path = NotImplemented
                self.database_manager.props.locked = False
            else:
                self._keyfile_unlock_failed()
        elif self.keyfile_path is not NotImplemented:
            self._unlock_method = UnlockMethod.KEYFILE
            self._open_database()

    # Composite Unlock

    def _on_composite_unlock_select_button_clicked(self, _widget):
        opening_dialog = Gtk.FileChooserNative.new(
            _("Choose Keyfile"), self.window, Gtk.FileChooserAction.OPEN,
            None, None)
        opening_dialog.add_filter(KeyFileFilter())

        opening_dialog.connect(
            "response", self._on_composite_filechooser_response, opening_dialog
        )
        opening_dialog.show()

    def _on_composite_filechooser_response(self,
                                           dialog: Gtk.Dialog,
                                           response: Gtk.ResponseType,
                                           _dialog: Gtk.Dialog) -> None:
        composite_unlock_select_button = self.builder.get_object("composite_unlock_select_button")
        if response == Gtk.ResponseType.ACCEPT:
            logging.debug("File selected: %s", dialog.get_file().get_path)
            file_path = dialog.get_file().get_path()
            composite_unlock_select_button.set_label(ntpath.basename(file_path))
            self.composite_keyfile_path = file_path

        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection cancelled")

    def _on_composite_unlock_button_clicked(self, _widget):
        composite_unlock_entry = self.builder.get_object("composite_unlock_entry")
        entered_pwd = composite_unlock_entry.get_text()

        if self.database_manager:
            if ((self.composite_keyfile_path is not NotImplemented)
                    and (self.database_manager.keyfile_hash == self.database_manager.create_keyfile_hash(self.composite_keyfile_path))
                    and (entered_pwd == self.database_manager.password)):
                self.parent_widget.remove(self.hdy_page)
                self.database_manager.props.locked = False
            else:
                self._composite_unlock_failed()
        else:
            if (entered_pwd
                    and self.composite_keyfile_path is not NotImplemented):
                self._unlock_method = UnlockMethod.COMPOSITE
                self._password = entered_pwd
                self._open_database()
            else:
                composite_unlock_entry.get_style_context().add_class("error")

    def _set_last_used_composite_key(self):
        if (not passwordsafe.config_manager.get_remember_composite_key()
                or self.composite_keyfile_path is NotImplemented):
            return

        pairs = passwordsafe.config_manager.get_last_used_composite_key()
        uri = Gio.File.new_for_path(self.database_filepath).get_uri()
        pair_array = []
        already_added = False

        for pair in pairs:
            pair_array.append([pair[0], pair[1]])

        for pair in pair_array:
            if pair[0] == uri:
                pair[1] = self.composite_keyfile_path
                already_added = True

        if not already_added:
            pair_array.append([uri, self.composite_keyfile_path])
            passwordsafe.config_manager.set_last_used_composite_key(pair_array)

    #
    # Open Database
    #

    def _open_database_update_entries(self, sensitive):
        if self._unlock_method == UnlockMethod.PASSWORD:
            entry = self.builder.get_object("password_unlock_entry")
            button = self.builder.get_object("password_unlock_button")
            image = self.builder.get_object("password_unlock_button_image")
        elif self._unlock_method == UnlockMethod.KEYFILE:
            entry = self.builder.get_object("keyfile_unlock_select_button")
            button = self.builder.get_object("keyfile_unlock_button")
            image = self.builder.get_object("keyfile_unlock_button_image")
        else:
            entry = self.builder.get_object("composite_unlock_entry")
            button = self.builder.get_object("composite_unlock_button")
            image = self.builder.get_object("composite_unlock_button_image")

        entry.set_sensitive(sensitive)
        button.set_sensitive(sensitive)
        back_button = self.builder.get_object("back_button")
        back_button.set_sensitive(sensitive)
        self.unlock_database_stack_switcher.set_sensitive(sensitive)

        return button, image

    def _open_database(self):
        button, image = self._open_database_update_entries(False)

        spinner = Gtk.Spinner()
        spinner.show()
        spinner.start()

        button.set_child(spinner)

        self.unlock_thread = threading.Thread(
            target=self._open_database_process)
        self.unlock_thread.daemon = True
        self.unlock_thread.start()

    def _open_database_process(self):
        if self._unlock_method == UnlockMethod.PASSWORD:
            password = self._password
            keyfile = None
        elif self._unlock_method == UnlockMethod.KEYFILE:
            password = None
            keyfile = self.keyfile_path
        else:
            password = self._password
            keyfile = self.composite_keyfile_path

        try:
            self.database_manager = DatabaseManager(
                self.database_filepath, password, keyfile)
            GLib.idle_add(self._open_database_success)
        except(OSError, ValueError, AttributeError,
               CredentialsError, PayloadChecksumError, HeaderChecksumError):
            GLib.idle_add(self._open_database_failure)

    def _open_database_failure(self):
        button, image = self._open_database_update_entries(True)
        button.set_icon_name(image)

        if self._unlock_method == UnlockMethod.PASSWORD:
            self._password_unlock_failed()
        elif self._unlock_method == UnlockMethod.KEYFILE:
            if self.database_manager:
                self.database_manager.keyfile_hash = NotImplemented
            self._keyfile_unlock_failed()
        else:
            if self.database_manager:
                self.database_manager.keyfile_hash = NotImplemented
            self._composite_unlock_failed()

    def _open_database_success(self):
        if self._unlock_method == UnlockMethod.KEYFILE:
            self.database_manager.set_keyfile_hash(self.keyfile_path)
        elif self._unlock_method == UnlockMethod.COMPOSITE:
            self.database_manager.set_keyfile_hash(self.composite_keyfile_path)

        if Path(self.database_filepath).suffix == ".kdb":
            self._open_database_failure()
            # NOTE kdb is a an older format for Keepass databases.
            self.window.send_notification(_("The kdb format is not supported"))
            return

        if self._unlock_method == UnlockMethod.COMPOSITE:
            self._set_last_used_composite_key()

        self._password = None
        self.keyfile_path = NotImplemented
        self.composite_keyfile_path = NotImplemented

        if passwordsafe.config_manager.get_remember_unlock_method():
            passwordsafe.config_manager.set_unlock_method(self._unlock_method)

        logging.debug("Opening of database was successful")
        self._open_database_page()

    def _open_database_page(self):
        self._clear_input_fields()
        opened = Gio.File.new_for_path(self.database_filepath)
        passwordsafe.config_manager.set_last_opened_database(opened.get_uri())

        if passwordsafe.config_manager.get_development_backup_mode():
            cache_dir = os.path.join(
                GLib.get_user_cache_dir(), "passwordsafe", "backup"
            )
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            current_time = datetime.now().strftime('%F_%T')
            basename = os.path.splitext(
                ntpath.basename(self.database_filepath))[0]
            backup_name = basename + "_backup_" + current_time + ".kdbx"
            backup = Gio.File.new_for_path(
                os.path.join(cache_dir, backup_name))
            try:
                opened.copy(backup, Gio.FileCopyFlags.NONE)
            except GLib.Error:
                warning_msg = (
                    "Could not copy database file to backup location. This "
                    "most likely happened because the database is located on "
                    "a network drive, and Password Safe doesn't have network "
                    "permission. Either disable development-backup-mode or if "
                    "PasswordSafe runs as Flatpak grant network permission.")
                logging.warning(warning_msg)

        already_added = False
        path_listh = []
        for path in passwordsafe.config_manager.get_last_opened_list():
            path_listh.append(path)
            if path == opened.get_uri():
                already_added = True

        if not already_added:
            path_listh.append(opened.get_uri())
        else:
            path_listh.sort(key=opened.get_uri().__eq__)

        if len(path_listh) > 10:
            path_listh.pop(0)

        passwordsafe.config_manager.set_last_opened_list(path_listh)

        self.parent_widget.remove(self.hdy_page)
        UnlockedDatabase(
            self.window, self.parent_widget, self.database_manager)
        self.database_manager.connect(
            "notify::locked", self._on_database_locked_changed)

    #
    # Helper Functions
    #

    def _clear_input_fields(self):
        password_unlock_entry = self.builder.get_object("password_unlock_entry")
        composite_unlock_entry = self.builder.get_object("composite_unlock_entry")
        password_unlock_entry.set_text("")
        composite_unlock_entry.set_text("")

    def _on_database_locked_changed(self, _database_manager=None, _value=None):
        if (not self.database_manager
            or (self.database_manager
                and self.database_manager.props.locked)):
            self.builder = Gtk.Builder()
            self.builder.add_from_resource(
                "/org/gnome/PasswordSafe/unlock_database.ui")

            self._set_headerbar()
            self._assemble_stack()

    def _composite_unlock_failed(self):
        self.window.send_notification(_("Failed to unlock safe"))

        if self.database_manager:
            self.database_manager.keyfile_hash = NotImplemented

        composite_unlock_select_button = self.builder.get_object(
            "composite_unlock_select_button")
        composite_unlock_entry = self.builder.get_object(
            "composite_unlock_entry")
        composite_unlock_entry.grab_focus()
        composite_unlock_entry.get_style_context().add_class("error")
        composite_unlock_select_button.get_style_context().remove_class(
            "suggested-action")
        composite_unlock_select_button.get_style_context().add_class(
            "destructive-action")
        self._clear_input_fields()

        logging.debug("Could not open database, wrong password")

    def _keyfile_unlock_failed(self):
        self.window.send_notification(_("Failed to unlock safe"))

        if self.database_manager:
            self.database_manager.keyfile_hash = NotImplemented

        keyfile_unlock_select_button = self.builder.get_object(
            "keyfile_unlock_select_button")
        keyfile_unlock_select_button.get_style_context().add_class(
            "destructive-action")
        keyfile_unlock_select_button.set_label(_("Try again"))

        logging.debug("Invalid keyfile chosen")

    def _password_unlock_failed(self):
        self.window.send_notification(_("Failed to unlock safe"))

        password_unlock_entry = self.builder.get_object(
            "password_unlock_entry")
        password_unlock_entry.grab_focus()
        password_unlock_entry.get_style_context().add_class("error")
        self._clear_input_fields()

        logging.info("Could not open database, wrong password")
