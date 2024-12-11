# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing

from gi.repository import Adw, Gio, GObject, Gtk

import gsecrets.config_manager as config
from gsecrets.entry_row import EntryRow
from gsecrets.group_row import GroupRow
from gsecrets.safe_element import SafeGroup
from gsecrets.single_selection import SingleSelection
from gsecrets.sorting import SortingHat

if typing.TYPE_CHECKING:
    from gsecrets.safe_element import SafeEntry


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/browsing_panel.ui")
class BrowsingPanel(Adw.Bin):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "BrowsingPanel"

    _empty_group_box = Gtk.Template.Child()
    _empty_search_page = Gtk.Template.Child()
    _list_view = Gtk.Template.Child()
    _scrolled_window = Gtk.Template.Child()
    _stack = Gtk.Template.Child()

    _query = ""

    def __init__(self, unlocked_database):
        super().__init__()

        self._signals = GObject.SignalGroup.new(SafeGroup)
        self._signals.connect_closure(
            "children-changed",
            self._on_children_changed,
            False,
        )

        sorting = config.get_sort_order()
        self.entry_sorter = SortingHat.get_sorter(sorting)
        self.group_sorter = SortingHat.get_sorter(sorting)

        dbm = unlocked_database.database_manager

        self.current_group = dbm.root
        self._signals.props.target = self.current_group

        self.entries = Gtk.SortListModel.new(dbm.entries, self.entry_sorter)
        self.groups = Gtk.SortListModel.new(dbm.groups, self.group_sorter)

        self.unlocked_database = unlocked_database

        flatten = Gio.ListStore.new(Gtk.SortListModel)
        flatten.splice(0, 0, [self.groups, self.entries])

        flatten_model = Gtk.FlattenListModel.new(flatten)

        self._filter = Gtk.CustomFilter.new(self._parent_filter_fn)
        self._search_filter = Gtk.CustomFilter.new(self._search_filter_fn)

        self._list_model = Gtk.FilterListModel.new(flatten_model, self._filter)

        self.selection_model = SingleSelection(self._list_model)

        settings = unlocked_database.window.application.settings
        settings.connect("changed::sort-order", self._on_sort_order_changed)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_setup)
        factory.connect("bind", self._on_bind)

        self._list_view.set_model(self.selection_model)
        self._list_view.set_factory(factory)
        self._list_model.connect("notify::n-items", self._on_model_n_items_changed)
        self._set_stack_page()

        unlocked_database.database_manager.connect(
            "sorting_changed",
            self._on_sorting_changed,
        )

        self._list_view.connect("activate", self._on_listview_activate)
        self.selection_model.connect("notify::selected-item", self._on_selected_item)

    def _on_selected_item(self, model, _pspec):
        if element := model.props.selected_item:
            self.unlocked_database.show_edit_page(element)
        else:
            current = self.unlocked_database.current_element
            self.unlocked_database.show_browser_page(current.parentgroup)

    def visit_group(self, group):
        self.current_group = group
        self._signals.props.target = group
        self.unlocked_database.props.search_active = False
        self._filter.changed(Gtk.FilterChange.DIFFERENT)

    def set_search(self, query: str | None) -> None:
        if self._query == query:
            return

        if query is None:
            self._list_model.props.filter = self._filter
            self._set_stack_page()
            self._query = ""
            return

        self._list_model.props.filter = self._search_filter

        if query in self._query:
            change = Gtk.FilterChange.LESS_STRICT
        elif self._query in query:
            change = Gtk.FilterChange.MORE_STRICT
        else:
            change = Gtk.FilterChange.DIFFERENT

        self._query = query.lower()
        self._search_filter.changed(change)

    def hide_selection(self, hide):
        self.selection_model.props.hide_selected = hide

    def _on_listview_activate(self, _list_view, pos):
        element = self._list_model.get_item(pos)

        if element.is_group:
            self.unlocked_database.show_browser_page(element)
        elif self.unlocked_database.props.selection_mode:
            element.props.selected = not element.props.selected
        else:
            self.selection_model.props.selected_item = element
            self.unlocked_database.show_edit_page(element)

    def _on_setup(self, _list_view, item):
        entry_row = EntryRow(self.unlocked_database)

        item.props.child = entry_row

    def _on_bind(self, _list_view, item):
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

    def _on_sorting_changed(self, _db_manager, is_entry):
        if is_entry:
            self.entry_sorter.changed(Gtk.SorterChange.DIFFERENT)
        else:
            self.group_sorter.changed(Gtk.SorterChange.DIFFERENT)

    def _on_sort_order_changed(self, settings, _key):
        """Callback to be executed when the sorting has been changed."""
        sorting = settings.get_enum("sort-order")
        logging.debug("Sort order changed to %s", sorting)

        sorting = config.get_sort_order()
        self.entry_sorter = SortingHat.get_sorter(sorting)
        self.group_sorter = SortingHat.get_sorter(sorting)

        self.entries.set_sorter(self.entry_sorter)
        self.groups.set_sorter(self.group_sorter)

    def _set_stack_page(self):
        if not self._list_model.get_n_items():
            if self.unlocked_database.props.search_active:
                self._stack.props.visible_child = self._empty_search_page
            else:
                self._stack.props.visible_child = self._empty_group_box
        else:
            self._stack.props.visible_child = self._scrolled_window

    def _on_model_n_items_changed(self, _model, _pspec):
        self._set_stack_page()

    def _on_children_changed(self, _group, removed, added):
        if added > 0 and removed == 0:
            change = Gtk.FilterChange.LESS_STRICT
        elif removed > 0 and added == 0:
            change = Gtk.FilterChange.MORE_STRICT
        else:
            change = Gtk.FilterChange.DIFFERENT

        self._filter.changed(change)

    def _parent_filter_fn(self, item):
        if item.is_root_group:
            return False

        return item.parentgroup == self.current_group

    def _search_filter_fn(self, item: SafeEntry | SafeGroup) -> bool:
        if item.is_root_group:
            return False

        if not item.is_group and item.tags:
            for tag in item.tags:
                if self._query in tag.lower():
                    return True

        if isinstance(item, SafeGroup):
            fields = [item.name, item.notes]
        else:
            fields = [item.name, item.notes, item.url, item.username]

        for field in fields:
            if not field:  # type: ignore
                continue

            if self._query in field.lower():  # type: ignore
                return True

        return False

    def unselect(self, item):
        if item == self.selection_model.props.selected_item:
            self.selection_model.props.selected_item = None
