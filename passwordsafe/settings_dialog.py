# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk

import passwordsafe.config_manager as config
from passwordsafe.config_manager import UnlockMethod


class SettingsDialog():
    window = NotImplemented
    builder = NotImplemented

    def __init__(self, window):
        self.window = window
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/settings_dialog.ui")

    def on_settings_menu_clicked(self, _action, _param):
        settings_dialog = self.builder.get_object("settings_dialog")

        settings_dialog.set_modal(True)
        settings_dialog.set_transient_for(self.window)
        settings_dialog.present()

        self.set_config_values()

    def set_config_values(self):
        # General
        settings_theme_switch = self.builder.get_object("settings_theme_switch")
        settings_theme_switch.connect("notify::active", self.on_settings_theme_switch_switched)
        settings_theme_switch_value = config.get_dark_theme()
        settings_theme_switch.set_active(settings_theme_switch_value)

        settings_fstart_switch = self.builder.get_object("settings_fstart_switch")
        settings_fstart_switch.connect("notify::active", self.on_settings_fstart_switch_switched)
        settings_fstart_switch_value = config.get_first_start_screen()
        settings_fstart_switch.set_active(settings_fstart_switch_value)

        # Safe
        settings_save_switch = self.builder.get_object("settings_save_switch")
        settings_save_switch.connect("notify::active", self.on_settings_save_switch_switched)
        settings_save_switch_value = config.get_save_automatically()
        settings_save_switch.set_active(settings_save_switch_value)

        # Password Generator
        generator_length_spin_button = self.builder.get_object("generator_length_spin_button")
        generator_length_spin_button.connect("value-changed", self.on_generator_length_spin_button_changed)
        generator_length_spin_button_value = config.get_generator_length()
        length_adjustment = Gtk.Adjustment(generator_length_spin_button_value, 1, 500, 1, 5)
        generator_length_spin_button.set_adjustment(length_adjustment)

        generator_use_uppercase_switch = self.builder.get_object("generator_use_uppercase_switch")
        generator_use_uppercase_switch.connect("notify::active", self.on_generator_use_uppercase_switch_switched)
        generator_use_uppercase_switch_value = config.get_generator_use_uppercase()
        generator_use_uppercase_switch.set_active(generator_use_uppercase_switch_value)

        generator_use_lowercase_switch = self.builder.get_object("generator_use_lowercase_switch")
        generator_use_lowercase_switch.connect("notify::active", self.on_generator_use_lowercase_switch_switched)
        generator_use_lowercase_switch_value = config.get_generator_use_lowercase()
        generator_use_lowercase_switch.set_active(generator_use_lowercase_switch_value)

        generator_use_numbers_switch = self.builder.get_object("generator_use_numbers_switch")
        generator_use_numbers_switch.connect("notify::active", self.on_generator_use_numbers_switch_switched)
        generator_use_numbers_switch_value = config.get_generator_use_numbers()
        generator_use_numbers_switch.set_active(generator_use_numbers_switch_value)

        generator_use_symbols_switch = self.builder.get_object("generator_use_symbols_switch")
        generator_use_symbols_switch.connect("notify::active", self.on_generator_use_symbols_switch_switched)
        generator_use_symbols_switch_value = config.get_generator_use_symbols()
        generator_use_symbols_switch.set_active(generator_use_symbols_switch_value)

        # Passphrase Generation
        generator_words_spin_button = self.builder.get_object("generator_words_spin_button")
        generator_words_spin_button.connect("value-changed", self.on_generator_words_spin_button_changed)
        generator_words_spin_button_value = config.get_generator_words()
        generator_words_adjustment = Gtk.Adjustment(generator_words_spin_button_value, 1, 100, 1, 5)
        generator_words_spin_button.set_adjustment(generator_words_adjustment)

        generator_separator_entry = self.builder.get_object("generator_separator_entry")
        generator_separator_entry.connect("activate", self.on_generator_separator_entry_changed)
        generator_separator_entry_value = config.get_generator_separator()
        generator_separator_entry.set_text(generator_separator_entry_value)

        # Security
        settings_lockdb_spin_button = self.builder.get_object("settings_lockdb_spin_button")
        settings_lockdb_spin_button.connect("value-changed", self.on_settings_lockdb_spin_button_changed)
        settings_lockdb_spin_button_value = config.get_database_lock_timeout()
        lockdb_adjustment = Gtk.Adjustment(settings_lockdb_spin_button_value, 0, 60, 1, 5)
        settings_lockdb_spin_button.set_adjustment(lockdb_adjustment)

        settings_clearcb_spin_button = self.builder.get_object("settings_clearcb_spin_button")
        settings_clearcb_spin_button.connect("value-changed", self.on_settings_clearcb_spin_button_changed)
        settings_clearcb_spin_button_value = config.get_clear_clipboard()
        clearcb_adjustment = Gtk.Adjustment(settings_clearcb_spin_button_value, 0, 300, 1, 5)
        settings_clearcb_spin_button.set_adjustment(clearcb_adjustment)

        settings_showpw_switch = self.builder.get_object("settings_showpw_switch")
        settings_showpw_switch.connect("notify::active", self.on_settings_showpw_switch_switched)
        settings_showpw_switch_value = config.get_show_password_fields()
        settings_showpw_switch.set_active(settings_showpw_switch_value)

        settings_clear_button = self.builder.get_object("settings_clear_button")
        settings_clear_button.connect("clicked", self.on_settings_clear_recents_clicked)

        if config.get_last_opened_list():
            settings_clear_button.set_sensitive(False)

        # Search
        settings_full_text_search_switch = self.builder.get_object("settings_full_text_search_switch")
        settings_full_text_search_switch.connect("notify::active", self.on_settings_full_text_search_switch_switched)
        settings_full_text_search_switch_value = config.get_full_text_search()
        settings_full_text_search_switch.set_active(settings_full_text_search_switch_value)

        settings_local_search_switch = self.builder.get_object("settings_local_search_switch")
        settings_local_search_switch.connect("notify::active", self.on_settings_local_search_switch_switched)
        settings_local_search_switch_value = config.get_local_search()
        settings_local_search_switch.set_active(settings_local_search_switch_value)

        # Unlock
        settings_remember_switch = self.builder.get_object("settings_remember_switch")
        settings_remember_switch.connect("notify::active", self.on_settings_remember_switch_switched)
        settings_remember_switch_value = config.get_remember_composite_key()
        settings_remember_switch.set_active(settings_remember_switch_value)

        settings_remember_method_switch = self.builder.get_object("settings_remember_method_switch")
        settings_remember_method_switch.connect("notify::active", self.on_settings_remember_method_switch_switched)
        settings_remember_method_switch_value = config.get_remember_unlock_method()
        settings_remember_method_switch.set_active(settings_remember_method_switch_value)

    def on_generator_use_uppercase_switch_switched(self, switch: Gtk.Switch, _: None) -> None:
        config.set_generator_use_uppercase(switch.get_active())

    def on_generator_use_lowercase_switch_switched(self, switch: Gtk.Switch, _: None) -> None:
        config.set_generator_use_lowercase(switch.get_active())

    def on_generator_use_symbols_switch_switched(self, switch: Gtk.Switch, _: None) -> None:
        config.set_generator_use_symbols(switch.get_active())

    def on_generator_use_numbers_switch_switched(self, switch: Gtk.Switch, _: None) -> None:
        config.set_generator_use_numbers(switch.get_active())

    def on_generator_words_spin_button_changed(self, spin_button: Gtk.SpinButton) -> None:
        config.set_generator_words(spin_button.get_value_as_int())

    def on_generator_length_spin_button_changed(self, spin_button: Gtk.SpinButton) -> None:
        config.set_generator_length(spin_button.get_value_as_int())

    def on_generator_separator_entry_changed(self, entry: Gtk.Entry) -> None:
        config.set_generator_separator(entry.get_text())

    def on_settings_full_text_search_switch_switched(self, switch_button, _gparam):
        config.set_full_text_search(switch_button.get_active())

    def on_settings_local_search_switch_switched(self, switch_button, _gparam):
        config.set_local_search(switch_button.get_active())

    def on_settings_theme_switch_switched(self, switch_button, _gparam):
        gtk_settings = Gtk.Settings.get_default()

        if switch_button.get_active():
            config.set_dark_theme(True)
            gtk_settings.set_property("gtk-application-prefer-dark-theme", True)
        else:
            config.set_dark_theme(False)
            gtk_settings.set_property("gtk-application-prefer-dark-theme", False)

    def on_settings_fstart_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            config.set_first_start_screen(True)
        else:
            config.set_first_start_screen(False)

    def on_settings_save_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            config.set_save_automatically(True)
        else:
            config.set_save_automatically(False)

    def on_settings_lockdb_spin_button_changed(self, spin_button):
        config.set_database_lock_timeout(spin_button.get_value())
        for db in self.window.opened_databases:  # pylint: disable=C0103
            db.start_database_lock_timer()

    def on_settings_clearcb_spin_button_changed(self, spin_button):
        config.set_clear_clipboard(spin_button.get_value())

    def on_settings_showpw_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            config.set_show_password_fields(True)
        else:
            config.set_show_password_fields(False)

    def on_settings_clear_recents_clicked(self, widget):
        config.set_last_opened_list([])
        if self.window.container is NotImplemented or not self.window.container.get_n_pages():
            self.window.display_welcome_page()

        widget.set_sensitive(False)

    def on_settings_remember_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            config.set_remember_composite_key(True)
        else:
            config.set_remember_composite_key(False)
            config.set_last_used_composite_key("")

    def on_settings_remember_method_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            config.set_remember_unlock_method(True)
        else:
            config.set_remember_unlock_method(False)
            config.set_unlock_method(
                UnlockMethod.PASSWORD)
