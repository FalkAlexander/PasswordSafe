# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, Gio, Gtk

import passwordsafe.config_manager as config
from passwordsafe.const import APP_ID


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/settings_dialog.ui")
class SettingsDialog(Adw.PreferencesWindow):

    __gtype_name__ = "SettingsDialog"

    _clear_button = Gtk.Template.Child()
    _clearcb_spin_button = Gtk.Template.Child()
    _dark_theme_row = Gtk.Template.Child()
    _generator_length_spin_button = Gtk.Template.Child()
    _generator_separator_entry = Gtk.Template.Child()
    _generator_words_spin_button = Gtk.Template.Child()
    _lockdb_spin_button = Gtk.Template.Child()

    def __init__(self, window):
        super().__init__()

        self.window = window
        self.props.transient_for = self.window
        self._set_config_values()

    def on_dark_theme(self, action, *args):
        manager = Adw.StyleManager.get_default()
        if action.props.state:
            manager.props.color_scheme = Adw.ColorScheme.PREFER_DARK
        else:
            manager.props.color_scheme = Adw.ColorScheme.DEFAULT

    def _set_config_values(self):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        action_group = Gio.SimpleActionGroup.new()
        settings = Gio.Settings.new(APP_ID)

        # General
        manager = Adw.StyleManager.get_default()
        if not manager.props.system_supports_color_schemes:
            self._dark_theme_row.props.visible = True
            dark_mode_action = settings.create_action("dark-theme")
            action_group.add_action(dark_mode_action)
            dark_mode_action.connect("notify::state", self.on_dark_theme)

        first_start_action = settings.create_action("first-start-screen")
        action_group.add_action(first_start_action)

        # Safe
        save_automatically_action = settings.create_action("save-automatically")
        action_group.add_action(save_automatically_action)

        # Password Generator
        settings.bind(
            "generator-length",
            self._generator_length_spin_button,
            "value",
            Gio.SettingsBindFlags.DEFAULT,
        )

        use_uppercase_action = settings.create_action("generator-use-uppercase")
        action_group.add_action(use_uppercase_action)

        use_lowercase_action = settings.create_action("generator-use-lowercase")
        action_group.add_action(use_lowercase_action)

        use_numbers_action = settings.create_action("generator-use-numbers")
        action_group.add_action(use_numbers_action)

        use_symbols_action = settings.create_action("generator-use-symbols")
        action_group.add_action(use_symbols_action)

        # Passphrase Generation
        settings.bind(
            "generator-words",
            self._generator_words_spin_button,
            "value",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "generator-separator",
            self._generator_separator_entry,
            "text",
            Gio.SettingsBindFlags.DEFAULT,
        )

        # Security
        settings.bind(
            "database-lock-timeout",
            self._lockdb_spin_button,
            "value",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "clear-clipboard",
            self._clearcb_spin_button,
            "value",
            Gio.SettingsBindFlags.DEFAULT,
        )

        self._clear_button.connect("clicked", self._on_settings_clear_recents_clicked)
        if not config.get_last_opened_list():
            self._clear_button.props.sensitive = False

        # Unlock
        remember_composite_key_action = settings.create_action("remember-composite-key")
        action_group.add_action(remember_composite_key_action)
        remember_composite_key_action.connect(
            "notify::state", self._on_remember_composite_key
        )

        self.insert_action_group("settings", action_group)

    def _on_remember_composite_key(self, action, _param):
        if not action.props.state:
            config.set_last_used_composite_key([])

    def _on_settings_clear_recents_clicked(self, widget):
        config.set_last_opened_list([])
        config.set_last_opened_database("")
        if self.window.view == self.window.View.RECENT_FILES:
            self.window.view = self.window.View.WELCOME

        widget.set_sensitive(False)
