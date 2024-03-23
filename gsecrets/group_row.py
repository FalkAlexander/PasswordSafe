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

    _prefix_stack = Gtk.Template.Child()
    _selection_checkbox = Gtk.Template.Child()
    _group_icon = Gtk.Template.Child()

    _safe_group = None

    title = GObject.Property(type=str, default="")

    def __init__(self, unlocked_database):
        super().__init__()

        self._signals = GObject.SignalGroup.new(SafeGroup)
        self._bindings = GObject.BindingGroup.new()

        self._signals.connect_closure(
            "notify::name",
            self._on_group_name_changed,
            False,
        )
        self._signals.connect_closure(
            "notify::selected",
            self._on_selected_notify,
            False,
        )
        self._bindings.bind(
            "selected",
            self._selection_checkbox,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )
        self._bindings.bind(
            "sensitive",
            self,
            "sensitive",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        self.unlocked_database = unlocked_database

        unlocked_database.connect(
            "notify::selection-mode",
            self._on_selection_mode_notify,
        )

    @GObject.Property(type=SafeGroup)
    def safe_group(self):
        return self._safe_group

    @safe_group.setter  # type: ignore
    def safe_group(self, element):
        if not isinstance(element, SafeGroup):
            msg = "Expected a SafeGroup."
            raise TypeError(msg)

        self._safe_group = element

        self._signals.props.target = element
        self._bindings.props.source = element

        self._on_group_name_changed(element, None)
        self._on_selection_mode_notify(self.unlocked_database, None)

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

        if db_view.props.selection_mode:
            selected = self._safe_group.selected  # type: ignore
            self._safe_group.selected = not selected  # type: ignore
        else:
            db_view.props.selection_mode = True
            self._safe_group.selected = True  # type: ignore

    def _on_selected_notify(self, group, _pspec):
        self.unlocked_database.start_database_lock_timer()

        if group.props.selected:
            self.unlocked_database.add_selection(group)
        else:
            self.unlocked_database.remove_selection(group)

    @Gtk.Template.Callback()
    def on_navigate_button_clicked(self, _button: Gtk.Button) -> None:
        """Edit the button in a GroupRow when clicked.

        button: The edit button in the GroupRow
        """
        self.unlocked_database.start_database_lock_timer()  # Reset the lock timer

        self.unlocked_database.show_browser_page(self._safe_group)

    def _on_group_name_changed(
        self,
        safe_group: SafeGroup,
        _value: GObject.ParamSpec,
    ) -> None:
        group_name = GLib.markup_escape_text(safe_group.name)
        if group_name:
            self.remove_css_class("italic-title")
            self.props.title = group_name
        else:
            self.add_css_class("italic-title")
            self.props.title = _("Title not Specified")

    def _on_selection_mode_notify(self, unlocked_db, _pspec):
        selection_mode = unlocked_db.props.selection_mode

        if selection_mode:
            visible_child = self._selection_checkbox
        else:
            visible_child = self._group_icon

        self._prefix_stack.props.visible_child = visible_child

    @Gtk.Template.Callback()
    def _on_long_press_gesture_pressed(self, _gesture, _x, _y):
        self.unlocked_database.props.selection_mode = True
        self._safe_group.props.selected = not self._safe_group.props.selected
