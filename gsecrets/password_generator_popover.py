# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _

from gi.repository import GObject, Gtk

import gsecrets.config_manager as config
from gsecrets.passphrase_generator import Passphrase
from gsecrets.password_generator import generate as generate_pwd


@Gtk.Template(
    resource_path="/org/gnome/World/Secrets/gtk/password_generator_popover.ui"
)
class PasswordGeneratorPopover(Gtk.Popover):

    __gtype_name__ = "PasswordGeneratorPopover"

    _digit_spin_button = Gtk.Template.Child()
    _generate_button = Gtk.Template.Child()
    _high_letter_toggle_btn = Gtk.Template.Child()
    _low_letter_toggle_button = Gtk.Template.Child()
    _number_toggle_button = Gtk.Template.Child()
    _separator_entry = Gtk.Template.Child()
    _special_toggle_button = Gtk.Template.Child()
    _stack = Gtk.Template.Child()
    _words_spin_button = Gtk.Template.Child()

    def __init__(self):
        """Popover to generate a new password for an entry

        :param UnlockedDatabase database_view: database view
        """
        super().__init__()

        use_lowercase = config.get_generator_use_lowercase()
        self._low_letter_toggle_button.set_active(use_lowercase)

        use_uppercase = config.get_generator_use_uppercase()
        self._high_letter_toggle_btn.set_active(use_uppercase)

        use_numbers = config.get_generator_use_numbers()
        self._number_toggle_button.set_active(use_numbers)

        use_symbols = config.get_generator_use_symbols()
        self._special_toggle_button.set_active(use_symbols)

        length = config.get_generator_length()
        self._digit_spin_button.set_value(length)

        separator = config.get_generator_separator()
        self._separator_entry.set_text(separator)

        words = config.get_generator_words()
        self._words_spin_button.set_value(words)

        self._low_letter_toggle_button.connect("toggled", self.on_toggled_callback)
        self._high_letter_toggle_btn.connect("toggled", self.on_toggled_callback)
        self._number_toggle_button.connect("toggled", self.on_toggled_callback)
        self._special_toggle_button.connect("toggled", self.on_toggled_callback)

        self.set_tooltips()

    def on_toggled_callback(self, _button):
        self.set_tooltips()

    def set_tooltips(self):
        use_uppercase: bool = self._high_letter_toggle_btn.props.active
        use_lowercase: bool = self._low_letter_toggle_button.props.active
        use_numbers: bool = self._number_toggle_button.props.active
        use_symbols: bool = self._special_toggle_button.props.active

        self._low_letter_toggle_button.set_tooltip_text(
            # TRANSLATORS This will be used in conjunction with either Include
            # or Exclude. e.g. Include Lowercase.
            _("{} Lowercase").format(_format_bool(use_lowercase))
        )
        self._high_letter_toggle_btn.set_tooltip_text(
            # TRANSLATORS This will be used in conjunction with either Include
            # or Exclude. e.g. Exclude Uppercase.
            _("{} Uppercase").format(_format_bool(use_uppercase))
        )
        self._number_toggle_button.set_tooltip_text(
            # TRANSLATORS This will be used in conjunction with either Include
            # or Exclude. e.g. Include Numbers.
            _("{} Numbers").format(_format_bool(use_numbers))
        )
        self._special_toggle_button.set_tooltip_text(
            # TRANSLATORS This will be used in conjunction with either Include
            # or Exclude. e.g. Include Symbols.
            _("{} Symbols").format(_format_bool(use_symbols))
        )

    @Gtk.Template.Callback()
    def _on_generate_button_clicked(self, _button: Gtk.Button) -> None:
        if self._stack.get_visible_child_name() == "password":
            use_uppercase: bool = self._high_letter_toggle_btn.props.active
            use_lowercase: bool = self._low_letter_toggle_button.props.active
            use_numbers: bool = self._number_toggle_button.props.active
            use_symbols: bool = self._special_toggle_button.props.active

            length: int = self._digit_spin_button.get_value_as_int()
            pass_text: str = generate_pwd(
                length, use_uppercase, use_lowercase, use_numbers, use_symbols
            )
            self.emit("generated", pass_text)
        else:
            separator: str = self._separator_entry.props.text
            words: int = self._words_spin_button.get_value_as_int()
            passphrase_generator = Passphrase()
            passphrase_generator.connect("generated", self.on_passphrase_generated)
            passphrase_generator.generate(words, separator)

    @GObject.Signal(arg_types=(str,))
    def generated(self, _password):
        return

    def on_passphrase_generated(self, _passphrase_gen, passphrase):
        self.emit("generated", passphrase)


def _format_bool(boolean):
    if boolean:
        # TRANSLATORS This will be used in conjunction with one of Lowercase,
        # Uppercase, Numbers, or Symbols. eg. Exclude Lowercase.
        return _("Exclude")

    # TRANSLATORS This will be used in conjunction with one of Lowercase,
    # Uppercase, Numbers, or Symbols. eg. Include Lowercase.
    return _("Include")
