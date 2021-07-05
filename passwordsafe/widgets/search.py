# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import threading
import typing

from gi.repository import Adw, Gio, GLib, GObject, Gtk

import passwordsafe.config_manager as config
from passwordsafe.safe_element import SafeElement, SafeEntry, SafeGroup
from passwordsafe.sorting import SortingHat

if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/search.ui")
class Search(Gtk.Stack):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "Search"

    _result_list = Gio.ListStore.new(SafeElement)

    _empty_search_page = Gtk.Template.Child()
    _info_search_page = Gtk.Template.Child()
    _results_search_page = Gtk.Template.Child()
    search_list_box = Gtk.Template.Child()

    def __init__(self, unlocked_database: UnlockedDatabase) -> None:
        super().__init__()

        self.unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager
        self._search_changed_id: int | None = None

        self._headerbar = self.unlocked_database.search_headerbar
        self._search_entry = self._headerbar.search_entry

        self._search_text: str = self._search_entry.props.text
        self._result_list.connect("items_changed", self._on_items_changed)

        self._search_entry.set_key_capture_widget(self.unlocked_database.window)

    def _on_items_changed(
        self, list_model: Gio.ListModel, _pos: int, _removed: int, _added: int
    ) -> None:
        if list_model.get_n_items() == 0:
            if len(self._search_text) < 2:
                self.set_visible_child(self._info_search_page)

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

        else:
            if self._search_changed_id is not None:
                self._search_entry.disconnect(self._search_changed_id)
                self._search_changed_id = None

            self._search_entry.props.text = ""
            self._result_list.remove_all()

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
            search_thread.daemon = True
            search_thread.start()
        else:
            self.set_visible_child(self._info_search_page)

    def _perform_search(self):
        """Search for results in the database."""
        query = self._search_text

        db_manager = self.unlocked_database.database_manager

        def filter_func(element: SafeElement) -> bool:
            if element.is_group:
                fields = [element.name, element.notes]
            else:
                fields = [element.name, element.notes, element.url, element.username]

            for field in fields:
                if query.lower() in field.lower():
                    return True

            return False

        db_entries = filter(
            filter_func, [SafeEntry(db_manager, e) for e in db_manager.db.entries]
        )
        db_groups = filter(
            filter_func,
            [
                SafeGroup(db_manager, g)
                for g in db_manager.db.groups
                if not g.is_root_group
            ],
        )
        results = list(db_groups) + list(db_entries)

        if len(results) == 0:
            self.set_visible_child(self._empty_search_page)
            return

        GLib.idle_add(self._show_results, results)

    def _show_results(self, results):
        n_items = self._result_list.get_n_items()
        self._result_list.splice(0, n_items, results)

        # Sort the results
        sorting = config.get_sort_order()
        sort_func = SortingHat.get_sort_func(sorting)
        self._result_list.sort(sort_func)

        self.set_visible_child(self._results_search_page)

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

    @property
    def headerbar(self) -> Adw.HeaderBar:
        """Get the search headerbar.

        :returns: the search headerbar
        :rtype: Adw.Headerbar
        """
        return self._headerbar
