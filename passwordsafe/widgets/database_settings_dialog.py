# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import ntpath
import os
import threading
from datetime import datetime
from gettext import gettext as _

from gi.repository import Adw, GLib, Gtk

from passwordsafe.password_generator_popover import PasswordGeneratorPopover  # noqa: F401, pylint: disable=unused-import
from passwordsafe.utils import KeyFileFilter
from passwordsafe.utils import format_time, generate_keyfile
from passwordsafe.widgets.password_level_bar import PasswordLevelBar  # noqa: F401, pylint: disable=unused-import
from passwordsafe.widgets.preferences_row import PreferencesRow  # noqa: F401, pylint: disable=unused-import


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/database_settings_dialog.ui")
class DatabaseSettingsDialog(Adw.PreferencesWindow):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "DatabaseSettingsDialog"

    new_password: str | None = None
    current_keyfile_path = None
    new_keyfile_path = None

    entries_number = None
    groups_number = None
    passwords_number = None

    auth_apply_button = Gtk.Template.Child()
    select_keyfile_button = Gtk.Template.Child()
    generate_keyfile_button = Gtk.Template.Child()

    level_bar = Gtk.Template.Child()

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
        old_hash = self.database_manager.keyfile_hash
        new_hash = None
        database_password = self.database_manager.password
        current_password = self.current_password_entry.get_text()

        if self.current_keyfile_path:
            new_hash = self.database_manager.create_keyfile_hash(
                self.current_keyfile_path
            )

        return old_hash == new_hash and database_password == current_password

    def passwords_coincide(self) -> bool:
        new_password = self.new_password_entry.get_text()
        repeat_password = self.confirm_password_entry.get_text()

        return repeat_password == new_password and new_password

    @Gtk.Template.Callback()
    def on_keyfile_select_button_clicked(self, button: Gtk.Button) -> None:
        self.unlocked_database.start_database_lock_timer()
        select_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for choosing current used keyfile
            _("Choose current keyfile"),
            self,
            Gtk.FileChooserAction.OPEN,
            _("_Open"),
            None,
        )
        select_dialog.set_modal(True)

        ffilter = KeyFileFilter().file_filter
        select_dialog.add_filter(ffilter)

        select_dialog.connect(
            "response", self._on_select_filechooser_response, button, select_dialog
        )
        select_dialog.show()

    def _on_select_filechooser_response(
        self,
        select_dialog: Gtk.Dialog,
        response: Gtk.ResponseType,
        button: Gtk.Button,
        _dialog: Gtk.Dialog,
    ) -> None:
        select_dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            selected_keyfile = select_dialog.get_file().get_path()
            keyfile_hash: str = self.database_manager.create_keyfile_hash(
                selected_keyfile
            )
            self.current_keyfile_path = selected_keyfile

            if (
                keyfile_hash == self.database_manager.keyfile_hash
                or self.database_manager.keyfile_hash is None
            ):
                button.set_icon_name("object-select-symbolic")
                correct_input = self.passwords_coincide() and self.correct_credentials()

                self.auth_apply_button.set_sensitive(correct_input)
            else:
                button.set_icon_name("edit-delete-symbolic")
                self.auth_apply_button.set_sensitive(False)

    @Gtk.Template.Callback()
    def on_keyfile_generator_button_clicked(self, _button: Gtk.Button) -> None:
        self.unlocked_database.start_database_lock_timer()
        save_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for generating a new keyfile
            _("Choose location for keyfile"),
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
            self.new_keyfile_path = keyfile.get_path()

            def callback():
                self.generate_keyfile_button.set_icon_name("object-select-symbolic")

            GLib.idle_add(generate_keyfile, keyfile, callback)

    @Gtk.Template.Callback()
    def on_auth_apply_button_clicked(self, button):
        new_password = self.new_password_entry.get_text()

        self.database_manager.password = new_password
        self.database_manager.keyfile = self.new_keyfile_path

        # Insensitive entries and buttons
        self.set_sensitive(False)

        spinner = Gtk.Spinner()
        spinner.start()
        button.set_child(spinner)
        button.set_sensitive(False)

        save_thread = threading.Thread(target=self.auth_save_process)
        save_thread.daemon = True
        save_thread.start()

    @Gtk.Template.Callback()
    def on_password_generated(self, _popover, password):
        self.confirm_password_entry.props.text = password
        self.new_password_entry.props.text = password

    def auth_save_process(self):
        self.database_manager.save_database()
        GLib.idle_add(self.auth_save_process_finished)

    def auth_save_process_finished(self):
        # Restore all widgets

        self.set_sensitive(True)
        self.current_password_entry.set_text("")
        self.new_password_entry.set_text("")
        self.confirm_password_entry.set_text("")

        self.select_keyfile_button.set_icon_name("document-open-symbolic")
        self.generate_keyfile_button.set_icon_name("security-high-symbolic")

        self.current_keyfile_path = None

        self.auth_apply_button.set_label(_("Apply Changes"))
        self.auth_apply_button.set_sensitive(False)

    def set_detail_values(self):
        # Name
        self.name_row.props.subtitle = (
            os.path.splitext(ntpath.basename(self.database_manager.database_path))[0]
        )

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
        date = datetime.utcfromtimestamp(epoch_time)
        self.date_row.props.subtitle = format_time(date)

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
