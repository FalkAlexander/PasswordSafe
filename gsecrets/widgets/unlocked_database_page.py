# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing

from gi.repository import Adw, Gio, Gtk

import gsecrets.config_manager as config
from gsecrets.sorting import SortingHat

if typing.TYPE_CHECKING:
    from gsecrets.widgets.selection_mode_headerbar import SelectionModeHeaderbar


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlocked_database_page.ui")
class UnlockedDatabasePage(Adw.Bin):

    __gtype_name__ = "UnlockedDatabasePage"

    empty_group_box = Gtk.Template.Child()
    list_box = Gtk.Template.Child()
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

        settings = unlocked_database.window.application.settings
        settings.connect("changed", self.on_sort_order_changed)

        unlocked_database.selection_mode_headerbar.connect(
            "clear-selection", self._on_clear_selection
        )
        self.list_box.bind_model(self.list_model, unlocked_database.listbox_row_factory)
        self.list_box.connect(
            "row-activated", unlocked_database.on_list_box_row_activated
        )
        self.list_model.connect(
            "items-changed",
            self.on_listbox_items_changed,
        )
        if not self.list_model.get_item(0):
            self.stack.set_visible_child(self.empty_group_box)

    def do_map(self):  # pylint: disable=arguments-differ
        # FIXME This is a hacky way of having the focus on
        # the listbox.
        Gtk.Widget.do_map(self)
        child = self.list_box.get_first_child()
        if child:
            child.grab_focus()

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
        for row in self.list_box:  # pylint: disable=not-an-iterable
            row.selection_checkbox.props.active = False
