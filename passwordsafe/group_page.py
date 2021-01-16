# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing

from gi.repository import GObject, Gtk

from passwordsafe.history_buffer import HistoryEntryBuffer, HistoryTextBuffer

if typing.TYPE_CHECKING:
    from passwordsafe.safe_element import SafeGroup


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/group_page.ui")
class GroupPage(Gtk.ScrolledWindow):

    __gtype_name__ = "GroupPage"

    name_property_value_entry = Gtk.Template.Child()
    notes_property_value_entry = Gtk.Template.Child()

    def __init__(self, unlocked_database):
        super().__init__()

        self.unlocked_database = unlocked_database

        safe_group = self.unlocked_database.current_element
        notes_buffer = HistoryTextBuffer([])

        # Setup Widgets
        self.name_property_value_entry.set_buffer(HistoryEntryBuffer([]))
        self.name_property_value_entry.grab_focus()
        self.notes_property_value_entry.set_buffer(notes_buffer)

        # Connect Signals
        safe_group.connect("updated", self._on_safe_group_updated)
        safe_group.bind_property(
            "name", self.name_property_value_entry, "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL
        )
        safe_group.bind_property(
            "notes", notes_buffer, "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL
        )

    def _on_safe_group_updated(self, _safe_group: SafeGroup) -> None:
        self.unlocked_database.start_database_lock_timer()
