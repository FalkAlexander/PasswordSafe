# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import ntpath
import os
import threading
from gettext import gettext as _

from gi.repository import Adw, GLib, Gtk

from gsecrets.utils import KeyFileFilter
from gsecrets.utils import format_time, generate_keyfile


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/database_settings_dialog.ui")
class DatabaseSettingsDialog(Adw.PreferencesWindow):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "DatabaseSettingsDialog"

    new_password: str | None = None
    current_keyfile_hash = None
    current_keyfile_path = None
    new_keyfile_hash = None
    new_keyfile_path = None

    entries_number = None
    groups_number = None
    passwords_number = None

    auth_apply_button = Gtk.Template.Child()
    select_keyfile_button = Gtk.Template.Child()
    generate_keyfile_button = Gtk.Template.Child()

    level_bar = Gtk.Template.Child()

    keyfile_error_revealer = Gtk.Template.Child()

    encryption_algorithm_row = Gtk.Template.Child()
    date_row = Gtk.Template.Child()
    derivation_algorithm_row = Gtk.Template.Child()
    n_entries_row = Gtk.Template.Child()
    n_groups_row = Gtk.Template.Child()
    n_passwords_row = Gtk.Template.Child()
    name_row = Gtk.Template.Child()
    path_row = Gtk.Template.Child()
    size_row = Gtk.Template.Child()
    version_row = Gtk.Template.Child()

    confirm_password_entry = Gtk.Template.Child()
    current_password_entry = Gtk.Template.Child()
    new_password_entry = Gtk.Template.Child()

    save_id: int | None = None

    def __init__(self, unlocked_database):
        super().__init__()

        self.unlocked_database = unlocked_database
        self.database_manager = unlocked_database.database_manager

        self.__setup_widgets()
        self.__setup_signals()

    #
    # Dialog Creation
    #

    def __setup_signals(self) -> None:
        self.database_manager.connect("notify::locked", self.__on_locked)

    def __setup_widgets(self) -> None:
        # Dialog
        self.set_modal(True)
        self.set_transient_for(self.unlocked_database.window)

        self.set_detail_values()

        stats_thread = threading.Thread(target=self.start_stats_thread)
        stats_thread.daemon = True
        stats_thread.start()

    @Gtk.Template.Callback()
    def on_password_entry_changed(self, _entry: Gtk.Entry) -> None:
        """CB if password entry (existing or new) has changed"""

        self.unlocked_database.start_database_lock_timer()

        new_password = self.new_password_entry.get_text()
        conf_password = self.confirm_password_entry.get_text()

        if new_password != conf_password:
            self.new_password_entry.add_css_class("error")
            self.confirm_password_entry.add_css_class("error")
        else:
            self.new_password_entry.remove_css_class("error")
            self.confirm_password_entry.remove_css_class("error")

        correct_input = self.passwords_coincide() and self.correct_credentials()
        self.auth_apply_button.set_sensitive(correct_input)

    def correct_credentials(self) -> bool:
        database_hash = self.database_manager.keyfile_hash
        database_password = self.database_manager.password
        current_hash = self.current_keyfile_hash
        current_password = self.current_password_entry.get_text()

        return database_hash == current_hash and database_password == current_password

    def passwords_coincide(self) -> bool:
        new_password = self.new_password_entry.get_text()
        repeat_password = self.confirm_password_entry.get_text()

        return repeat_password == new_password and new_password

    @Gtk.Template.Callback()
    def on_keyfile_select_button_clicked(self, button: Gtk.Button) -> None:
        self.unlocked_database.start_database_lock_timer()

        # We reset the button if we previously failed.
        if button.props.icon_name == "edit-delete-symbolic":
            button.props.icon_name = "document-open-symbolic"
            button.remove_css_class("destructive-action")
            self.current_keyfile_path = None
            self.current_keyfile_hash = None
            return

        select_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for choosing current used keyfile
            _("Select Current Keyfile"),
            self,
            Gtk.FileChooserAction.OPEN,
            None,
            None,
        )
        select_dialog.set_modal(True)

        ffilter = KeyFileFilter().file_filter
        select_dialog.add_filter(ffilter)

        select_dialog.connect(
            "response", self._on_select_filechooser_response, select_dialog
        )
        select_dialog.show()

    def _on_select_filechooser_response(
        self,
        select_dialog: Gtk.Dialog,
        response: Gtk.ResponseType,
        _dialog: Gtk.Dialog,
    ) -> None:
        select_dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            keyfile = select_dialog.get_file()
            keyfile.load_bytes_async(None, self.load_bytes_callback)

    def load_bytes_callback(self, gfile, result):
        try:
            gbytes, _ = gfile.load_bytes_finish(result)
            if not gbytes:
                raise Exception("IO operation error")

        except Exception as err:  # pylint: disable=broad-except
            logging.debug("Could not set keyfile hash: %s", err)
            self.keyfile_error_revealer.reveal(True)
            self.select_keyfile_button.set_icon_name("document-open-symbolic")
        else:
            keyfile_hash = GLib.compute_checksum_for_bytes(
                GLib.ChecksumType.SHA1, gbytes
            )
            self.current_keyfile_path = gfile.get_path()
            self.current_keyfile_hash = keyfile_hash

            button = self.select_keyfile_button

            if keyfile_hash == self.database_manager.keyfile_hash:
                button.set_icon_name("object-select-symbolic")
                correct_input = self.passwords_coincide() and self.correct_credentials()

                self.auth_apply_button.set_sensitive(correct_input)
            else:
                button.set_icon_name("edit-delete-symbolic")
                button.add_css_class("destructive-action")
                self.auth_apply_button.set_sensitive(False)

    @Gtk.Template.Callback()
    def on_keyfile_generator_button_clicked(self, button: Gtk.Button) -> None:
        self.unlocked_database.start_database_lock_timer()

        # We reset the button if we previously failed.
        if button.props.icon_name == "object-select-symbolic":
            button.props.icon_name = "security-high-symbolic"
            self.new_keyfile_path = None
            self.new_keyfile_hash = None
            return

        save_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for generating a new keyfile
            _("Generate Keyfile"),
            self,
            Gtk.FileChooserAction.SAVE,
            _("_Generate"),
            None,
        )
        save_dialog.set_current_name(_("Keyfile"))
        save_dialog.set_modal(True)

        ffilter = KeyFileFilter().file_filter
        save_dialog.add_filter(ffilter)

        save_dialog.connect("response", self._on_filechooser_response, save_dialog)
        save_dialog.show()

    def _on_filechooser_response(
        self, save_dialog: Gtk.Dialog, response: Gtk.ResponseType, _dialog: Gtk.Dialog
    ) -> None:
        save_dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            spinner = Gtk.Spinner()
            spinner.start()
            self.generate_keyfile_button.set_child(spinner)

            keyfile = save_dialog.get_file()

            def callback(gfile, result, keyfile_hash):
                try:
                    success, _ = gfile.replace_contents_finish(result)
                    if not success:
                        raise Exception("IO operation error")

                except Exception as err:  # pylint: disable=broad-except
                    self.generate_keyfile_button.set_icon_name("security-high-symbolic")
                    logging.debug("Could not create keyfile: %s", err)
                    self.keyfile_error_revealer.reveal(True)
                else:
                    self.generate_keyfile_button.set_icon_name("object-select-symbolic")
                    self.new_keyfile_hash = keyfile_hash
                    self.new_keyfile_path = keyfile.get_path()

            generate_keyfile(keyfile, callback)

    def _on_save_notification(self, dbm, _saved):
        # TODO Handle errors, possibly with a AdwToast.
        if self.save_id:
            dbm.disconnect(self.save_id)
            self.save_id = None

        self.auth_save_process_finished()

    @Gtk.Template.Callback()
    def on_auth_apply_button_clicked(self, button):
        new_password = self.new_password_entry.get_text()

        self.database_manager.password = new_password
        self.database_manager.keyfile = self.new_keyfile_path
        self.database_manager.keyfile_hash = self.new_keyfile_hash

        # Insensitive entries and buttons
        self.set_sensitive(False)

        spinner = Gtk.Spinner()
        spinner.start()
        button.set_child(spinner)
        button.set_sensitive(False)

        self.save_id = self.database_manager.connect(
            "save-notification", self._on_save_notification
        )
        self.database_manager.save_database(True)

    @Gtk.Template.Callback()
    def on_password_generated(self, _popover, password):
        self.confirm_password_entry.props.text = password
        self.new_password_entry.props.text = password

    def auth_save_process_finished(self):
        # Restore all widgets

        self.set_sensitive(True)
        self.current_password_entry.set_text("")
        self.new_password_entry.set_text("")
        self.confirm_password_entry.set_text("")

        self.select_keyfile_button.set_icon_name("document-open-symbolic")
        self.generate_keyfile_button.set_icon_name("security-high-symbolic")

        self.current_keyfile_hash = None
        self.current_keyfile_path = None
        self.new_keyfile_hash = None
        self.new_keyfile_path = None

        self.auth_apply_button.set_label(_("_Apply Changes"))
        self.auth_apply_button.set_sensitive(False)

    def set_detail_values(self):
        # Name
        self.name_row.props.subtitle = os.path.splitext(
            ntpath.basename(self.database_manager.database_path)
        )[0]

        # Path
        path = self.database_manager.database_path
        if "/home/" in path:
            self.path_row.props.subtitle = "~/" + os.path.relpath(path)
        else:
            self.path_row.props.subtitle = path

        # Size
        size = os.path.getsize(path) / 1000
        self.size_row.props.subtitle = str(size) + " kB"

        # Version
        version = self.database_manager.db.version
        self.version_row.props.subtitle = str(version[0]) + "." + str(version[1])

        # Date
        # TODO g_file_info_get_creation_date_time introduced in GLib 2.70.
        epoch_time = os.path.getctime(path)  # Time since UNIX epoch.
        gdate = GLib.DateTime.new_from_unix_utc(epoch_time)
        self.date_row.props.subtitle = format_time(gdate)

        # Encryption Algorithm
        enc_alg = _("Unknown")
        enc_alg_priv = self.database_manager.db.encryption_algorithm
        if enc_alg_priv == "aes256":
            # NOTE: AES is a proper name
            enc_alg = _("AES 256-bit")
        elif enc_alg_priv == "chacha20":
            # NOTE: ChaCha20 is a proper name
            enc_alg = _("ChaCha20 256-bit")
        elif enc_alg_priv == "twofish":
            # NOTE: Twofish is a proper name
            enc_alg = _("Twofish 256-bit")
        self.encryption_algorithm_row.props.subtitle = enc_alg

        # Derivation Algorithm
        der_alg = _("Unknown")
        der_alg_priv = self.database_manager.db.kdf_algorithm
        if der_alg_priv == "argon2":
            # NOTE: Argon2 is a proper name
            der_alg = _("Argon2")
        elif der_alg_priv == "aeskdf":
            # NOTE: AES-KDF is a proper name
            der_alg = _("AES-KDF")

        self.derivation_algorithm_row.props.subtitle = der_alg

    def set_stats_values(self):
        self.n_entries_row.props.subtitle = str(self.entries_number)
        self.n_groups_row.props.subtitle = str(self.groups_number)
        self.n_passwords_row.props.subtitle = str(self.passwords_number)

    def start_stats_thread(self):
        self.entries_number = len(self.database_manager.db.entries)
        self.groups_number = len(self.database_manager.db.groups)
        self.passwords_number = 0
        for entry in self.database_manager.db.entries:
            if entry.password is not None and entry.password != "":
                self.passwords_number = self.passwords_number + 1
        GLib.idle_add(self.set_stats_values)

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.close()
