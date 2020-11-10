from __future__ import annotations

import typing
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

    @Gtk.Template.Callback()
    def _on_generate_button_clicked(self, _button: Gtk.Button) -> None:
        self._db_view.start_database_lock_timer()

        if self._stack.get_visible_child_name() == "password":
            has_high_letter: bool = self._high_letter_toggle_btn.props.active
            has_low_letter: bool = self._low_letter_toggle_button.props.active
            has_number: bool = self._number_toggle_button.props.active
            has_special: bool = self._special_toggle_button.props.active

            digits: int = self._digit_spin_button.get_value_as_int()
            pass_text: str = generate_pwd(
                digits, has_high_letter, has_low_letter, has_number,
                has_special)
        else:
            separator: str = self._separator_entry.props.text
            words: int = self._words_spin_button.get_value_as_int()
            pass_text = generate_phrase(words, separator)

        self.props.password = pass_text
