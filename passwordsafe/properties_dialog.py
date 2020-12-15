# SPDX-License-Identifier: GPL-3.0-only
"""Responsible for displaying the Entry/Group Properties"""
from __future__ import annotations

from gi.repository import Gtk, Gdk, Handy


class PropertiesDialog:
    """Displays a modal dialog with Entry/Group Properties"""

    def __init__(self, database):
        self.__builder = Gtk.Builder()
        self.__builder.add_from_resource("/org/gnome/PasswordSafe/properties_dialog.ui")
        self.__dialog = self.__builder.get_object("properties_dialog")
        self.__database = database
        self.__db_manager = database.database_manager
        self.__setup_signals()
        self.__setup_widgets()

    def present(self):
        """Present the dialog"""
        self.__dialog.present()

    def __update_properties(self) -> None:
        """Construct dialog content with the attributes of the Entry|Group"""
        element = self.__database.current_element
        hex_uuid = element.uuid.hex.upper()
        self.__builder.get_object("label_uuid").set_text(hex_uuid)
        self.__builder.get_object("label_accessed").set_text(
            self.__db_manager.get_element_acessed_date(element)
        )
        self.__builder.get_object("label_modified").set_text(
            self.__db_manager.get_element_modified_date(element)
        )
        self.__builder.get_object("label_created").set_text(
            self.__db_manager.get_element_creation_date(element)
        )

    def __setup_signals(self) -> None:
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self.__on_key_press_event)
        self.__dialog.add_controller(controller)
        self.__db_manager.connect("notify::locked", self.__on_locked)

    def __setup_widgets(self) -> None:
        self.__update_properties()
        self.__dialog.set_modal(True)
        self.__dialog.set_transient_for(self.__database.window)

    def __on_key_press_event(self, _controller, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape:
            self.__dialog.close()
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.__dialog.close()
