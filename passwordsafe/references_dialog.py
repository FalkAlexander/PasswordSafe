# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from typing import Any

from gi.repository import Gio, Gtk


class ReferencesDialog():
    __property = "P"

    def __init__(self, unlocked_database):
        self.__unlocked_database = unlocked_database
        self.__database_manager = unlocked_database.database_manager
        self.__builder = Gtk.Builder()
        self.__builder.add_from_resource("/org/gnome/PasswordSafe/references_dialog.ui")

        self.__reference_entry = self.__builder.get_object("reference_entry")
        self.__dialog = self.__builder.get_object("references_dialog")

        self.__setup_actions()
        self.__setup_signals()
        self.__setup_widgets()

    def present(self) -> None:
        self.__dialog.present()

    def __setup_widgets(self) -> None:
        self.__dialog.set_modal(True)
        self.__dialog.set_transient_for(self.__unlocked_database.window)
        self.__update_reference_entry()

    def __setup_signals(self) -> None:
        self.__reference_entry.connect("icon-press", self.__on_copy_secondary_button_clicked)
        self.__connect_model_buttons_signals()
        self.__database_manager.connect("notify::locked", self.__on_locked)

    def __setup_actions(self) -> None:
        action_group = Gio.SimpleActionGroup.new()
        for label in ["U", "N", "A", "P", "T"]:
            simple_action = Gio.SimpleAction.new(label, None)
            simple_action.connect("activate", self.__on_property_model_button_clicked)
            action_group.insert(simple_action)
        self.__dialog.insert_action_group("reference", action_group)

    def __connect_model_buttons_signals(self):
        self.__builder.get_object("property_label_gesture").connect(
            "pressed", self.__open_codes_popover)
        self.__builder.get_object("identifier_label_gesture").connect("pressed", self.__open_codes_popover)
        self.__builder.get_object("uuid_label_gesture").connect("pressed", self.__open_uuid_popover)

        uuid_popover = self.__builder.get_object("uuid_popover")
        uuid_popover.set_parent(self.__builder.get_object("uuid_label"))

        codes_popover = self.__builder.get_object("codes_popover")
        codes_popover.set_parent(self.__builder.get_object("property_label"))

    def __update_reference_entry(self):
        """Update the reference entry and selected label text."""
        uuid = self.__unlocked_database.current_element.uuid
        encoded_uuid = uuid.hex.upper()

        self.__builder.get_object("property_popover_button").set_label(self.__property)

        self.__reference_entry.set_text("{REF:" + self.__property + "@I:" + encoded_uuid + "}")

    def __open_codes_popover(self, _gesture, _n_points, _x, _y, _data=None):
        codes_popover = self.__builder.get_object("codes_popover")
        codes_popover.popup()

    def __open_uuid_popover(self, _gesture, _n_points, _x, _y, _data=None):
        uuid_popover = self.__builder.get_object("uuid_popover")
        uuid_popover.popup()

    def __on_copy_secondary_button_clicked(self, entry, _position):
        self.__unlocked_database.start_database_lock_timer()
        self.__unlocked_database.clipboard.set(entry.get_text())

    def __on_property_model_button_clicked(self, action: Gio.SimpleAction, _data: Any = None) -> None:
        self.__unlocked_database.start_database_lock_timer()
        self.__property = action.props.name
        self.__update_reference_entry()

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.__dialog.close()
