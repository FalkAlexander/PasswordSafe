# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from typing import Optional

from gi.repository import Gdk, Gtk

import passwordsafe.config_manager
import passwordsafe.password_generator as pwd_generator
from passwordsafe.history_buffer import HistoryEntryBuffer
from passwordsafe.password_generator_popover import PasswordGeneratorPopover
if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.safe_element import SafeEntry
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/password_entry_row.ui")
class PasswordEntryRow(Gtk.Box):

    __gtype_name__ = "PasswordEntryRow"

    _generate_password_button = Gtk.Template.Child()
    _password_level_bar = Gtk.Template.Child()
    _password_value_entry = Gtk.Template.Child()
    _copy_password_button = Gtk.Template.Child()

    def __init__(self, unlocked_database: UnlockedDatabase) -> None:
        """Widget to set the password of an entry

        :param unlocked_database: unlocked database
        """
        super().__init__()

        self._unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager

        self._safe_entry: SafeEntry = unlocked_database.current_element
        self._password_value_entry.set_buffer(HistoryEntryBuffer([]))

        self._password_value_entry.props.text = self._safe_entry.props.password
        self._password_value_entry.bind_property("text", self._safe_entry, "password")

        show_pwds = passwordsafe.config_manager.get_show_password_fields()
        self._password_value_entry.props.visibility = show_pwds

        self._pwd_popover = PasswordGeneratorPopover(self._unlocked_database)
        self._pwd_popover.bind_property(
            "password", self._password_value_entry, "text")
        self._generate_password_button.set_popover(self._pwd_popover)

        self._unlocked_database.bind_accelerator(
            self._password_value_entry, "<primary><Shift>c", signal="copy-clipboard"
        )

        self._password_level_bar.add_offset_value("weak", 1.0)
        self._password_level_bar.add_offset_value("medium", 3.0)
        self._password_level_bar.add_offset_value("strong", 4.0)
        self._password_level_bar.add_offset_value("secure", 5.0)
        self._set_password_level_bar()

    @Gtk.Template.Callback()
    def _on_copy_password_button_clicked(self, _widget: Gtk.Button) -> None:
        self._unlocked_database.send_to_clipboard(self._password_value_entry.props.text)

    @Gtk.Template.Callback()
    def _on_password_value_changed(self, _widget: Gtk.Entry) -> None:
        """Invoked when the password entry has changed

        Take note that this callback is already invoked after the initial
        population of the entry when nothing has really been changed by
        the user, so be careful of doing things here that could have unwanted
        side-effects.
        """
        self._unlocked_database.start_database_lock_timer()
        self._set_password_level_bar()

    @Gtk.Template.Callback()
    def _on_show_password_button_toggled(
        self,
        _widget: Gtk.Entry,
        _position: Optional[Gtk.EntryIconPosition] = None,
        _event: Optional[Gdk.Event] = None,
    ) -> None:
        self._unlocked_database.start_database_lock_timer()
        entry_visibility = self._password_value_entry.props.visibility
        self._password_value_entry.props.visibility = not entry_visibility

    def _set_password_level_bar(self) -> None:
        pwd_text: str = self._password_value_entry.props.text

        if pwd_text.startswith("{REF:P"):
            try:
                password: str = self._safe_entry.password
            except ValueError:
                logging.warning(
                    "Failed to look up password for reference '%s'", password)
                password = pwd_text
        else:
            password = pwd_text

        password_strength: Optional[float] = pwd_generator.strength(password)
        if password_strength is not None:
            self._password_level_bar.props.value = password_strength
