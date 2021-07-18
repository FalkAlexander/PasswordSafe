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

        self._signals = GObject.SignalGroup.new(SafeGroup)

        self._signals.connect_closure(
            "notify::name", self._on_group_name_changed, False
        )

        self.unlocked_database = unlocked_database

        self.unlocked_database.bind_property(
            "selection_mode",
            self._checkbox_revealer,
            "reveal-child",
            GObject.BindingFlags.SYNC_CREATE,
        )
        self.unlocked_database.bind_property(
            "selection_mode",
            self.edit_button,
            "sensitive",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.INVERT_BOOLEAN,
        )

    @GObject.Property(type=SafeGroup)
    def safe_group(self):
        return self._safe_group

    @safe_group.setter  # type: ignore
    def safe_group(self, element):
        assert isinstance(element, SafeGroup)

        self._safe_group = element
        self._signals.props.target = element

        self._on_group_name_changed(element, None)

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
        self.unlocked_database.start_database_lock_timer()

        if self.selection_checkbox.get_active():
            self.unlocked_database.selection_mode_headerbar.add_group(self)
        else:
            self.unlocked_database.selection_mode_headerbar.remove_group(self)

    @Gtk.Template.Callback()
    def on_group_edit_button_clicked(self, _button: Gtk.Button) -> None:
        """Edit button in a GroupRow was clicked

        button: The edit button in the GroupRow"""
        self.unlocked_database.start_database_lock_timer()  # Reset the lock timer

        self.unlocked_database.show_edit_page(self._safe_group)

    def _on_group_name_changed(
        self, safe_group: SafeGroup, _value: GObject.ParamSpec
    ) -> None:
        group_name = GLib.markup_escape_text(safe_group.name)
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
