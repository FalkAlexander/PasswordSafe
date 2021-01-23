# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk, Handy

import passwordsafe.config_manager as config
from passwordsafe.config_manager import UnlockMethod


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/settings_dialog.ui")
class SettingsDialog(Handy.PreferencesWindow):

    __gtype_name__ = "SettingsDialog"

    _clear_button = Gtk.Template.Child()
    _clearcb_spin_button = Gtk.Template.Child()
    _fstart_switch = Gtk.Template.Child()
    _generator_length_spin_button = Gtk.Template.Child()
    _generator_separator_entry = Gtk.Template.Child()
    _generator_use_lowercase_switch = Gtk.Template.Child()
    _generator_use_numbers_switch = Gtk.Template.Child()
    _generator_use_symbols_switch = Gtk.Template.Child()
    _generator_use_uppercase_switch = Gtk.Template.Child()
    _generator_words_spin_button = Gtk.Template.Child()
    _lockdb_spin_button = Gtk.Template.Child()
    _remember_method_switch = Gtk.Template.Child()
    _remember_switch = Gtk.Template.Child()
    _save_switch = Gtk.Template.Child()
    _showpw_switch = Gtk.Template.Child()
    _theme_switch = Gtk.Template.Child()

    def __init__(self, window):
        super().__init__()

        self.window = window
        self.props.transient_for = self.window

    def on_settings_menu_clicked(self, _action, _param):
        self._set_config_values()
        self.present()

    def _set_config_values(self):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        # General
        self._theme_switch.props.active = config.get_dark_theme()
        self._theme_switch.connect(
            "notify::active", self._on_settings_theme_switch_switched
        )

        self._fstart_switch.props.active = config.get_first_start_screen()
        self._fstart_switch.connect(
            "notify::active", self._on_settings_fstart_switch_switched
        )

        # Safe
        self._save_switch.props.active = config.get_save_automatically()
        self._save_switch.connect(
            "notify::active", self._on_settings_save_switch_switched
        )

        # Password Generator
        generator_length = config.get_generator_length()
        length_adjustment = Gtk.Adjustment(generator_length, 1, 500, 1, 5)
        self._generator_length_spin_button.props.adjustment = length_adjustment
        self._generator_length_spin_button.connect(
            "value-changed", self._on_generator_length_spin_button_changed
        )

        use_uppercase = config.get_generator_use_uppercase()
        self._generator_use_uppercase_switch.props.active = use_uppercase
        self._generator_use_uppercase_switch.connect(
            "notify::active", self._on_generator_use_uppercase_switch_switched
        )

        use_lowercase = config.get_generator_use_lowercase()
        self._generator_use_lowercase_switch.props.active = use_lowercase
        self._generator_use_lowercase_switch.connect(
            "notify::active", self._on_generator_use_lowercase_switch_switched
        )

        use_numbers = config.get_generator_use_numbers()
        self._generator_use_numbers_switch.props.active = use_numbers
        self._generator_use_numbers_switch.connect(
            "notify::active", self._on_generator_use_numbers_switch_switched
        )

        use_symbols_value = config.get_generator_use_symbols()
        self._generator_use_symbols_switch.props.active = use_symbols_value
        self._generator_use_symbols_switch.connect(
            "notify::active", self._on_generator_use_symbols_switch_switched
        )

        # Passphrase Generation
        generator_words_value = config.get_generator_words()
        words_adjustment = Gtk.Adjustment(generator_words_value, 1, 100, 1, 5)
        self._generator_words_spin_button.props.adjustment = words_adjustment
        self._generator_words_spin_button.connect(
            "value-changed", self._on_generator_words_spin_button_changed
        )

        separator_entry_value = config.get_generator_separator()
        self._generator_separator_entry.props.text = separator_entry_value
        self._generator_separator_entry.connect(
            "activate", self._on_generator_separator_entry_changed
        )

        # Security
        lockdb_value = config.get_database_lock_timeout()
        lockdb_adjustment = Gtk.Adjustment(lockdb_value, 1, 60, 1, 5)
        self._lockdb_spin_button.props.adjustment = lockdb_adjustment
        self._lockdb_spin_button.connect(
            "value-changed", self._on_settings_lockdb_spin_button_changed
        )

        clear_cb_value = config.get_clear_clipboard()
        clear_adjustment = Gtk.Adjustment(clear_cb_value, 1, 300, 1, 5)
        self._clearcb_spin_button.props.adjustment = clear_adjustment
        self._clearcb_spin_button.connect(
            "value-changed", self._on_settings_clearcb_spin_button_changed
        )

        self._showpw_switch.props.active = config.get_show_password_fields()
        self._showpw_switch.connect(
            "notify::active", self._on_settings_showpw_switch_switched
        )

        self._clear_button.connect("clicked", self._on_settings_clear_recents_clicked)
        if not config.get_last_opened_list():
            self._clear_button.props.sensitive = False

        # Unlock
        remember_composite_key = config.get_remember_composite_key()
        self._remember_switch.props.active = remember_composite_key
        self._remember_switch.connect(
            "notify::active", self._on_settings_remember_switch_switched
        )

        remember_method = config.get_remember_unlock_method()
        self._remember_method_switch.props.active = remember_method
        self._remember_method_switch.connect(
            "notify::active", self._on_settings_remember_method_switch_switched
        )

    def _on_generator_use_uppercase_switch_switched(
        self, switch: Gtk.Switch, _: None
    ) -> None:
        config.set_generator_use_uppercase(switch.get_active())

    def _on_generator_use_lowercase_switch_switched(
        self, switch: Gtk.Switch, _: None
    ) -> None:
        config.set_generator_use_lowercase(switch.get_active())

    def _on_generator_use_symbols_switch_switched(
        self, switch: Gtk.Switch, _: None
    ) -> None:
        config.set_generator_use_symbols(switch.get_active())

    def _on_generator_use_numbers_switch_switched(
        self, switch: Gtk.Switch, _: None
    ) -> None:
        config.set_generator_use_numbers(switch.get_active())

    def _on_generator_words_spin_button_changed(
        self, spin_button: Gtk.SpinButton
    ) -> None:
        config.set_generator_words(spin_button.get_value_as_int())

    def _on_generator_length_spin_button_changed(
        self, spin_button: Gtk.SpinButton
    ) -> None:
        config.set_generator_length(spin_button.get_value_as_int())

    def _on_generator_separator_entry_changed(self, entry: Gtk.Entry) -> None:
        config.set_generator_separator(entry.get_text())

    def _on_settings_theme_switch_switched(self, switch_button, _gparam):
        gtk_settings = Gtk.Settings.get_default()
        value = switch_button.get_active()
        config.set_dark_theme(value)
        gtk_settings.set_property("gtk-application-prefer-dark-theme", value)

    def _on_settings_fstart_switch_switched(self, switch_button, _gparam):
        config.set_first_start_screen(switch_button.get_active())

    def _on_settings_save_switch_switched(self, switch_button, _gparam):
        config.set_save_automatically(switch_button.get_active())

    def _on_settings_lockdb_spin_button_changed(self, spin_button):
        config.set_database_lock_timeout(spin_button.get_value())
        for db in self.window.opened_databases:
            db.start_database_lock_timer()

    def _on_settings_clearcb_spin_button_changed(self, spin_button):
        config.set_clear_clipboard(spin_button.get_value())

    def _on_settings_showpw_switch_switched(self, switch_button, _gparam):
        config.set_show_password_fields(switch_button.get_active())

    def _on_settings_clear_recents_clicked(self, widget):
        config.set_last_opened_list([])
        config.set_last_opened_database("")
        if not self.window.opened_databases or not self.window.container.get_n_pages():
            self.window.display_welcome_page()

        widget.set_sensitive(False)

    def _on_settings_remember_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            config.set_remember_composite_key(True)
        else:
            config.set_remember_composite_key(False)
            config.set_last_used_composite_key("")

    def _on_settings_remember_method_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            config.set_remember_unlock_method(True)
        else:
            config.set_remember_unlock_method(False)
            config.set_unlock_method(
                UnlockMethod.PASSWORD)
