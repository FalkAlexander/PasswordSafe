# SPDX-License-Identifier: GPL-3.0-only
import ntpath
import os
import threading
import time
from gettext import gettext as _

from gi.repository import GLib, Gtk

import passwordsafe.config_manager as config
import passwordsafe.keyfile_generator
import passwordsafe.password_generator


class DatabaseSettingsDialog:
    window = NotImplemented

    unlocked_database = NotImplemented
    database_manager = NotImplemented
    builder = NotImplemented
    stack = NotImplemented

    auth_apply_button = NotImplemented
    encryption_apply_button = NotImplemented
    generate_keyfile_button = NotImplemented

    new_password = NotImplemented
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

        self.assemble_window()
        # self.assemble_encryption_page()
        self.set_detail_values()

        stats_thread = threading.Thread(target=self.start_stats_thread)
        stats_thread.daemon = True
        stats_thread.start()

    #
    # Dialog Creation
    #

    def assemble_window(self) -> None:
        self.window = self.builder.get_object("database_settings_window")
        self.stack = self.builder.get_object("dbsd_stack")

        self.stack.set_visible_child(self.stack.get_child_by_name("auth_page"))

        # Apply Buttons
        self.auth_apply_button = self.builder.get_object("auth_apply_button")
        self.auth_apply_button.connect("clicked", self.on_auth_apply_button_clicked)
        self.auth_apply_button.set_sensitive(False)

        self.encryption_apply_button = self.builder.get_object("encryption_apply_button")
        self.encryption_apply_button.connect("clicked", self.on_encryption_apply_button_clicked)
        self.encryption_apply_button.set_sensitive(False)

        # Password Section
        self.builder.get_object("current_password_entry").connect("changed", self.on_password_entry_changed)
        self.builder.get_object("new_password_entry").connect("changed", self.on_password_entry_changed)
        self.builder.get_object("new_password_entry").connect("icon-press", self.on_generate_password)
        self.builder.get_object("confirm_password_entry").connect("changed", self.on_password_entry_changed)
        self.builder.get_object("confirm_password_entry").connect("icon-press", self.on_show_password)

        # Keyfile Section
        select_keyfile_button = self.builder.get_object("select_keyfile_button")
        select_keyfile_button.connect("clicked", self.on_keyfile_select_button_clicked)

        self.generate_keyfile_button = self.builder.get_object("generate_keyfile_button")
        self.generate_keyfile_button.connect("clicked", self.on_keyfile_generator_button_clicked)

        if self.database_manager.keyfile_hash is NotImplemented:
            self.generate_keyfile_button.set_sensitive(True)
            select_keyfile_button.set_sensitive(False)
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
        self.window.present()

        self.unlocked_database.database_settings_window = self.window
        self.window.connect("delete-event", self.on_dialog_quit)

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

        self.new_password = NotImplemented

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

    def on_generate_password(self, _widget, _position, _eventbutton):
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

        new_password_entry.set_visibility(True)
        confirm_password_entry.set_visibility(True)

    def on_show_password(self, _widget, _position, _eventbutton):
        new_password_entry = self.builder.get_object("new_password_entry")
        confirm_password_entry = self.builder.get_object("confirm_password_entry")

        if new_password_entry.get_visibility() is True:
            new_password_entry.set_visibility(False)
            confirm_password_entry.set_visibility(False)
        else:
            new_password_entry.set_visibility(True)
            confirm_password_entry.set_visibility(True)

    #
    # Keyfile Section
    #

    def on_keyfile_select_button_clicked(self, button: Gtk.Button) -> None:
        self.unlocked_database.start_database_lock_timer()
        select_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for choosing current used keyfile
            _("Choose current keyfile"), self.window, Gtk.FileChooserAction.OPEN,
            _("Open"), None)
        select_dialog.set_modal(True)
        select_dialog.set_local_only(False)

        ffilter = Gtk.FileFilter()
        ffilter.set_name(_("Keyfile"))
        ffilter.add_mime_type("application/octet-stream")
        ffilter.add_mime_type("application/x-keepass2")
        ffilter.add_mime_type("text/plain")
        ffilter.add_mime_type("application/x-iwork-keynote-sffkey")

        select_dialog.add_filter(ffilter)
        response = select_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            selected_keyfile = select_dialog.get_filename()
            self.keyfile_hash = self.database_manager.create_keyfile_hash(selected_keyfile)

            if self.keyfile_hash == self.database_manager.keyfile_hash or self.database_manager.keyfile_hash is NotImplemented:
                self.generate_keyfile_button.set_sensitive(True)

                if self.keyfile_hash == self.database_manager.keyfile_hash:
                    self.new_keyfile_path = selected_keyfile

                button.set_sensitive(False)
                button.remove(button.get_children()[0])
                button.add(Gtk.Image.new_from_icon_name("object-select-symbolic", Gtk.IconSize.BUTTON))
                button.show_all()
            else:
                button.remove(button.get_children()[0])
                button.add(Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON))
                button.show_all()

    def on_keyfile_generator_button_clicked(self, _button: Gtk.Button) -> None:
        self.unlocked_database.start_database_lock_timer()
        save_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for generating a new keyfile
            _("Choose location for keyfile"), self.window, Gtk.FileChooserAction.SAVE,
            _("Generate"), None)
        save_dialog.set_do_overwrite_confirmation(True)
        save_dialog.set_current_name(_("Keyfile"))
        save_dialog.set_modal(True)
        save_dialog.set_local_only(False)

        ffilter = Gtk.FileFilter()
        ffilter.set_name(_("Keyfile"))
        ffilter.add_mime_type("application/octet-stream")
        ffilter.add_mime_type("application/x-keepass2")
        ffilter.add_mime_type("text/plain")
        ffilter.add_mime_type("application/x-iwork-keynote-sffkey")

        save_dialog.add_filter(ffilter)
        response = save_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.generate_keyfile_button.set_sensitive(False)

            spinner = Gtk.Spinner()
            spinner.start()
            self.generate_keyfile_button.remove(self.generate_keyfile_button.get_children()[0])
            self.generate_keyfile_button.add(spinner)
            self.generate_keyfile_button.show_all()

            self.new_keyfile_path = save_dialog.get_filename()

            if self.new_password is NotImplemented:
                generator_thread = threading.Thread(target=passwordsafe.keyfile_generator.generate_keyfile, args=(self.new_keyfile_path, False, self, False))
            else:
                generator_thread = threading.Thread(target=passwordsafe.keyfile_generator.generate_keyfile, args=(self.new_keyfile_path, False, self, True))

            generator_thread.daemon = True
            generator_thread.start()

    def keyfile_generated(self):
        self.generate_keyfile_button.remove(self.generate_keyfile_button.get_children()[0])
        self.generate_keyfile_button.add(Gtk.Image.new_from_icon_name("object-select-symbolic", Gtk.IconSize.BUTTON))
        self.generate_keyfile_button.set_sensitive(True)
        self.generate_keyfile_button.show_all()

        self.auth_apply_button.set_sensitive(True)

    #
    # Apply Buttons
    #

    def on_auth_apply_button_clicked(self, button):
        if self.new_password is not NotImplemented:
            if self.new_keyfile_path is NotImplemented and self.database_manager.keyfile_hash is not NotImplemented:
                self.database_manager.set_database_keyfile(None)
                self.database_manager.keyfile_hash = NotImplemented

            self.database_manager.password = self.new_password

        if self.new_keyfile_path is not NotImplemented:
            if self.new_password is NotImplemented:
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

        select_keyfile_button.remove(select_keyfile_button.get_children()[0])
        select_keyfile_button.add(Gtk.Image.new_from_icon_name("document-open-symbolic", Gtk.IconSize.BUTTON))
        select_keyfile_button.show_all()

        self.generate_keyfile_button.remove(self.generate_keyfile_button.get_children()[0])
        self.generate_keyfile_button.add(Gtk.Image.new_from_icon_name("security-high-symbolic", Gtk.IconSize.BUTTON))
        self.generate_keyfile_button.show_all()

        self.new_password = NotImplemented
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

    def assemble_encryption_page(self):
        enc_alg_list = self.builder.get_object("enc_alg_list_box")

        if self.database_manager.db.encryption_algorithm == "chacha20":
            enc_alg_list.select_row(enc_alg_list.get_row_at_index(0))
        elif self.database_manager.db.encryption_algorithm == "twofish":
            enc_alg_list.select_row(enc_alg_list.get_row_at_index(1))
        elif self.database_manager.db.encryption_algorithm == "aes256":
            enc_alg_list.select_row(enc_alg_list.get_row_at_index(2))

        der_alg_list = self.builder.get_object("der_alg_list_box")

        if self.database_manager.db.version == (4, 0):
            der_alg_list.select_row(der_alg_list.get_row_at_index(0))
        elif self.database_manager.db.version == (3, 1):
            der_alg_list.select_row(der_alg_list.get_row_at_index(1))

        enc_alg_list.connect("row-activated", self.on_encryption_changed)
        der_alg_list.connect("row-activated", self.on_derivation_changed)

    def on_encryption_changed(self, _list_box, row):
        self.new_encryption_algorithm = NotImplemented

        if row.get_name() != "chacha20" and row.get_name() != "twofish" and row.get_name() != "aes256":
            return

        self.new_encryption_algorithm = row.get_name()

        if self.builder.get_object("der_alg_list_box").get_selected_row().get_name() == "argon2":
            version_tuple = (4, 0)
        elif self.builder.get_object("der_alg_list_box").get_selected_row().get_name() == "aeskdf":
            version_tuple = (3, 1)

        if self.database_manager.db.encryption_algorithm == row.get_name() and self.database_manager.db.version == version_tuple:
            self.encryption_apply_button.set_sensitive(False)
        else:
            self.encryption_apply_button.set_sensitive(True)

    def on_derivation_changed(self, _list_box, row):
        self.new_derivation_algorithm = NotImplemented

        if row.get_name() != "argon2" and row.get_name() != "aeskdf":
            return

        version_tuple = NotImplemented

        if row.get_name() == "argon2":
            version_tuple = (4, 0)
        elif row.get_name() == "aeskdf":
            version_tuple = (3, 1)

        if version_tuple == NotImplemented:
            return

        self.new_derivation_algorithm = version_tuple

        if self.database_manager.db.encryption_algorithm == self.builder.get_object("enc_alg_list_box").get_selected_row().get_name() and self.database_manager.db.version == version_tuple:
            self.encryption_apply_button.set_sensitive(False)
        else:
            self.encryption_apply_button.set_sensitive(True)

    #
    # Tools
    #

    def on_dialog_quit(self, _window, _event):
        self.unlocked_database.database_settings_window = NotImplemented
