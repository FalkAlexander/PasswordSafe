# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing

from gi.repository import Adw, Gio, GObject, Gtk

import passwordsafe.config_manager as config
from passwordsafe.safe_element import SafeElement
from passwordsafe.sorting import SortingHat

if typing.TYPE_CHECKING:
    from uuid import UUID

    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.widgets.selection_mode_headerbar import SelectionModeHeaderbar


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/unlocked_database_page.ui")
class UnlockedDatabasePage(Adw.Bin):

    __gtype_name__ = "UnlockedDatabasePage"

    clamp = Gtk.Template.Child()
    list_box = Gtk.Template.Child()
    empty_group_box = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    def __init__(self, unlocked_database, group):
        super().__init__()

        self.list_model = Gio.ListStore.new(SafeElement)
        self.unlocked_database = unlocked_database
        self.group = group

        settings = unlocked_database.window.application.settings
        settings.connect("changed", self.on_sort_order_changed)

        unlocked_database.database_manager.connect(
            "element-removed", self._on_element_removed
        )
        unlocked_database.database_manager.connect(
            "element-added", self._on_element_added
        )
        unlocked_database.database_manager.connect(
            "element-moved", self._on_element_moved
        )
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
        self.populate_list_model()

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
            sort_func = SortingHat.get_sort_func(sorting)

            self.list_model.sort(sort_func)

    def _on_element_removed(
        self,
        _db_manager: DatabaseManager,
        element_uuid: UUID,
    ) -> None:
        pos = 0
        found = False
        for element in self.list_model:
            if element.uuid == element_uuid:
                found = True
                break
            pos += 1

        # Only removes the element if it is the current list model
        if found:
            self.list_model.remove(pos)

    def _on_element_added(
        self,
        _db_manager: DatabaseManager,
        element: SafeElement,
        target_group_uuid: UUID,
    ) -> None:
        # Return if the element was added to another group than the one
        # used to generate the list model.
        list_model_group_uuid = self.group.uuid
        if target_group_uuid != list_model_group_uuid:
            return

        sorting = config.get_sort_order()
        sort_func = SortingHat.get_sort_func(sorting)
        self.list_model.insert_sorted(element, sort_func)
        element.sorted_handler_id = element.connect(
            "notify::name", self._on_element_renamed
        )

    def _on_element_renamed(
        self,
        element: SafeElement,
        _value: GObject.ParamSpec,
    ) -> None:
        pos = 0
        found = False
        # Disconnect previous signal
        if element.sorted_handler_id:
            element.disconnect(element.sorted_handler_id)
            element.sorted_handler_id = None

        # We check if element is in the list model
        for elem in self.list_model:
            if elem == element:
                found = True
                break
            pos += 1

        if found:
            sorting = config.get_sort_order()
            sort_func = SortingHat.get_sort_func(sorting)

            self.list_model.remove(pos)
            self.list_model.insert_sorted(element, sort_func)
            element.sorted_handler_id = element.connect(
                "notify::name", self._on_element_renamed
            )
        else:
            logging.debug("No.")

    def _on_element_moved(
        self,
        _db_manager: DatabaseManager,
        moved_element: SafeElement,
        old_loc_uuid: UUID,
        new_loc_uuid: UUID,
    ) -> None:
        # pylint: disable=too-many-arguments
        """Moves the element to a new list model.
        If the listmodel corresponds to the old group we remove it,
        and if corresponds to the new location, we add it."""
        list_model_group_uuid = self.group.uuid
        if list_model_group_uuid == old_loc_uuid:
            pos = 0
            found = False
            for element in self.list_model:
                if element == moved_element:
                    found = True
                    break
                pos += 1

            if found:
                self.list_model.remove(pos)

        if list_model_group_uuid == new_loc_uuid:
            sorting = config.get_sort_order()
            sort_func = SortingHat.get_sort_func(sorting)
            self.list_model.insert_sorted(moved_element, sort_func)
            moved_element.sorted_handler_id = moved_element.connect(
                "notify::name", self._on_element_renamed
            )

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
            self.stack.set_visible_child(self.clamp)

    def populate_list_model(self) -> None:
        entries = self.group.entries
        groups = [g for g in self.group.subgroups if not g.is_root_group]

        elements = groups + entries
        self.list_model.splice(0, 0, elements)
        for elem in self.list_model:
            elem.sorted_handler_id = elem.connect(
                "notify::name", self._on_element_renamed
            )

        self.sort_list_model()

    def sort_list_model(self) -> None:
        sorting = config.get_sort_order()
        sort_func = SortingHat.get_sort_func(sorting)

        self.list_model.sort(sort_func)

    def _on_clear_selection(self, _header: SelectionModeHeaderbar) -> None:
        for row in self.list_box:  # pylint: disable=not-an-iterable
            row.selection_checkbox.props.active = False
