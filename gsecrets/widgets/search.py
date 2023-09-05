# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import threading
import typing

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from pykeepass.group import Group

from gsecrets.safe_element import SafeEntry, SafeGroup
from gsecrets.sorting import SortingHat

if typing.TYPE_CHECKING:
    import uuid

    from gsecrets.database_manager import DatabaseManager
    from gsecrets.unlocked_database import UnlockedDatabase

    from pykeepass.entry import Entry


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/search.ui")
class Search(Adw.Bin):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "Search"

    _empty_search_page = Gtk.Template.Child()
    _info_search_page = Gtk.Template.Child()
    _results_search_page = Gtk.Template.Child()
    search_list_box = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    def __init__(self, unlocked_database: UnlockedDatabase) -> None:
        super().__init__()

        self.unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager
        self._search_changed_id: int | None = None

        self._search_entry = self.unlocked_database.search_entry

        self._search_text: str = self._search_entry.props.text

        self.results_entries_filter = Gtk.FilterListModel.new(
            self._db_manager.entries, None
        )
        self.results_groups_filter = Gtk.FilterListModel.new(
            self._db_manager.groups, None
        )

        # Parameters of the previous search query
        self.query: str = ""
        self.db_groups: list[uuid.UUID] = []
        self.db_entries: list[uuid.UUID] = []

        def entry_filter(element: SafeEntry) -> bool:
            return element.uuid in self.db_entries

        def group_filter(element: SafeGroup) -> bool:
            return element.uuid in self.db_groups

        self.entry_filter = Gtk.CustomFilter.new(entry_filter)
        self.group_filter = Gtk.CustomFilter.new(group_filter)

        # Sort the results
        sorting = SortingHat.SortOrder.ASC
        sorter = SortingHat.get_sorter(sorting)

        self._results_entries = Gtk.SortListModel.new(
            self.results_entries_filter, sorter
        )
        self._results_groups = Gtk.SortListModel.new(
            self.results_groups_filter, sorter
        )

        flatten = Gio.ListStore.new(Gtk.SortListModel)
        flatten.splice(0, 0, [self._results_groups, self._results_entries])

        self._result_list = Gtk.FlattenListModel.new(flatten)

    def initialize(self):
        # Search Headerbar
        self._search_entry.connect(
            "activate", self.on_headerbar_search_entry_enter_pressed
        )

        self.unlocked_database.connect("notify::search-active", self._on_search_active)
        self._search_entry.connect("search-started", self._on_search_started)

        self._prepare_search_page()

    def _on_search_started(self, search_entry: Gtk.SearchEntry) -> None:
        unlocked_database = self.unlocked_database
        if (
            unlocked_database.props.mode == unlocked_database.Mode.GROUP
            and not self.unlocked_database.database_manager.props.locked
        ):
            unlocked_database.props.search_active = True
        else:
            search_entry.props.text = ""

    # Search headerbar
    def _on_search_active(
        self, _db_view: UnlockedDatabase, _value: GObject.ParamSpecBoolean
    ) -> None:
        """Update the view when the search view is activated or
        deactivated.

        :param UnlockedDatabase db_view: unlocked_database view
        :param GObject.ParamSpecBoolean value: new value as GParamSpec
        """
        search_active = self.unlocked_database.props.search_active

        if search_active:
            self._search_changed_id = self._search_entry.connect(
                "search-changed", self._on_search_changed
            )
            self._search_entry.grab_focus()
            self.results_entries_filter.set_filter(self.entry_filter)
            self.results_groups_filter.set_filter(self.group_filter)

        else:
            if self._search_changed_id is not None:
                self._search_entry.disconnect(self._search_changed_id)
                self._search_changed_id = None

            self._search_entry.props.text = ""
            self.results_entries_filter.set_filter(None)
            self.results_groups_filter.set_filter(None)
            self.stack.set_visible_child(self._info_search_page)

    def _prepare_search_page(self):
        self.search_list_box.bind_model(
            self._result_list, self.unlocked_database.listbox_row_factory
        )
        self.search_list_box.connect(
            "row-activated", self.unlocked_database.on_list_box_row_activated
        )

    def _start_search(self):
        """Update the overlays and start a search
        if the search term is not empty.
        """
        if self._search_text:
            search_thread = threading.Thread(target=self._perform_search)
            search_thread.start()
        else:
            self.stack.set_visible_child(self._info_search_page)

    def _perform_search(self):
        """Search for results in the database."""
        query = self._search_text

        db_manager = self.unlocked_database.database_manager

        def filter_func(element: Entry | Group) -> bool:
            if isinstance(element, Group):
                fields = [element.name, element.notes]
            else:
                fields = [element.title, element.notes, element.url, element.username]

            for field in fields:
                if not field:
                    continue

                if query.lower() in field.lower():
                    return True

            return False

        db_entries = [e.uuid for e in filter(filter_func, db_manager.db.entries)]
        db_groups = [
            g.uuid
            for g in filter(filter_func, db_manager.db.groups)
            if not g.is_root_group
        ]

        if query in self.query:
            change = Gtk.FilterChange.LESS_STRICT
        if self.query and self.query in query:
            change = Gtk.FilterChange.MORE_STRICT
        else:
            change = Gtk.FilterChange.DIFFERENT

        self.db_groups = db_groups
        self.db_entries = db_entries
        self.query = query

        GLib.idle_add(self._show_results, db_groups, db_entries, change)

    def _show_results(self, db_groups, db_entries, change):
        if not db_groups and not db_entries:
            if len(self._search_text) < 2:
                self.stack.set_visible_child(self._info_search_page)
            else:
                self.stack.set_visible_child(self._empty_search_page)

            return GLib.SOURCE_REMOVE

        self.entry_filter.changed(change)
        self.group_filter.changed(change)

        self.stack.set_visible_child(self._results_search_page)

        return GLib.SOURCE_REMOVE

    # Events

    def _on_search_changed(self, search_entry):
        self.unlocked_database.start_database_lock_timer()
        self._search_text = search_entry.props.text
        self._start_search()

    def on_headerbar_search_entry_enter_pressed(self, _widget):
        self.unlocked_database.start_database_lock_timer()

        # Do nothing on empty search terms or no search results
        if not self._search_text:
            return
        if not self.search_list_box.get_first_child():
            return

        first_row = self.search_list_box.get_first_child()
        focus = self.search_list_box.get_focus_child()
        if focus is None:
            first_row.emit("activate")
