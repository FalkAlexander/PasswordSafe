# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, Gio, Gtk

import passwordsafe.config_manager as config
from passwordsafe.const import APP_ID
from passwordsafe.config_manager import UnlockMethod


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/settings_dialog.ui")
class SettingsDialog(Adw.PreferencesWindow):

    __gtype_name__ = "SettingsDialog"

    _clear_button = Gtk.Template.Child()
    _clearcb_spin_button = Gtk.Template.Child()
    _generator_length_spin_button = Gtk.Template.Child()
    _generator_separator_entry = Gtk.Template.Child()
    _generator_words_spin_button = Gtk.Template.Child()
    _lockdb_spin_button = Gtk.Template.Child()
    _remember_method_switch = Gtk.Template.Child()
    _remember_switch = Gtk.Template.Child()
    _showpw_switch = Gtk.Template.Child()

    def __init__(self, window):
        super().__init__()

        self.window = window
        self.props.transient_for = self.window
        self._set_config_values()

    def _set_config_values(self):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        action_group = Gio.SimpleActionGroup.new()
        settings = Gio.Settings.new(APP_ID)

        # General
        dark_mode_action = settings.create_action("dark-theme")
        action_group.add_action(dark_mode_action)

        first_start_action = settings.create_action("first-start-screen")
        action_group.add_action(first_start_action)

        # Safe
        save_automatically_action = settings.create_action("save-automatically")
        action_group.add_action(save_automatically_action)

        # Password Generator
        settings.bind("generator-length", self._generator_length_spin_button, "value", Gio.SettingsBindFlags.DEFAULT)

        use_uppercase_action = settings.create_action("generator-use-uppercase")
        action_group.add_action(use_uppercase_action)

        use_lowercase_action = settings.create_action("generator-use-lowercase")
        action_group.add_action(use_lowercase_action)

        use_numbers_action = settings.create_action("generator-use-numbers")
        action_group.add_action(use_numbers_action)

        use_symbols_action = settings.create_action("generator-use-symbols")
        action_group.add_action(use_symbols_action)

        # Passphrase Generation
        settings.bind("generator-words", self._generator_words_spin_button, "value", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("generator-separator", self._generator_separator_entry, "text", Gio.SettingsBindFlags.DEFAULT)

        # Security
        settings.bind("database-lock-timeout", self._lockdb_spin_button, "value", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("clear-clipboard", self._clearcb_spin_button, "value", Gio.SettingsBindFlags.DEFAULT)

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

        self.insert_action_group("settings", action_group)

    def _on_settings_showpw_switch_switched(self, switch_button, _gparam):
        config.set_show_password_fields(switch_button.get_active())

    def _on_settings_clear_recents_clicked(self, widget):
        config.set_last_opened_list([])
        config.set_last_opened_database("")
        if self.window.view == self.window.View.RECENT_FILES:
            self.window.view = self.window.View.WELCOME

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
            config.set_unlock_method(UnlockMethod.PASSWORD)
