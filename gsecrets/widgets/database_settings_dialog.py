# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import threading
import typing
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from gsecrets.utils import (
    compare_passwords,
    format_time,
)

if typing.TYPE_CHECKING:
    from gsecrets.provider.base_provider import BaseProvider


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/database_settings_dialog.ui")
class DatabaseSettingsDialog(Adw.PreferencesDialog):
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

    level_bar = Gtk.Template.Child()

    encryption_algorithm_row = Gtk.Template.Child()
    date_row = Gtk.Template.Child()
    derivation_algorithm_row = Gtk.Template.Child()
    n_entries_row = Gtk.Template.Child()
    n_groups_row = Gtk.Template.Child()
    n_passwords_row = Gtk.Template.Child()
    name_row = Gtk.Template.Child()
    description_row = Gtk.Template.Child()
    default_username_row = Gtk.Template.Child()
    path_row = Gtk.Template.Child()
    size_row = Gtk.Template.Child()
    version_row = Gtk.Template.Child()
    current_password_entry = Gtk.Template.Child()
    provider_group = Gtk.Template.Child()
    banner = Gtk.Template.Child()

    confirm_password_entry = Gtk.Template.Child()
    new_password_entry = Gtk.Template.Child()

    def __init__(self, unlocked_database):
        super().__init__()

        self.unlocked_database = unlocked_database
        self.database_manager = unlocked_database.database_manager
        self.window = self.unlocked_database.window
        self.signals = []
        self.bindings = []

        self.__setup_widgets()
        self.__setup_signals()

        self._providers = self.window.key_providers

        for key_provider in self._providers.get_key_providers():
            if key_provider.available:
                self.provider_group.add(key_provider.create_database_row())

                show_id = key_provider.connect(
                    key_provider.show_message,
                    self._on_show_message,
                )
                hide_id = key_provider.connect(
                    key_provider.hide_message,
                    self._on_hide_message,
                )

                self.signals.append((show_id, key_provider))
                self.signals.append((hide_id, key_provider))

    def do_closed(self):
        for signal_id, obj in self.signals:
            obj.disconnect(signal_id)

        self.signals = []

        for binding in self.bindings:
            binding.unbind()

        self.bindings = []

    def _on_show_message(self, _provider: BaseProvider, label: str) -> None:
        self.banner.set_title(label)
        self.banner.set_revealed(True)

    def _on_hide_message(self, _provider: BaseProvider) -> None:
        self.banner.set_revealed(False)

    #
    # Dialog Creation
    #

    def __setup_signals(self) -> None:
        signal_id = self.database_manager.connect("notify::locked", self.__on_locked)
        name_binding = self.database_manager.bind_property(
            "name",
            self.name_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        description_binding = self.database_manager.bind_property(
            "description",
            self.description_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        self.signals.append((signal_id, self.database_manager))

        self.bindings.append(name_binding)
        self.bindings.append(description_binding)

    def __setup_widgets(self) -> None:
        # Dialog
        self.set_detail_values()

        stats_thread = threading.Thread(target=self.start_stats_thread)
        stats_thread.daemon = True
        stats_thread.start()

    @Gtk.Template.Callback()
    def on_password_entry_changed(self, _entry: Gtk.Entry) -> None:
        """CB if password entry (existing or new) has changed."""
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
        database_password = self.database_manager.password
        current_password = self.current_password_entry.get_text()
        return compare_passwords(database_password, current_password)

    def passwords_coincide(self) -> bool:
        new_password = self.new_password_entry.get_text()
        repeat_password = self.confirm_password_entry.get_text()

        return compare_passwords(new_password, repeat_password)

    def _on_set_credentials(self, database_manager, result):
        try:
            is_saved = database_manager.set_credentials_finish(result)
        except GLib.Error:
            logging.exception("Could not set credentials")
            self.add_toast(Adw.Toast.new(_("Could not apply changes")))
        else:
            if not is_saved:  # Should be unreachable
                logging.error("Credentials set without changes")
                self.add_toast(Adw.Toast.new(_("Could not apply changes")))
                return  # Still executes the finally block

            self.add_toast(Adw.Toast.new(_("Changes Applied")))

            # Restore all widgets
            self.current_password_entry.set_text("")
            self.new_password_entry.set_text("")
            self.confirm_password_entry.set_text("")

            self.current_keyfile_hash = None
            self.current_keyfile_path = None
            self.new_keyfile_hash = None
            self.new_keyfile_path = None
        finally:
            self.set_sensitive(True)
            self.auth_apply_button.set_sensitive(False)
            self.auth_apply_button.set_label(_("_Apply Changes"))
            for provider in self.provider_group:
                provider.set_sensitive(True)

    def _on_generate_composite_key(self, providers, result):
        for provider in self.provider_group:
            provider.set_sensitive(False)

        try:
            self._new_composition_key = providers.generate_composite_key_finish(result)
        except GLib.Error:
            logging.exception("Failed to generate composite key")
            self.window.send_notification(_("Failed to generate composite key"))
            return

        self.database_manager.check_file_changes_async(self.on_check_file_changes)

    @Gtk.Template.Callback()
    def on_default_username_changed(self, entry: Adw.EntryRow) -> None:
        self.database_manager.default_username = entry.get_text()

    @Gtk.Template.Callback()
    def on_auth_apply_button_clicked(self, button):
        # Insensitive entries and buttons
        self.set_sensitive(False)

        spinner = Adw.Spinner()
        button.set_child(spinner)
        button.set_sensitive(False)

        self.window.key_providers.generate_composite_key_async(
            self.database_manager.get_salt_as_lazy(),
            self._on_generate_composite_key,
        )

    def on_check_file_changes(self, dbm, result):
        try:
            conflicts = dbm.check_file_changes_finish(result)
        except GLib.Error:
            logging.exception("Could not monitor file changes")
            toast = _("Could not change credentials")
            self.add_toast(toast)
        else:
            if conflicts:
                dialog = Adw.AlertDialog.new(
                    _("Conflicts While Saving"),
                    _(
                        "The safe was modified from somewhere else. Please resolve these conflicts from the main window when saving.",  # noqa: E501
                    ),
                )
                dialog.add_response("ok", _("OK"))
                dialog.present(self)
            else:
                new_password = self.new_password_entry.props.text
                self.database_manager.set_credentials_async(
                    new_password,
                    self._new_composition_key,
                    self._on_set_credentials,
                )
        finally:
            self.set_sensitive(True)
            self.auth_apply_button.set_sensitive(False)
            self.auth_apply_button.set_label(_("_Apply Changes"))
            self._new_composition_key = None

    @Gtk.Template.Callback()
    def on_password_generated(self, _popover, password):
        self.confirm_password_entry.props.text = password
        self.new_password_entry.props.text = password

    def set_detail_values(self):
        # Name
        self.default_username_row.props.text = self.database_manager.default_username

        # Path
        path = self.database_manager.path
        gfile = Gio.File.new_for_path(path)
        if "/home/" in path:
            self.path_row.props.subtitle = "~/" + os.path.relpath(path)
        else:
            self.path_row.props.subtitle = path

        # Size
        def query_info_cb(gfile, result):
            try:
                file_info = gfile.query_info_finish(result)
            except GLib.Error:
                logging.exception("Could not query file info")
            else:
                size = file_info.get_size()  # In bytes.
                self.size_row.props.subtitle = GLib.format_size(size)

        attributes = Gio.FILE_ATTRIBUTE_STANDARD_SIZE
        gfile.query_info_async(
            attributes,
            Gio.FileQueryInfoFlags.NONE,
            GLib.PRIORITY_DEFAULT,
            None,
            query_info_cb,
        )

        # Version
        version = self.database_manager.db.version
        self.version_row.props.subtitle = str(version[0]) + "." + str(version[1])

        # Date
        # TODO g_file_info_get_creation_date_time introduced in GLib 2.70.
        epoch_time = Path(path).stat().st_ctime  # Time since UNIX epoch.
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
        if der_alg_priv == "argon2id":
            # NOTE: Argon2id is a proper name
            der_alg = _("Argon2id")
        elif der_alg_priv == "aeskdf":
            # NOTE: AES-KDF is a proper name
            der_alg = _("AES-KDF")

        self.derivation_algorithm_row.props.subtitle = der_alg

    def set_stats_values(self):
        self.n_entries_row.props.subtitle = str(self.entries_number)
        self.n_groups_row.props.subtitle = str(self.groups_number)
        self.n_passwords_row.props.subtitle = str(self.passwords_number)

        return GLib.SOURCE_REMOVE

    def start_stats_thread(self):
        self.entries_number = len(self.database_manager.entries)
        self.groups_number = len(self.database_manager.groups)
        self.passwords_number = 0
        for entry in self.database_manager.entries:
            if entry.password is not None and entry.password != "":
                self.passwords_number = self.passwords_number + 1
        GLib.idle_add(self.set_stats_values)

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.close()
