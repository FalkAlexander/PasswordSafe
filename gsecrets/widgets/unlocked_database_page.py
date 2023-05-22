# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing

from gi.repository import Adw, Gio, GObject, Gtk

import gsecrets.config_manager as config
from gsecrets.entry_row import EntryRow
from gsecrets.group_row import GroupRow
from gsecrets.sorting import SortingHat
from gsecrets.selection import Selection
from gsecrets.safe_element import SafeGroup

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

        dbm = unlocked_database.database_manager
        root = SafeGroup.get_root(dbm)

        self.current_group = root

        self.entries = Gtk.SortListModel.new(dbm.entries, self.entry_sorter)
        self.groups = Gtk.SortListModel.new(dbm.groups, self.group_sorter)

        self.unlocked_database = unlocked_database
        self.group = group

        flatten = Gio.ListStore.new(Gtk.SortListModel)
        flatten.splice(0, 0, [self.groups, self.entries])

        flatten_model = Gtk.FlattenListModel.new(flatten)

        def filter_fn(item):
            return item.parentgroup == self.current_group and not item.is_root_group

        self.filter_ = Gtk.CustomFilter.new(filter_fn)

        self.list_model = Gtk.FilterListModel.new(flatten_model, self.filter_)

        self.selection_model = Selection(self.list_model, unlocked_database)
        self.selection_model.connect("notify::selected-item", self.on_selected_item_changed)

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
        self.list_model.connect(
            "notify::n-items",
            self.on_listbox_n_items_changed,
        )
        if self.list_model.get_item(0) is None:
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

    def on_selected_item_changed(self, selection_model, _pspec):
        element = selection_model.props.selected_item
        database = self.unlocked_database

        if database.props.search_active:
            database.props.search_active = False

        if element.is_group:
            self.unlocked_database.show_edit_page(element)
            return

        if database.props.selection_mode:
            element.props.selected = not element.props.selected
            return

        self.unlocked_database.show_edit_page(element)

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
        for element in self.list_model:
            element.props.selected = False

    def visit_group(self, group):
        self.current_group = group
        self.filter_.changed(Gtk.FilterChange.DIFFERENT)
