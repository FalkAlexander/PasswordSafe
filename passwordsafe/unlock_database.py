# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import ntpath
import os
import threading
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

import passwordsafe.config_manager
from passwordsafe import const
from passwordsafe.config_manager import UnlockMethod
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.unlocked_database import UnlockedDatabase
from passwordsafe.utils import KeyFileFilter


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/unlock_database.ui")
class UnlockDatabase(Adw.Bin):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "UnlockDatabase"

    database_filepath = NotImplemented
    keyfile_path = NotImplemented
    keyfile_hash = None
    composite_keyfile_path = NotImplemented

    password_unlock_button = Gtk.Template.Child()
    password_unlock_entry = Gtk.Template.Child()

    composite_unlock_button = Gtk.Template.Child()
    composite_unlock_entry = Gtk.Template.Child()
    composite_unlock_select_button = Gtk.Template.Child()

    keyfile_unlock_select_button = Gtk.Template.Child()
    keyfile_unlock_button = Gtk.Template.Child()

    stack = Gtk.Template.Child()
    stack_switcher = Gtk.Template.Child()

    def __init__(self, window, filepath):
        super().__init__()

        self.window = window
        self.database_filepath = filepath

        self.database_manager = None
        self.headerbar = self.window.unlock_database_headerbar
        self._password = None
        self._unlock_method = None

        # Reset headerbar to initial state if it already exists.
        self.headerbar.title.props.subtitle = os.path.basename(filepath)
        self.headerbar.back_button.props.sensitive = True

        database = self.window.unlocked_db
        if database:
            is_current = database.database_manager.database_path == filepath
            if is_current:
                self.database_manager = database.database_manager

        self._assemble_stack()

    #
    # Password stack
    #

    def _assemble_stack(self):
        pairs = passwordsafe.config_manager.get_last_used_composite_key()
        uri = Gio.File.new_for_path(self.database_filepath).get_uri()
        if passwordsafe.config_manager.get_remember_composite_key() and pairs:
            keyfile_path = None

            for pair in pairs:
                if pair[0] == uri:
                    keyfile_path = pair[1]
                    break

            if keyfile_path is not None:
                keyfile = Gio.File.new_for_path(keyfile_path)
                if keyfile.query_exists():
                    label = ntpath.basename(keyfile_path)
                    self.composite_unlock_select_button.set_label(label)
                    self.composite_keyfile_path = keyfile_path

        if passwordsafe.config_manager.get_remember_unlock_method():
            self.stack.set_visible_child(
                self.stack.get_child_by_name(
                    passwordsafe.config_manager.get_unlock_method() + "_unlock"
                )
            )

    def do_realize(self):  # pylint: disable=arguments-differ
        Gtk.Widget.do_realize(self)
        if self.stack.get_visible_child_name() == "password_unlock":
            self.password_unlock_entry.grab_focus()
        elif self.stack.get_visible_child_name() == "composite_unlock":
            self.composite_unlock_entry.grab_focus()
        else:
            self.keyfile_unlock_button.grab_focus()

    def load_keyfile_callback(self, keyfile, result):
        try:
            gbytes, _etag = keyfile.load_bytes_finish(result)
            if not gbytes:
                raise Exception("IO operation error")

        except Exception as err:  # pylint: disable=broad-except
            logging.debug("Could not set keyfile hash: %s", err)

            if self.stack.get_visible_child_name() == "composite_unlock":
                self.composite_unlock_select_button.set_label(_("Try again"))
                self.composite_unlock_select_button.remove_css_class("suggested-action")
                self.composite_unlock_select_button.add_css_class("destructive-action")
            else:
                self.keyfile_unlock_select_button.set_label(_("Try again"))
                self.keyfile_unlock_select_button.remove_css_class("suggested-action")
                self.keyfile_unlock_select_button.add_css_class("destructive-action")

        else:
            keyfile_hash = GLib.compute_checksum_for_bytes(GLib.ChecksumType.SHA1, gbytes)
            file_path = keyfile.get_path()
            basename = keyfile.get_basename()
            if keyfile_hash:
                self.keyfile_hash = keyfile_hash

            if self._unlock_method == UnlockMethod.COMPOSITE:
                self.composite_unlock_select_button.set_label(basename)
                self.composite_keyfile_path = file_path

                self.composite_unlock_select_button.remove_css_class("destructive-action")
                self.composite_unlock_select_button.add_css_class("suggested-action")
            else:
                self.keyfile_unlock_select_button.set_label(basename)
                self.keyfile_path = file_path

                self.keyfile_unlock_select_button.remove_css_class("destructive-action")
                self.keyfile_unlock_select_button.add_css_class("suggested-action")

                # After selecting a keyfile, activate the unlock button.
                self.keyfile_unlock_button.activate()

    def is_safe_open_elsewhere(self) -> bool:
        """Returns True if the safe is already open but not in the current window."""
        is_current = False
        filepath = self.database_filepath
        database = self.window.unlocked_db
        is_open = self.window.application.is_safe_open(filepath)

        if database:
            is_current = database.database_manager.database_path == filepath

        return is_open and not is_current

    @Gtk.Template.Callback()
    def _on_password_unlock_button_clicked(self, _widget):
        password_unlock_entry = self.password_unlock_entry

        entered_pwd = password_unlock_entry.get_text()
        if not entered_pwd:
            return

        if self.is_safe_open_elsewhere():
            self.window.send_notification(
                _("Safe {} is Already Open".format(self.database_filepath))
            )
            return

        if self.database_manager:
            if (
                entered_pwd == self.database_manager.password
                and self.database_manager.keyfile_hash is None
            ):
                self.database_manager.props.locked = False
            else:
                self._password_unlock_failed()
        else:
            self._unlock_method = UnlockMethod.PASSWORD
            self._password = entered_pwd
            self._open_database()

    # Keyfile Unlock

    @Gtk.Template.Callback()
    def _on_keyfile_unlock_select_button_clicked(self, _widget):
        """cb invoked when we unlock a database via keyfile"""
        keyfile_chooser_dialog = Gtk.FileChooserNative.new(
            _("Select Keyfile"), self.window, Gtk.FileChooserAction.OPEN, None, None
        )
        keyfile_chooser_dialog.add_filter(KeyFileFilter().file_filter)

        keyfile_chooser_dialog.connect(
            "response", self.on_dialog_response, keyfile_chooser_dialog
        )
        keyfile_chooser_dialog.show()

    def on_dialog_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType, _dialog: Gtk.Dialog
    ) -> None:
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            keyfile = dialog.get_file()
            self.keyfile_path = keyfile.get_path()
            keyfile.load_bytes_async(None, self.load_keyfile_callback)

            spinner = Gtk.Spinner()
            spinner.start()
            self.keyfile_unlock_select_button.props.child = spinner
            logging.debug("Keyfile selected: %s", keyfile.get_path())

        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection canceled")

    @Gtk.Template.Callback()
    def _on_keyfile_unlock_button_clicked(self, _widget):
        if self.is_safe_open_elsewhere():
            self.window.send_notification(
                _("Safe {} is Already Open".format(self.database_filepath))
            )
            return

        if self.database_manager:
            if (
                self.keyfile_path is not NotImplemented
                and self.database_manager.keyfile_hash
                == self.database_manager.create_keyfile_hash(self.keyfile_path)
            ):
                self.keyfile_path = NotImplemented
                self.database_manager.props.locked = False
            else:
                self._keyfile_unlock_failed()
        elif self.keyfile_path is not NotImplemented:
            self._unlock_method = UnlockMethod.KEYFILE
            self._open_database()

    # Composite Unlock

    @Gtk.Template.Callback()
    def _on_composite_unlock_select_button_clicked(self, _widget):
        opening_dialog = Gtk.FileChooserNative.new(
            _("Select Keyfile"), self.window, Gtk.FileChooserAction.OPEN, None, None
        )
        opening_dialog.add_filter(KeyFileFilter().file_filter)

        opening_dialog.connect(
            "response", self._on_composite_filechooser_response, opening_dialog
        )
        opening_dialog.show()

    def _on_composite_filechooser_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType, _dialog: Gtk.Dialog
    ) -> None:
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            keyfile = dialog.get_file()
            keyfile.load_bytes_async(None, self.load_keyfile_callback)

            spinner = Gtk.Spinner()
            spinner.start()
            self.composite_unlock_select_button.props.child = spinner

            logging.debug("KeyFile selected: %s", keyfile.get_path())

        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection cancelled")

    @Gtk.Template.Callback()
    def _on_composite_unlock_button_clicked(self, _widget):
        entered_pwd = self.composite_unlock_entry.get_text()
        if not entered_pwd:
            return

        if self.is_safe_open_elsewhere():
            self.window.send_notification(
                _("Safe {} is Already Open".format(self.database_filepath))
            )
            return

        if self.database_manager:
            if (
                (self.composite_keyfile_path is not NotImplemented)
                and (
                    self.database_manager.keyfile_hash
                    == self.database_manager.create_keyfile_hash(
                        self.composite_keyfile_path
                    )
                )
                and (entered_pwd == self.database_manager.password)
            ):
                self.database_manager.props.locked = False
            else:
                self._composite_unlock_failed()
        else:
            if entered_pwd and self.composite_keyfile_path is not NotImplemented:
                self._unlock_method = UnlockMethod.COMPOSITE
                self._password = entered_pwd
                self._open_database()
            else:
                self.composite_unlock_entry.add_css_class("error")

    def _set_last_used_composite_key(self):
        if (
            not passwordsafe.config_manager.get_remember_composite_key()
            or self.composite_keyfile_path is NotImplemented
        ):
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
            entry = self.password_unlock_entry
            button = self.password_unlock_button
        elif self._unlock_method == UnlockMethod.KEYFILE:
            entry = self.keyfile_unlock_select_button
            button = self.keyfile_unlock_button
        else:
            entry = self.composite_unlock_entry
            button = self.composite_unlock_button

        entry.set_sensitive(sensitive)
        button.set_sensitive(sensitive)
        back_button = self.headerbar.back_button
        back_button.set_sensitive(sensitive)
        self.stack_switcher.set_sensitive(sensitive)

        return button

    def _open_database(self):
        button = self._open_database_update_entries(False)

        spinner = Gtk.Spinner()
        spinner.start()

        button.set_child(spinner)

        unlock_thread = threading.Thread(target=self._open_database_process)
        unlock_thread.daemon = True
        unlock_thread.start()

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
                self.database_filepath, password, keyfile
            )
            self.database_manager.keyfile_hash = self.keyfile_hash
        except Exception as err:  # pylint: disable=broad-except
            logging.debug("Could not open safe: %s", err)
            GLib.idle_add(self._open_database_failure)
        else:
            GLib.idle_add(self._open_database_success)

    def _open_database_failure(self):
        button = self._open_database_update_entries(True)
        button.set_icon_name("changes-allow-symbolic")

        if self._unlock_method == UnlockMethod.PASSWORD:
            self._password_unlock_failed()
        elif self._unlock_method == UnlockMethod.KEYFILE:
            self._keyfile_unlock_failed()
        else:
            self._composite_unlock_failed()

    def _open_database_success(self):
        if Path(self.database_filepath).suffix == ".kdb":
            self._open_database_failure()
            # NOTE kdb is a an older format for Keepass databases.
            self.window.send_notification(_("The kdb Format is not Supported"))
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
                GLib.get_user_cache_dir(), const.SHORT_NAME, "backup"
            )
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            current_time = GLib.DateTime.new_now_local().format("%F_%T")
            basename = os.path.splitext(ntpath.basename(self.database_filepath))[0]
            backup_name = basename + "_backup_" + current_time + ".kdbx"
            backup = Gio.File.new_for_path(os.path.join(cache_dir, backup_name))

            def callback(gfile, result):
                try:
                    success = gfile.copy_finish(result)
                    if not success:
                        raise Exception("IO operation error")
                except Exception as err:  # pylint: disable=broad-except
                    logging.warning("Could not save database backup: %s", err)

            opened.copy_async(
                backup,
                Gio.FileCopyFlags.NONE,
                GLib.PRIORITY_DEFAULT,
                None,
                None,
                None,
                callback,
            )

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

        if self.window.unlocked_db is None:
            database = UnlockedDatabase(
                self.window, self.database_manager
            )
            self.window.unlocked_db = database
            self.window.unlocked_db_bin.props.child = database

        self.window.view = self.window.View.UNLOCKED_DATABASE

    #
    # Helper Functions
    #

    def _clear_input_fields(self):
        self.password_unlock_entry.set_text("")
        self.composite_unlock_entry.set_text("")

    def _composite_unlock_failed(self):
        self.window.send_notification(_("Failed to Unlock Safe"))
        self.composite_unlock_entry.grab_focus()
        self.composite_unlock_entry.add_css_class("error")
        self.composite_unlock_select_button.remove_css_class("suggested-action")
        self.composite_unlock_select_button.add_css_class("destructive-action")
        self._clear_input_fields()

        logging.debug("Could not open database, wrong password")

    def _keyfile_unlock_failed(self):
        self.window.send_notification(_("Failed to Unlock Safe"))
        self.keyfile_unlock_select_button.add_css_class("destructive-action")
        self.keyfile_unlock_select_button.set_label(_("Try again"))

        logging.debug("Invalid keyfile chosen")

    def _password_unlock_failed(self):
        self.window.send_notification(_("Failed to Unlock Safe"))

        self.password_unlock_entry.grab_focus()
        self.password_unlock_entry.add_css_class("error")
        self._clear_input_fields()

        logging.info("Could not open database, wrong password")
