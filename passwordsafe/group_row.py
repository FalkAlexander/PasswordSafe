# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk

from passwordsafe.safe_element import SafeGroup

if typing.TYPE_CHECKING:
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/group_row.ui")
class GroupRow(Adw.ActionRow):

    __gtype_name__ = "GroupRow"

    _checkbox_revealer = Gtk.Template.Child()
    selection_checkbox = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()

    def __init__(self, unlocked_database, safe_group):
        super().__init__()

        assert isinstance(safe_group, SafeGroup)
        self.unlocked_database = unlocked_database
        self.safe_group = safe_group
        self.assemble_group_row()

    def assemble_group_row(self):
        # Name title
        self.safe_group.connect("notify::name", self._on_group_name_changed)
        self._on_group_name_changed(self.safe_group, None)

        # Selection Mode Checkboxes
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
                active = self.selection_checkbox.props.active
                self.selection_checkbox.props.active = not active
            else:
                db_view.props.selection_mode = True
                self.selection_checkbox.props.active = True

    @Gtk.Template.Callback()
    def on_selection_checkbox_toggled(self, _widget):
        if self.selection_checkbox.get_active():
            self.unlocked_database.selection_mode_headerbar.add_group(self)
        else:
            self.unlocked_database.selection_mode_headerbar.remove_group(self)

    @Gtk.Template.Callback()
    def on_group_edit_button_clicked(self, _button: Gtk.Button) -> None:
        """Edit button in a GroupRow was clicked

        button: The edit button in the GroupRow"""
        self.unlocked_database.start_database_lock_timer()  # Reset the lock timer

        self.unlocked_database.show_edit_page(self.safe_group)

    def _on_group_name_changed(
        self, _safe_group: SafeGroup, _value: GObject.ParamSpec
    ) -> None:
        group_name = self.safe_group.name
        if group_name:
            self.remove_css_class("italic-title")
            self.props.title = group_name
        else:
            self.add_css_class("italic-title")
            self.props.title = _("Title not Specified")

    @Gtk.Template.Callback()
    def _on_long_press_gesture_pressed(self, _gesture, _x, _y):
        self.unlocked_database.props.selection_mode = True
        self.selection_checkbox.props.active = not self.selection_checkbox.props.active
