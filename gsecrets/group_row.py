# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gtk

from gsecrets.safe_element import SafeGroup

if typing.TYPE_CHECKING:
    from gsecrets.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/group_row.ui")
class GroupRow(Adw.Bin):

    __gtype_name__ = "GroupRow"

    _checkbox_revealer = Gtk.Template.Child()
    selection_checkbox = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()

    _safe_group = None

    title = GObject.Property(type=str, default="")

    def __init__(self, unlocked_database):
        super().__init__()

        self.unlocked_database = unlocked_database

    @GObject.Property(type=SafeGroup)
    def safe_group(self):
        return self._safe_group

    @safe_group.setter  # type: ignore
    def safe_group(self, element):
        self._safe_group = element
        # Name title
        element.connect("notify::name", self._on_group_name_changed)
        self._on_group_name_changed(element, None)

        # Selection Mode Checkboxes
        element.bind_property("selected", self.selection_checkbox, "active", GObject.BindingFlags.BIDIRECTIONAL)
        self.unlocked_database.bind_property(
            "selection_mode",
            self._checkbox_revealer,
            "reveal-child",
            GObject.BindingFlags.SYNC_CREATE,
        )

        # Edit Button
        self.unlocked_database.bind_property(
            "selection_mode",
            self.edit_button,
            "sensitive",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.INVERT_BOOLEAN,
        )

        element.bind_property(
            "sensitive", self, "sensitive", GObject.BindingFlags.SYNC_CREATE
        )

    @Gtk.Template.Callback()
    def _on_group_row_button_pressed(
        self,
        _gesture: Gtk.GestureClick,
        _n_press: int,
        _event_x: float,
        _event_y: float,
    ) -> None:
        # pylint: disable=too-many-arguments
        db_view: UnlockedDatabase = self.unlocked_database
        db_view.start_database_lock_timer()

        if not db_view.props.search_active:
            if db_view.props.selection_mode:
                selected = self._safe_group.props.selected
                self._safe_group.props.selected = not selected
            else:
                db_view.props.selection_mode = True
                self._safe_group.props.selected = True

    @Gtk.Template.Callback()
    def on_selection_checkbox_toggled(self, _widget):
        if self._safe_group.props.selected:
            self.unlocked_database.selection_mode_headerbar.add_group(self._safe_group)
        else:
            self.unlocked_database.selection_mode_headerbar.remove_group(self._safe_group)

    @Gtk.Template.Callback()
    def on_group_edit_button_clicked(self, _button: Gtk.Button) -> None:
        """Edit button in a GroupRow was clicked

        button: The edit button in the GroupRow"""
        self.unlocked_database.start_database_lock_timer()  # Reset the lock timer

        self.unlocked_database.show_edit_page(self._safe_group)

    def _on_group_name_changed(
        self, _safe_group: SafeGroup, _value: GObject.ParamSpec
    ) -> None:
        group_name = GLib.markup_escape_text(self.safe_group.name)
        if group_name:
            self.remove_css_class("italic-title")
            self.props.title = group_name
        else:
            self.add_css_class("italic-title")
            self.props.title = _("Title not Specified")

    @Gtk.Template.Callback()
    def _on_long_press_gesture_pressed(self, _gesture, _x, _y):
        self.unlocked_database.props.selection_mode = True
        self._safe_group.props.selected = not self._safe_group.props.selected
