# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from typing import Optional
from uuid import UUID

from gi.repository import Gdk, Gtk
from pykeepass.entry import Entry

import passwordsafe.config_manager
import passwordsafe.password_generator as pwd_generator
from passwordsafe.history_buffer import HistoryEntryBuffer
from passwordsafe.password_generator_popover import PasswordGeneratorPopover
if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.scrolled_page import ScrolledPage
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/password_entry_row.ui")
class PasswordEntryRow(Gtk.ListBoxRow):

    __gtype_name__ = "PasswordEntryRow"

    _generate_password_button = Gtk.Template.Child()
    _password_level_bar = Gtk.Template.Child()
    _password_value_entry = Gtk.Template.Child()
    _show_password_button = Gtk.Template.Child()

    def __init__(self, unlocked_database: UnlockedDatabase) -> None:
        """Widget to set the password of an entry

        :param unlocked_database: unlocked database
        """
        super().__init__()

        self._unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager

        entry_uuid: UUID = unlocked_database.current_element.uuid
        self._password_value_entry.set_buffer(HistoryEntryBuffer([]))
        pwd_value = self._db_manager.get_entry_password(entry_uuid)
        self._password_value_entry.props.text = pwd_value
        show_pwds = passwordsafe.config_manager.get_show_password_fields()
        self._password_value_entry.props.visibility = show_pwds

        self._pwd_popover = PasswordGeneratorPopover(self._unlocked_database)
        self._pwd_popover.bind_property(
            "password", self._password_value_entry, "text")
        self._generate_password_button.set_popover(self._pwd_popover)

        self._unlocked_database.bind_accelerator(
            self._unlocked_database.accelerators, self._password_value_entry,
            "<Control><Shift>c", signal="copy-clipboard")

        self._password_level_bar.add_offset_value("weak", 1.0)
        self._password_level_bar.add_offset_value("medium", 3.0)
        self._password_level_bar.add_offset_value("strong", 4.0)
        self._password_level_bar.add_offset_value("secure", 5.0)
        self._set_password_level_bar()

    @Gtk.Template.Callback()
    def _on_copy_secondary_button_clicked(
            self, widget: Gtk.Entry,
            _position: Optional[Gtk.EntryIconPosition] = None,
            _event: Optional[Gdk.Event] = None) -> None:
        self._unlocked_database.send_to_clipboard(widget.props.text)

    @Gtk.Template.Callback()
    def _on_password_value_changed(self, widget: Gtk.Entry) -> None:
        self._unlocked_database.start_database_lock_timer()

        entry: Entry = self._unlocked_database.current_element
        current_password = self._db_manager.get_entry_password(entry)
        new_password = widget.props.text
        if new_password != current_password:
            page: ScrolledPage = self._unlocked_database.get_current_page()
            page.is_dirty = True
            self._db_manager.set_entry_password(entry, new_password)

        self._set_password_level_bar()

    @Gtk.Template.Callback()
    def _on_show_password_button_toggled(
            self, widget: Gtk.ToggleButton) -> None:
        # pylint: disable=unused-argument
        self._unlocked_database.start_database_lock_timer()
        entry_visibility = self._password_value_entry.props.visibility
        self._password_value_entry.props.visibility = not entry_visibility

    def _set_password_level_bar(self) -> None:
        pwd_text: str = self._password_value_entry.props.text

        if pwd_text.startswith("{REF:P"):
            try:
                uuid: UUID = UUID(
                    self._unlocked_database.reference_to_hex_uuid(pwd_text))
                password: str = self._db_manager.get_entry_password(uuid)
            except ValueError:
                logging.warning(
                    "Failed to look up password for reference '%s'", password)
                password = pwd_text
        else:
            password = pwd_text

        password_strength: Optional[float] = pwd_generator.strength(password)
        if password_strength is not None:
            self._password_level_bar.props.value = password_strength
