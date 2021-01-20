# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import ntpath
import os
import threading
import time
from gettext import gettext as _

from gi.repository import Gdk, GLib, Gtk

import passwordsafe.config_manager as config
import passwordsafe.password_generator
from passwordsafe.utils import generate_keyfile


class DatabaseSettingsDialog:
    # pylint: disable=too-many-instance-attributes

    new_password: str | None = None
    new_keyfile_path = NotImplemented

    entries_number = NotImplemented
    groups_number = NotImplemented
    passwords_number = NotImplemented

    new_encryption_algorithm = NotImplemented
    new_derivation_algorithm = NotImplemented

    def __init__(self, unlocked_database):
        self.unlocked_database = unlocked_database
        self.database_manager = unlocked_database.database_manager
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/database_settings_dialog.ui")

        self.window = self.builder.get_object("database_settings_window")
        self.auth_apply_button = self.builder.get_object("auth_apply_button")

        self.stack = self.builder.get_object("dbsd_stack")
        self.encryption_apply_button = self.builder.get_object("encryption_apply_button")
        self.select_keyfile_button = self.builder.get_object("select_keyfile_button")
        self.generate_keyfile_button = self.builder.get_object("generate_keyfile_button")

        self.__setup_widgets()
        self.__setup_signals()

    #
    # Dialog Creation
    #

    def __setup_signals(self) -> None:
        self.auth_apply_button.connect("clicked", self.on_auth_apply_button_clicked)
        self.encryption_apply_button.connect(
            "clicked", self.on_encryption_apply_button_clicked
        )
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self.__on_key_press_event)
        self.window.add_controller(controller)

        # Password Section
        self.builder.get_object("current_password_entry").connect("changed", self.on_password_entry_changed)
        self.builder.get_object("new_password_entry").connect("changed", self.on_password_entry_changed)
        self.builder.get_object("new_password_generate_button").connect("clicked", self.on_generate_password)
        self.builder.get_object("confirm_password_entry").connect("changed", self.on_password_entry_changed)

        self.generate_keyfile_button.connect("clicked", self.on_keyfile_generator_button_clicked)
        self.select_keyfile_button.connect("clicked", self.on_keyfile_select_button_clicked)

        self.database_manager.connect(
            "notify::locked", self.__on_locked
        )

    def __setup_widgets(self) -> None:
        self.stack.set_visible_child(self.stack.get_child_by_name("auth_page"))
        self.auth_apply_button.set_sensitive(False)
        self.encryption_apply_button.set_sensitive(False)

        if self.database_manager.keyfile_hash is NotImplemented:
            self.generate_keyfile_button.set_sensitive(True)
            self.select_keyfile_button.set_sensitive(False)
        else:
            self.generate_keyfile_button.set_sensitive(False)

        # Password Level Bar
        level_bar = self.builder.get_object("password_level_bar")
        level_bar.add_offset_value("weak", 1.0)
        level_bar.add_offset_value("medium", 3.0)
        level_bar.add_offset_value("strong", 4.0)
        level_bar.add_offset_value("secure", 5.0)

        # Dialog
        self.window.set_modal(True)
        self.window.set_transient_for(self.unlocked_database.window)

        self.set_detail_values()

        stats_thread = threading.Thread(target=self.start_stats_thread)
        stats_thread.daemon = True
        stats_thread.start()

    def present(self):
        self.window.present()

    #
    # Password Section
    #

    def on_password_entry_changed(self, entry: Gtk.Entry) -> None:
        """CB if password entry (existing or new) has changed"""

        self.unlocked_database.start_database_lock_timer()

        current_password = self.builder.get_object("current_password_entry").get_text()
        new_password_entry = self.builder.get_object("new_password_entry")
        new_password = new_password_entry.get_text()
        conf_password_entry = self.builder.get_object("confirm_password_entry")
        conf_password = conf_password_entry.get_text()

        self.new_password = None

        # Update the quality level bar
        if entry.get_name() == "new_entry" and new_password:
            level = passwordsafe.password_generator.strength(new_password)
            self.builder.get_object("password_level_bar").set_value(level or 0)

        if new_password != conf_password:
            self.auth_apply_button.set_sensitive(False)
            new_password_entry.get_style_context().add_class("error")
            conf_password_entry.get_style_context().add_class("error")
            return
        new_password_entry.get_style_context().remove_class("error")
        conf_password_entry.get_style_context().remove_class("error")

        if (self.database_manager.password != current_password
           or (not new_password or not conf_password)):
            # 1) existing db password != current one entered
            # 2) Nothing entered for new and/or confirmed password
            self.auth_apply_button.set_sensitive(False)
            return

        self.auth_apply_button.set_sensitive(True)
        self.new_password = new_password

    def on_generate_password(self, _button: Gtk.Button) -> None:
        new_password_entry = self.builder.get_object("new_password_entry")
        confirm_password_entry = self.builder.get_object("confirm_password_entry")

        use_lowercase = config.get_generator_use_lowercase()
        use_uppercase = config.get_generator_use_uppercase()
        use_numbers = config.get_generator_use_numbers()
        use_symbols = config.get_generator_use_symbols()
        length = config.get_generator_length()

        generated_password = passwordsafe.password_generator.generate(length, use_uppercase, use_lowercase, use_numbers, use_symbols)

        new_password_entry.set_text(generated_password)
        confirm_password_entry.set_text(generated_password)

    #
    # Keyfile Section
    #

    def on_keyfile_select_button_clicked(self, button: Gtk.Button) -> None:
        self.unlocked_database.start_database_lock_timer()
        select_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for choosing current used keyfile
            _("Choose current keyfile"), self.window, Gtk.FileChooserAction.OPEN,
            _("_Open"), None)
        select_dialog.set_modal(True)

        ffilter = Gtk.FileFilter()
        ffilter.set_name(_("Keyfile"))
        ffilter.add_mime_type("application/octet-stream")
        ffilter.add_mime_type("application/x-keepass2")
        ffilter.add_mime_type("text/plain")
        ffilter.add_mime_type("application/x-iwork-keynote-sffkey")

        select_dialog.add_filter(ffilter)

        select_dialog.connect(
            "response", self._on_select_filechooser_response, button, select_dialog
        )
        select_dialog.show()

    def _on_select_filechooser_response(self,
                                        select_dialog: Gtk.Dialog,
                                        response: Gtk.ResponseType,
                                        button: Gtk.Button,
                                        _dialog: Gtk.Dialog) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            selected_keyfile = select_dialog.get_file().get_path()
            keyfile_hash: str = self.database_manager.create_keyfile_hash(
                selected_keyfile
            )

            if (
                keyfile_hash == self.database_manager.keyfile_hash
                or self.database_manager.keyfile_hash is NotImplemented
            ):
                self.generate_keyfile_button.set_sensitive(True)

                if keyfile_hash == self.database_manager.keyfile_hash:
                    self.new_keyfile_path = selected_keyfile

                button.set_sensitive(False)
                button.set_icon_name("object-select-symbolic")
            else:
                button.set_icon_name("edit-delete-symbolic")

    def on_keyfile_generator_button_clicked(self, _button: Gtk.Button) -> None:
        self.unlocked_database.start_database_lock_timer()
        save_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for generating a new keyfile
            _("Choose location for keyfile"), self.window, Gtk.FileChooserAction.SAVE,
            _("_Generate"), None)
        save_dialog.set_current_name(_("Keyfile"))
        save_dialog.set_modal(True)

        ffilter = Gtk.FileFilter()
        ffilter.set_name(_("Keyfile"))
        ffilter.add_mime_type("application/octet-stream")
        ffilter.add_mime_type("application/x-keepass2")
        ffilter.add_mime_type("text/plain")
        ffilter.add_mime_type("application/x-iwork-keynote-sffkey")

        save_dialog.add_filter(ffilter)
        save_dialog.connect("response", self._on_filechooser_response, save_dialog)
        save_dialog.show()

    def _on_filechooser_response(self,
                                 save_dialog: Gtk.Dialog,
                                 response: Gtk.ResponseType,
                                 _dialog: Gtk.Dialog) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            self.generate_keyfile_button.set_sensitive(False)

            spinner = Gtk.Spinner()
            spinner.start()
            self.generate_keyfile_button.set_child(spinner)

            keyfile = save_dialog.get_file()
            self.new_keyfile_path = keyfile.get_path()

            def callback():
                if self.new_password is not None:
                    self.database_manager.password = self.new_password

                self.database_manager.set_database_keyfile(self.new_keyfile_path)
                self.database_manager.save_database()

                self.keyfile_generated()

            GLib.idle_add(generate_keyfile, keyfile, callback)

    def keyfile_generated(self):
        self.generate_keyfile_button.set_icon_name("object-select-symbolic")
        self.generate_keyfile_button.set_sensitive(True)

        self.auth_apply_button.set_sensitive(True)

    #
    # Apply Buttons
    #

    def on_auth_apply_button_clicked(self, button):
        if self.new_password is not None:
            if self.new_keyfile_path is NotImplemented and self.database_manager.keyfile_hash is not NotImplemented:
                self.database_manager.set_database_keyfile(None)
                self.database_manager.keyfile_hash = NotImplemented

            self.database_manager.password = self.new_password

        if self.new_keyfile_path is not NotImplemented:
            if self.new_password is None:
                self.database_manager.password = None

            self.database_manager.set_database_keyfile(str(self.new_keyfile_path))
            self.database_manager.keyfile_hash = self.database_manager.create_keyfile_hash(str(self.new_keyfile_path))

        # Insensitive entries and buttons
        self.builder.get_object("stack_switcher").set_sensitive(False)
        self.builder.get_object("current_password_entry").set_sensitive(False)
        self.builder.get_object("new_password_entry").set_sensitive(False)
        self.builder.get_object("confirm_password_entry").set_sensitive(False)
        self.builder.get_object("select_keyfile_button").set_sensitive(False)
        self.generate_keyfile_button.set_sensitive(False)

        button.set_label(_("Apply…"))
        button.set_sensitive(False)

        save_thread = threading.Thread(target=self.auth_save_process)
        save_thread.daemon = True
        save_thread.start()

    def auth_save_process(self):
        self.database_manager.save_database()
        GLib.idle_add(self.auth_save_process_finished)

    def auth_save_process_finished(self):
        # Restore all widgets
        current_password_entry = self.builder.get_object("current_password_entry")
        new_password_entry = self.builder.get_object("new_password_entry")
        confirm_password_entry = self.builder.get_object("confirm_password_entry")
        select_keyfile_button = self.builder.get_object("select_keyfile_button")

        self.builder.get_object("stack_switcher").set_sensitive(True)
        current_password_entry.set_sensitive(True)
        new_password_entry.set_sensitive(True)
        confirm_password_entry.set_sensitive(True)

        current_password_entry.set_text("")
        new_password_entry.set_text("")
        confirm_password_entry.set_text("")

        if self.database_manager.keyfile_hash is NotImplemented:
            select_keyfile_button.set_sensitive(False)
            self.generate_keyfile_button.set_sensitive(True)
        else:
            select_keyfile_button.set_sensitive(True)

        select_keyfile_button.set_icon_name("document-open-symbolic")
        self.generate_keyfile_button.set_icon_name("security-high-symbolic")

        self.new_password = None
        self.new_keyfile_path = NotImplemented

        self.auth_apply_button.set_label(_("Apply Changes"))
        self.auth_apply_button.set_sensitive(False)

    def on_encryption_apply_button_clicked(self, _button):
        if self.new_encryption_algorithm is not NotImplemented:
            self.database_manager.db.encryption_algorithm = self.new_encryption_algorithm

        if self.new_derivation_algorithm is not NotImplemented:
            self.database_manager.db.version = self.new_derivation_algorithm

        self.encryption_apply_button.set_sensitive(False)
        self.encryption_apply_button.set_label(_("Apply…"))

        save_thread = threading.Thread(target=self.enc_save_thread)
        save_thread.daemon = True
        save_thread.start()

    def enc_save_thread(self):
        self.database_manager.save_database()
        GLib.idle_add(self.enc_save_process_finished)

    def enc_save_process_finished(self):
        self.encryption_apply_button.set_label(_("Apply Changes"))

    #
    # General Section
    #

    def set_detail_values(self):
        # Name
        self.builder.get_object("label_name").set_text(os.path.splitext(ntpath.basename(self.database_manager.database_path))[0])

        # Path
        label_path = self.builder.get_object("label_path")
        path = self.database_manager.database_path
        if "/home/" in path:
            label_path.set_text("~/" + os.path.relpath(path))
        else:
            label_path.set_text(path)

        # Size
        size = os.path.getsize(path) / 1000
        self.builder.get_object("label_size").set_text(str(size) + " kB")

        # Version
        version = self.database_manager.db.version
        self.builder.get_object("label_version").set_text(str(version[0]) + "." + str(version[1]))

        # Date
        date = time.ctime(os.path.getctime(path))
        self.builder.get_object("label_date").set_text(date)

        # Encryption Algorithm
        enc_alg = _("Unknown")
        if self.database_manager.db.encryption_algorithm == "aes256":
            # NOTE: AES is a proper name
            enc_alg = _("AES 256-bit")
        elif self.database_manager.db.encryption_algorithm == "chacha20":
            # NOTE: ChaCha20 is a proper name
            enc_alg = _("ChaCha20 256-bit")
        elif self.database_manager.db.encryption_algorithm == "twofish":
            # NOTE: Twofish is a proper name
            enc_alg = _("Twofish 256-bit")
        self.builder.get_object("label_enc_alg").set_text(enc_alg)

        # Derivation Algorithm
        der_alg = "Argon2"
        if version == (3, 1):
            der_alg = "AES-KDF"
        self.builder.get_object("label_der_alg").set_text(der_alg)

    def set_stats_values(self):
        # Number of Entries
        if self.builder.get_object("label_number_entries") is not None:
            self.builder.get_object("label_number_entries").set_text(str(self.entries_number))

        # Number of Groups
        if self.builder.get_object("label_number_groups") is not None:
            self.builder.get_object("label_number_groups").set_text(str(self.groups_number))

        # Number of Passwords
        if self.builder.get_object("label_number_passwords") is not None:
            self.builder.get_object("label_number_passwords").set_text(str(self.passwords_number))

    def start_stats_thread(self):
        self.entries_number = len(self.database_manager.db.entries)
        self.groups_number = len(self.database_manager.db.groups)
        self.passwords_number = 0
        for entry in self.database_manager.db.entries:
            if entry.password is not None and entry.password != "":
                self.passwords_number = self.passwords_number + 1
        GLib.idle_add(self.set_stats_values)

    #
    # Encryption Section
    #

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.window.close()

    def __on_key_press_event(self, _controller, keyval, _keycode, _state, _gdata=None):
        if keyval == Gdk.KEY_Escape:
            self.window.close()
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE
