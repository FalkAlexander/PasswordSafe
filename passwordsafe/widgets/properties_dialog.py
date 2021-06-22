# SPDX-License-Identifier: GPL-3.0-only
"""Responsible for displaying the Entry/Group Properties"""
from __future__ import annotations

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/properties_dialog.ui")
class PropertiesDialog(Adw.Window):
    """Displays a modal dialog with Entry/Group Properties"""

    __gtype_name__ = "PropertiesDialog"

    _accessed_label = Gtk.Template.Child()
    _created_label = Gtk.Template.Child()
    _modified_label = Gtk.Template.Child()
    _uuid_label = Gtk.Template.Child()

    def __init__(self, database):
        super().__init__()

        self.__database = database
        self.__db_manager = database.database_manager
        self.__setup_signals()
        self.__setup_widgets()

    def __update_properties(self) -> None:
        """Construct dialog content with the attributes of the Entry|Group"""
        element = self.__database.current_element
        hex_uuid = element.uuid.hex.upper()
        self._uuid_label.set_text(hex_uuid)
        self._accessed_label.set_text(
            self.__db_manager.get_element_acessed_date(element)
        )
        self._modified_label.set_text(
            self.__db_manager.get_element_modified_date(element)
        )
        self._created_label.set_text(
            self.__db_manager.get_element_creation_date(element)
        )

    def __setup_signals(self) -> None:
        self.__db_manager.connect("notify::locked", self.__on_locked)

    def __setup_widgets(self) -> None:
        self.__update_properties()
        self.set_modal(True)
        self.set_transient_for(self.__database.window)

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.close()
