# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing

import passwordsafe.config_manager as config

from gi.repository import GObject, Gtk

from passwordsafe.passphrase_generator import generate as generate_phrase
from passwordsafe.password_generator import generate as generate_pwd

if typing.TYPE_CHECKING:
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(
    resource_path="/org/gnome/PasswordSafe/password_generator_popover.ui")
class PasswordGeneratorPopover(Gtk.Popover):  # pylint: disable=too-few-public-methods

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

    password = GObject.Property(
        type=str, default="", flags=GObject.ParamFlags.READWRITE)

    def __init__(self, database_view: UnlockedDatabase):
        """Popover to generate a new password for an entry

        :param UnlockedDatabase database_view: database view
        """
        super().__init__()

        self._db_view: UnlockedDatabase = database_view

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

    @Gtk.Template.Callback()
    def _on_generate_button_clicked(self, _button: Gtk.Button) -> None:
        self._db_view.start_database_lock_timer()

        if self._stack.get_visible_child_name() == "password":
            use_lowercase: bool = self._low_letter_toggle_button.props.active
            config.set_generator_use_lowercase(use_lowercase)

            use_uppercase: bool = self._high_letter_toggle_btn.props.active
            config.set_generator_use_uppercase(use_uppercase)

            use_numbers: bool = self._number_toggle_button.props.active
            config.set_generator_use_numbers(use_numbers)

            use_symbols: bool = self._special_toggle_button.props.active
            config.set_generator_use_symbols(use_symbols)

            length: int = self._digit_spin_button.get_value_as_int()
            config.set_generator_length(length)

            self.props.password = generate_pwd()
        else:
            separator: str = self._separator_entry.props.text
            config.set_generator_separator(separator)

            words: int = self._words_spin_button.get_value_as_int()
            config.set_generator_words(words)

            self.props.password = generate_phrase()
