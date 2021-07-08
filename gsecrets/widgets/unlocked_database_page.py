# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing

from gi.repository import Adw, Gio, Gtk

import gsecrets.config_manager as config
from gsecrets.entry_row import EntryRow
from gsecrets.group_row import GroupRow
from gsecrets.safe_element import SafeElement, SafeEntry
from gsecrets.sorting import SortingHat

if typing.TYPE_CHECKING:
    from gsecrets.widgets.selection_mode_headerbar import SelectionModeHeaderbar


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlocked_database_page.ui")
class UnlockedDatabasePage(Adw.Bin):

    __gtype_name__ = "UnlockedDatabasePage"

    empty_group_box = Gtk.Template.Child()
    list_view = Gtk.Template.Child()
    scrolled_window = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    def __init__(self, unlocked_database, group):
        super().__init__()

        sorting = config.get_sort_order()
        self.entry_sorter = SortingHat.get_sorter(sorting)
        self.group_sorter = SortingHat.get_sorter(sorting)

        self.entries = Gtk.SortListModel.new(group.entries, self.entry_sorter)
        self.groups = Gtk.SortListModel.new(group.subgroups, self.group_sorter)

        self.unlocked_database = unlocked_database
        self.group = group

        flatten = Gio.ListStore.new(Gtk.SortListModel)
        flatten.splice(0, 0, [self.groups, self.entries])
        self.list_model = Gtk.FlattenListModel.new(flatten)
        self.selection_model = Gtk.NoSelection.new(self.list_model)

        settings = unlocked_database.window.application.settings
        settings.connect("changed::sort-order", self.on_sort_order_changed)

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
            "notify::n-items",
            self.on_listbox_n_items_changed,
        )
        if not self.list_model.get_item(0):
            self.stack.set_visible_child(self.empty_group_box)

        unlocked_database.database_manager.connect(
            "sorting_changed", self._on_sorting_changed
        )

    def on_setup(self, _list_view, item):
        entry_row = EntryRow(self.unlocked_database)

        item.props.child = entry_row

    def on_bind(self, _list_view, item):
        element = item.props.item
        row = item.props.child
        if element.is_group:
            if row.__gtype_name__ != "GroupRow":
                row = GroupRow(self.unlocked_database)
                item.props.child = row

            row.props.safe_group = element
        else:
            if row.__gtype_name__ != "EntryRow":
                row = EntryRow(self.unlocked_database)
                item.props.child = row

            row.props.safe_entry = element

    def on_list_view_activate(self, _list_view, pos):
        element = self.list_model.get_item(pos)

        if isinstance(element, SafeEntry):
            self.unlocked_database.show_edit_page(element)
            return

        self.unlocked_database.show_browser_page(element)

    def do_grab_focus(self):  # pylint: disable=arguments-differ
        if child := self.list_box.get_first_child():
            return child.grab_focus()

        return Gtk.Widget.do_grab_focus(self)

    def _on_sorting_changed(self, _db_manager, is_entry):
        if is_entry:
            self.entry_sorter.changed(Gtk.SorterChange.DIFFERENT)
        else:
            self.group_sorter.changed(Gtk.SorterChange.DIFFERENT)

    def on_sort_order_changed(self, settings, _key):
        """Callback to be executed when the sorting has been changed."""
        sorting = settings.get_enum("sort-order")
        logging.debug("Sort order changed to %s", sorting)

        sorting = config.get_sort_order()
        self.entry_sorter = SortingHat.get_sorter(sorting)
        self.group_sorter = SortingHat.get_sorter(sorting)

        self.entries.set_sorter(self.entry_sorter)
        self.groups.set_sorter(self.group_sorter)

    def on_listbox_n_items_changed(self, listmodel, _pspec,):
        if not listmodel.get_n_items():
            self.stack.set_visible_child(self.empty_group_box)
        else:
            self.stack.set_visible_child(self.scrolled_window)

    def _on_clear_selection(self, _header: SelectionModeHeaderbar) -> None:
        for row in self.list_view:  # pylint: disable=not-an-iterable
            row.selection_checkbox.props.active = False
