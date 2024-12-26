# SPDX-License-Identifier: GPL-3.0-only
"""Responsible for displaying the Entry/Group Properties."""

from __future__ import annotations

from gi.repository import Adw, Gtk

from gsecrets.utils import format_time


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/properties_dialog.ui")
class PropertiesDialog(Adw.Dialog):
    """Displays a modal dialog with Entry/Group Properties."""

    __gtype_name__ = "PropertiesDialog"

    _accessed_row = Gtk.Template.Child()
    _created_row = Gtk.Template.Child()
    _modified_row = Gtk.Template.Child()
    _uuid_row = Gtk.Template.Child()

    def __init__(self, database):
        super().__init__()

        self.__database = database
        self.__db_manager = database.database_manager
        self.__signal_handle = 0

        self.__setup_signals()
        self.__setup_widgets()

    def __update_properties(self) -> None:
        """Construct dialog content with the attributes of the Entry|Group."""
        element = self.__database.current_element
        hex_uuid = element.uuid.hex.upper()
        self._uuid_row.props.subtitle = hex_uuid
        self._accessed_row.props.subtitle = format_time(element.atime)
        self._modified_row.props.subtitle = format_time(element.mtime)
        self._created_row.props.subtitle = format_time(element.ctime)

    def __setup_signals(self) -> None:
        handle = self.__db_manager.connect("notify::locked", self.__on_locked)
        self.__signal_handle = handle

    def __setup_widgets(self) -> None:
        self.__update_properties()

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.close()

    def do_closed(self) -> None:
        if handle := self.__signal_handle:
            self.__db_manager.disconnect(handle)
            self.__signal_handle = 0
