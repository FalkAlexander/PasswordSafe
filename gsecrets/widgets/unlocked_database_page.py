# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing

from gi.repository import Adw, Gio, GObject, Gtk

import gsecrets.config_manager as config
from gsecrets.entry_row import EntryRow
from gsecrets.group_row import GroupRow
from gsecrets.safe_element import SafeElement, SafeEntry
from gsecrets.sorting import SortingHat

if typing.TYPE_CHECKING:
    from uuid import UUID

    from gsecrets.database_manager import DatabaseManager
    from gsecrets.widgets.selection_mode_headerbar import SelectionModeHeaderbar


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlocked_database_page.ui")
class UnlockedDatabasePage(Adw.Bin):

    __gtype_name__ = "UnlockedDatabasePage"

    list_view = Gtk.Template.Child()
    empty_group_box = Gtk.Template.Child()
    scrolled_window = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    def __init__(self, unlocked_database, group):
        super().__init__()

        sorting = config.get_sort_order()
        sorter = SortingHat.get_sorter(sorting)

        self.entries = Gtk.SortListModel.new(group.entries, sorter)
        self.groups = Gtk.SortListModel.new(group.subgroups, sorter)

        self.unlocked_database = unlocked_database
        self.group = group

        flatten = Gio.ListStore.new(Gtk.SortListModel)
        flatten.splice(0, 0, [self.groups, self.entries])
        self.list_model = Gtk.FlattenListModel.new(flatten)

        self.selection_model = Gtk.NoSelection()
        self.selection_model.set_model(self.list_model)

        settings = unlocked_database.window.application.settings
        settings.connect("changed", self.on_sort_order_changed)

        unlocked_database.selection_mode_headerbar.connect(
            "clear-selection", self._on_clear_selection
        )
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.on_setup)
        factory.connect("bind", self.on_bind)

        self.list_view.set_model(self.selection_model)
        self.list_view.set_factory(factory)
        self.list_view.connect("activate", self.on_list_view_activate)
        self.list_model.connect(
            "items-changed",
            self.on_listbox_items_changed,
        )

    def on_setup(self, list_view, item):
        stack = Gtk.Stack()
        entry_row = EntryRow(self.unlocked_database)
        group_row = GroupRow(self.unlocked_database)

        stack.add_named(entry_row, "entry_row")
        stack.add_named(group_row, "group_row")

        item.props.child = stack

    def on_bind(self, list_view, item):
        element = item.props.item
        stack = item.props.child
        if element.is_group:
            stack.props.visible_child_name = "group_row"
            row = stack.props.visible_child
            row.props.safe_group = element
        else:
            stack.props.visible_child_name = "entry_row"
            row = stack.props.visible_child
            row.props.safe_entry = element

    def on_list_view_activate(self, _list_view, pos):
        element = self.list_model.get_item(pos)

        if element.is_entry:
            self.unlocked_database.show_edit_page(element)
            return

        self.unlocked_database.show_browser_page(element)

    def on_sort_order_changed(self, settings, key):
        """Callback to be executed when the sorting has been changed."""
        if key == "sort-order":
            sorting = settings.get_enum("sort-order")
            logging.debug("Sort order changed to %s", sorting)

            sorting = config.get_sort_order()
            sorter = SortingHat.get_sorter(sorting)

            self.entries.set_sorter(sorter)
            self.groups.set_sorter(sorter)

    def on_listbox_items_changed(
        self,
        listmodel,
        _position,
        _removed,
        _added,
    ):
        if not listmodel.get_n_items():
            self.stack.set_visible_child(self.empty_group_box)
        else:
            self.stack.set_visible_child(self.scrolled_window)

    def _on_clear_selection(self, _header: SelectionModeHeaderbar) -> None:
        for row in self.list_view:  # pylint: disable=not-an-iterable
            row.selection_checkbox.props.active = False
