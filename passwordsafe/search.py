# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import threading
import typing

from typing import List
from uuid import UUID
from gi.repository import Gdk, GLib, GObject, Gtk, Handy

from passwordsafe.entry_row import EntryRow
from passwordsafe.group_row import GroupRow
from passwordsafe.scrolled_page import ScrolledPage

if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.unlocked_database import UnlockedDatabase


class Search:
    # pylint: disable=too-many-instance-attributes

    #
    # Global Variables
    #

    search_list_box = NotImplemented
    #
    # Init
    #

    def __init__(self, unlocked_database: UnlockedDatabase) -> None:
        self.unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager
        self._search_event_connection_id: int = 0
        self._search_changed_id: int = 0

        self._builder: Gtk.Builder = Gtk.Builder()
        self._builder.add_from_resource("/org/gnome/PasswordSafe/search.ui")

        self._overlay: Gtk.Overlay = self._builder.get_object("overlay")
        self._empty_search_box: Gtk.Box = self._builder.get_object(
            "empty_search_box")
        self._info_search_box: Gtk.Box = self._builder.get_object(
            "info_search_box")

        self.scrolled_page: ScrolledPage = ScrolledPage(False)

        self._search_entry = self._builder.get_object("headerbar_search_entry")
        self._headerbar: Handy.HeaderBar = self._builder.get_object(
            "headerbar_search")

        self._key_pressed: bool = False
        self._timeout_search: int = 0

        self._timeout_info: int = 0
        self._result_list: List[UUID] = []
        self._search_text: str = self._search_entry.props.text
        self._current_result_idx: int = 0

    def initialize(self):
        # Search Headerbar
        headerbar_close_button = self._builder.get_object("headerbar_close_button")
        headerbar_close_button.connect("clicked", self.on_headerbar_search_close_button_clicked)

        self._search_entry.connect("activate", self.on_headerbar_search_entry_enter_pressed)
        self._search_entry.connect("stop-search", self.on_headerbar_search_entry_focused)

        self.unlocked_database.bind_accelerator(
            self._search_entry, "<Control>f", signal="stop-search")
        self.unlocked_database.connect(
            "notify::search-active", self._on_search_active)
        self._prepare_search_page()
    #
    # Search
    #

    # Search headerbar
    def _on_search_active(
            self, db_view: UnlockedDatabase,
            value: GObject.ParamSpecBoolean) -> None:
        """Update the view when the search view is activated or
        deactivated.

        :param UnlockedDatabase db_view: unlocked_database view
        :param GObject.ParamSpecBoolean value: new value as GParamSpec
        """
        # pylint: disable=unused-argument
        search_active = self.unlocked_database.props.search_active

        if search_active:
            self._search_changed_id = self._search_entry.connect(
                "search-changed", self._on_search_entry_timeout)
            self._search_entry.grab_focus()

            if self.search_list_box is not NotImplemented:
                self.search_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
                self._search_event_connection_id = self._search_entry.connect(
                    "key-release-event", self.on_search_entry_navigation)

            self._timeout_info = GLib.timeout_add(
                200, self._display_info_overlay)

        else:
            self._clear_view()
            self.search_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
            self._search_entry.disconnect(self._search_event_connection_id)
            self._search_event_connection_id = 0

            self._search_entry.disconnect(self._search_changed_id)
            self._search_changed_id = 0
            self._search_entry.props.text = ""
            self._key_pressed = False

    #
    # Stack
    #

    # Set Search stack page
    def _prepare_search_page(self):
        self.search_list_box = self._builder.get_object("list_box")
        self.search_list_box.connect("row-activated", self.unlocked_database.on_list_box_row_activated)

        self.scrolled_page.add(self._overlay)
        self.scrolled_page.show_all()
        self.unlocked_database.add_page(self.scrolled_page, "search")

    def _display_info_overlay(self) -> bool:
        """When search-mode is activated the search text has not been
        entered yet. The info_search overlay only needs to be displayed
        if the search text is empty."""
        if self._timeout_info > 0:
            GLib.source_remove(self._timeout_info)
            self._timeout_info = 0

        if not self._key_pressed:
            self._info_search_box.show()

        return GLib.SOURCE_REMOVE

    #
    # Utils
    #

    def _clear_view(self) -> None:
        """Clear the view when the search mode is activated
        or when a new search is performed.

        All the overlay are removed and the results list is cleared.
        """
        for row in self.search_list_box:
            self.search_list_box.remove(row)

        self.search_list_box.hide()
        self._info_search_box.hide()
        self._empty_search_box.hide()

        self._result_list.clear()

    def _start_search(self):
        """Update the overlays and start a search
        if the search term is not empty.
        """
        if self._search_text:
            search_thread = threading.Thread(target=self._perform_search)
            search_thread.daemon = True
            search_thread.start()
        else:
            self._info_search_box.show()

    def _perform_search(self):
        """Search for results in the database."""
        path = self.unlocked_database.current_element.path
        self._result_list = self._db_manager.search(self._search_text, path)

        if not self._result_list:
            self._empty_search_box.show()
            return

        self._current_result_idx = 0
        GLib.idle_add(self._show_results)

    def _show_results(self, load_all=False):
        """Display some results.

        :param bool load_all: True if all the results need to be shown
        """
        self.search_list_box.show()
        window_height = self.unlocked_database.parent_widget.get_allocation().height - 120
        group_row_height = 50
        entry_row_height = 65
        search_height: int = 0
        skipped_rows: bool = False

        new_idx: int = 0
        for uuid in self._result_list[self._current_result_idx:]:
            if search_height < window_height or load_all:
                if self._db_manager.check_is_group(uuid):
                    search_height += group_row_height
                    row = GroupRow(
                        self.unlocked_database, self._db_manager,
                        self._db_manager.get_group(uuid))
                else:
                    search_height += entry_row_height
                    row = EntryRow(
                        self.unlocked_database,
                        self._db_manager.get_entry_object_from_uuid(uuid))

                self.search_list_box.add(row)
                new_idx += 1
            else:
                skipped_rows = True
                break

        self._current_result_idx += new_idx

        if skipped_rows:
            load_more_row = self._builder.get_object("load_more_row")
            self.search_list_box.add(load_more_row)
            search_height += 40

        # FIXME: It should not be necessary to set the height of the list
        # and a check_resize on the scrolled_page. Without this, the
        # result list is not always correctly displayed.
        # The 38 = 18 + 18 + 2 number comes from the margins and the border of
        # the list.
        # It has to be adjusted for mobile view when there are no margins.
        if self.unlocked_database.window.mobile_width:
            margin = 2
        else:
            margin = 38

        self.search_list_box.props.height_request = search_height + margin
        self.scrolled_page.check_resize()
        return GLib.SOURCE_REMOVE

    #
    # Events
    #

    def on_headerbar_search_close_button_clicked(self, _widget):
        self.unlocked_database.start_database_lock_timer()
        self.unlocked_database.props.search_active = False

    def on_search_entry_navigation(self, _widget, event, _data=None):
        self.unlocked_database.start_database_lock_timer()

        nr_rows = len(self.search_list_box)
        if nr_rows == 0:
            return

        selected_row = self.search_list_box.get_selected_row()
        if selected_row:
            idx = selected_row.get_index()
        else:
            idx = -1

        if (event.keyval == Gdk.KEY_Up and idx >= 1):
            self.search_list_box.select_row(
                self.search_list_box.get_row_at_index(idx - 1))
        elif (event.keyval == Gdk.KEY_Down and idx < nr_rows - 1):
            self.search_list_box.select_row(
                self.search_list_box.get_row_at_index(idx + 1))

    def _on_search_entry_timeout(self, widget: Gtk.Entry) -> None:
        self._key_pressed = True
        if self._timeout_search > 0:
            GLib.source_remove(self._timeout_search)

        self._timeout_search = GLib.timeout_add(
            500, self._on_search_entry_changed, widget)

    def _on_search_entry_changed(self, widget):
        self._timeout_search = 0
        self._clear_view()

        self._search_text = widget.get_text()
        self._start_search()

        return False

    def on_headerbar_search_entry_enter_pressed(self, _widget):
        self.unlocked_database.start_database_lock_timer()

        # Do nothing on empty search terms or no search results
        if not self._search_text:
            return
        if not self.search_list_box.get_children():
            return

        uuid = NotImplemented
        first_row = NotImplemented
        selected_row = self.search_list_box.get_selected_row()

        if selected_row is None:
            selected_row = self.search_list_box.get_children()[0]
        uuid = selected_row.get_uuid()
        if selected_row.type == "GroupRow":
            first_row = self._db_manager.get_group(uuid)
        else:
            first_row = self._db_manager.get_entry_object_from_uuid(uuid)

        self.unlocked_database.show_element(first_row)
        self.unlocked_database.props.search_active = False

    def on_load_more_row_clicked(self, row):
        self.search_list_box.remove(row)
        self._show_results(True)

    def on_headerbar_search_entry_focused(self, entry):
        if entry.has_focus() is True:
            return

        entry.grab_focus()

    @property
    def headerbar(self) -> Handy.HeaderBar:
        """Get the search headerbar.

        :returns: the search headerbar
        :rtype: Handy.Headerbar
        """
        return self._headerbar
