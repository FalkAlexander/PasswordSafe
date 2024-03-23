# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing

from gi.repository import Adw, GObject, Gtk

from gsecrets.safe_element import EntryColor

if typing.TYPE_CHECKING:
    from gsecrets.database_manager import DatabaseManager
    from gsecrets.safe_element import SafeEntry
    from gsecrets.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/color_button.ui")
class ColorButton(Gtk.FlowBoxChild):
    __gtype_name__ = "ColorButton"

    _selected_image = Gtk.Template.Child()

    selected = GObject.Property(type=bool, default=False)

    def __init__(self, color: EntryColor, selected: bool):
        """RadioButton to select the color of an entry.

        :param EntryColor color: color of the button
        :param bool selected: True if the color is selected
        """
        super().__init__()

        self._color: EntryColor = color
        self.add_css_class(self._color.value)

        self.bind_property("selected", self._selected_image, "visible")
        self.props.selected = selected
        self.props.tooltip_text = color.to_translatable()

    @property
    def color(self) -> str:
        """Color of the widget."""
        return self._color.value

    @Gtk.Template.Callback()
    def _on_enter_event(
        self,
        _gesture: Gtk.EventControllerMotion,
        _x: int,
        _y: int,
    ) -> None:
        self.set_state_flags(Gtk.StateFlags.PRELIGHT, False)

    @Gtk.Template.Callback()
    def _on_leave_event(self, _gesture: Gtk.EventControllerMotion) -> None:
        self.unset_state_flags(Gtk.StateFlags.PRELIGHT)


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/color_entry_row.ui")
class ColorEntryRow(Adw.PreferencesGroup):
    __gtype_name__ = "ColorEntryRow"

    _flowbox = Gtk.Template.Child()

    def __init__(self, unlocked_database: UnlockedDatabase, safe_entry: SafeEntry):
        """Widget to select the color of an entry.

        :param UnlockedDatabase unlocked_database: unlocked database
        :param SafeEntry safe_entry: the safe entry
        """
        super().__init__()

        self._unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager
        self._safe_entry: SafeEntry = safe_entry

        for color in EntryColor:
            active: bool = safe_entry.props.color == color.value
            color_button: ColorButton = ColorButton(color, active)
            self._flowbox.insert(color_button, -1)
            if active:
                self._flowbox.select_child(color_button)

    @Gtk.Template.Callback()
    def _on_color_activated(
        self,
        _flowbox: Gtk.FlowBox,
        selected_child: Gtk.FlowBoxChild,
    ) -> None:
        if selected_child.props.selected:
            return

        for child in self._flowbox:  # pylint: disable=not-an-iterable
            selected: bool = child == selected_child
            child.props.selected = selected

        self._safe_entry.props.color = selected_child.color
