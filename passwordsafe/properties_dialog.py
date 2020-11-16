# SPDX-License-Identifier: GPL-3.0-only
"""Responsible for displaying the Entry/Group Properties"""
from __future__ import annotations

from gi.repository import Gtk, Gdk, Handy


class PropertiesDialog:
    """Displays a modal dialog with Entry/Group Properties"""

    def __init__(self, database):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/properties_dialog.ui")
        self.dialog = self.builder.get_object("properties_dialog")
        self._database = database
        self._db_manager = database.database_manager
        self.dialog.set_transient_for(self._database.window)
        self.update_properties()
        self.connect_signals()

    def present(self):
        """Present the dialog"""
        self.dialog.present()

    def update_properties(self) -> None:
        """Construct dialog content with the attributes of the Entry|Group"""
        element = self._database.current_element
        hex_uuid = element.uuid.hex.upper()
        self.builder.get_object("label_uuid").set_text(hex_uuid)
        self.builder.get_object("label_accessed").set_text(
            self._db_manager.get_element_acessed_date(element)
        )
        self.builder.get_object("label_modified").set_text(
            self._db_manager.get_element_modified_date(element)
        )
        self.builder.get_object("label_created").set_text(
            self._db_manager.get_element_creation_date(element)
        )

    def connect_signals(self) -> None:
        self.dialog.connect("key-press-event", self._on_key_press_event)
        self._db_manager.connect("notify::locked", self.__on_locked)

    def _on_key_press_event(self, _window: Handy.Window, event: Gtk.Event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.dialog.close()
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def __on_locked(self, _database_manager, _value):
        self.dialog.close()
