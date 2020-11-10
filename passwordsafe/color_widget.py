# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations
import typing
from enum import Enum
from uuid import UUID

from gi.repository import GObject, Gtk

if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.scrolled_page import ScrolledPage
    from passwordsafe.unlocked_database import UnlockedDatabase


class Color(Enum):
    NONE = "NoneColorButton"
    BLUE = "BlueColorButton"
    GREEN = "GreenColorButton"
    ORANGE = "OrangeColorButton"
    RED = "RedColorButton"
    PURPLE = "PurpleColorButton"
    BROWN = "BrownColorButton"


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/color_button.ui")
class ColorButton(Gtk.RadioButton):  # pylint: disable=too-few-public-methods

    __gtype_name__ = "ColorButton"

    _selected_image = Gtk.Template.Child()

    selected = GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, color: Color, selected: bool):
        """RadioButton to select the color of an entry

        :param Color color: color of the button
        :param bool selected: True if the color is selected
        """
        super().__init__()

        self._color: Color = color
        self.get_style_context().add_class(self._color.value)

        if self._color == Color.NONE:
            image_class: str = "DarkIcon"
        else:
            image_class = "BrightIcon"

        self._selected_image.get_style_context().add_class(image_class)

        self.bind_property("selected", self._selected_image, "visible")
        self.props.selected = selected

    @property
    def color(self) -> str:
        """"Color of the widget."""
        return self._color.value


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/color_entry_row.ui")
class ColorEntryRow(Gtk.ListBoxRow):  # pylint: disable=too-few-public-methods

    __gtype_name__ = "ColorEntryRow"

    _box = Gtk.Template.Child()

    def __init__(
            self, unlocked_database: UnlockedDatabase,
            scrolled_page: ScrolledPage, entry_uuid: UUID):
        """Widget to select the color of an entry

        :param UnlockedDatabase unlocked_database: unlocked database
        :param ScrolledPage scrolled_page: container of the widget
        :param UUID entry_uuid: uuid of the entry
        """
        super().__init__()

        self._unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager
        self._scrolled_page: ScrolledPage = scrolled_page
        self._entry_uuid: UUID = entry_uuid

        self._selected_color: str = self._db_manager.get_entry_color_from_entry_uuid(
            entry_uuid)

        for color in Color:
            active: bool = (self._selected_color == color.value)
            color_button: ColorButton = ColorButton(color, active)
            color_button.connect("clicked", self._on_color_activated)
            self._box.add(color_button)

    def _on_color_activated(self, selected_button: Gtk.Button) -> None:
        self._unlocked_database.start_database_lock_timer()
        if selected_button.props.selected:
            return

        for color_button in self._box.get_children():
            selected: bool = (color_button == selected_button)
            color_button.props.selected = selected

        self._scrolled_page.is_dirty = True
        self._db_manager.set_entry_color(
            self._entry_uuid, selected_button.color)
