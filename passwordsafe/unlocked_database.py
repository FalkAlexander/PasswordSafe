# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import ntpath
import os
import re
import threading
import time
import typing
from gettext import gettext as _
from threading import Timer
from typing import List, Optional, Union
from uuid import UUID

from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Handy

import passwordsafe.config_manager
from passwordsafe.custom_keypress_handler import CustomKeypressHandler
from passwordsafe.database_settings_dialog import DatabaseSettingsDialog
from passwordsafe.entry_page import EntryPage
from passwordsafe.entry_row import EntryRow
from passwordsafe.group_page import GroupPage
from passwordsafe.group_row import GroupRow
from passwordsafe.pathbar import Pathbar
from passwordsafe.properties_dialog import PropertiesDialog
from passwordsafe.references_dialog import ReferencesDialog
from passwordsafe.responsive_ui import ResponsiveUI
from passwordsafe.scrolled_page import ScrolledPage
from passwordsafe.search import Search
from passwordsafe.selection_ui import SelectionUI

if typing.TYPE_CHECKING:
    from pykeepass.entry import Entry
    from pykeepass.group import Group


class UnlockedDatabase(GObject.GObject):
    # Instances
    window = NotImplemented
    database_manager = NotImplemented
    responsive_ui = NotImplemented
    selection_ui = NotImplemented
    search = NotImplemented
    entry_page = NotImplemented
    group_page = NotImplemented
    custom_keypress_handler = NotImplemented

    # Widgets
    parent_widget = NotImplemented
    headerbar = NotImplemented
    headerbar_search = NotImplemented
    headerbar_box = NotImplemented
    scrolled_window = NotImplemented
    divider = NotImplemented
    revealer = NotImplemented
    action_bar = NotImplemented
    pathbar = NotImplemented
    overlay = NotImplemented
    search_overlay = NotImplemented
    database_settings_dialog = NotImplemented
    references_dialog = NotImplemented
    notes_dialog = NotImplemented

    # Objects
    builder = NotImplemented
    accelerators = NotImplemented
    scheduled_page_destroy: List[UUID] = []
    scheduled_tmpfiles_deletion: List[Gio.File] = []
    clipboard = NotImplemented
    list_box_sorting = NotImplemented
    clipboard_timer = NotImplemented
    database_lock_timer = NotImplemented
    save_loop = NotImplemented
    dbus_subscription_id = NotImplemented
    listbox_insert_thread = NotImplemented

    selection_mode = GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, window, widget, dbm):
        super().__init__()

        # Instances
        self.window = window
        self.parent_widget = widget
        self.database_manager = dbm
        self.responsive_ui = ResponsiveUI(self)
        self.selection_ui = SelectionUI(self)
        self.search = Search(self)
        self.entry_page = EntryPage(self)
        self.group_page = GroupPage(self)
        self.custom_keypress_handler = CustomKeypressHandler(self)

        self._current_element: Optional[Union[Entry, Group]] = None

        self._selection_button_box: Optional[Gtk.Box] = None

        # Declare database as opened
        self.window.opened_databases.append(self)

        self._search_active = False

        # Browser Mode
        self.assemble_listbox()
        self.start_save_loop()
        self.custom_keypress_handler.register_custom_events()
        self.register_dbus_signal()

        # Responsive UI
        self.responsive_ui.headerbar_title()
        self.responsive_ui.headerbar_back_button()
        self.responsive_ui.headerbar_selection_button()

        self.database_manager.connect(
            "notify::locked", self._on_database_lock_changed)

    #
    # Stack Pages
    #

    def assemble_listbox(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/unlocked_database.ui")

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        self.accelerators = Gtk.AccelGroup()
        self.window.add_accel_group(self.accelerators)

        self.overlay = Gtk.Overlay()
        self.parent_widget.add(self.overlay)

        database_action_overlay = self.builder.get_object("database_action_overlay")
        self.overlay.add_overlay(database_action_overlay)

        self.current_element = self.database_manager.get_root_group()

        self._stack = self.builder.get_object("list_stack")
        # contains the "main page" with the stack and the revealer inside
        self.divider = self.builder.get_object("divider")
        self.revealer = self.builder.get_object("revealer")
        self.headerbar_box = self.builder.get_object("headerbar_box")
        self.action_bar = self.builder.get_object("action_bar")
        self.overlay.add(self.divider)
        self.overlay.show_all()

        self.set_headerbar()

        self.list_box_sorting = passwordsafe.config_manager.get_sort_order()
        self.start_database_lock_timer()

        self.show_page_of_new_directory(False, False)

    #
    # Headerbar
    #

    # Assemble headerbar
    def set_headerbar(self):
        self.headerbar = self.builder.get_object("headerbar")

        save_button = self.builder.get_object("save_button")
        save_button.connect("clicked", self.on_save_button_clicked)

        lock_button = self.builder.get_object("lock_button")
        lock_button.connect("clicked", self.on_lock_button_clicked)

        mod_box = self.builder.get_object("mod_box")
        browser_buttons_box = self.builder.get_object("browser_buttons_box")
        mod_box.add(browser_buttons_box)

        search_button = self.builder.get_object("search_button")
        search_button.connect("clicked", self._on_search_button_clicked)
        self.bind_accelerator(self.accelerators, search_button, "<Control>f")

        selection_button = self.builder.get_object("selection_button")
        selection_button.connect("clicked", self._on_selection_button_clicked)
        selection_button_mobile = self.builder.get_object("selection_button_mobile")
        selection_button_mobile.connect(
            "clicked", self._on_selection_button_clicked)

        back_button_mobile = self.builder.get_object("back_button_mobile")
        back_button_mobile.connect("clicked", self.on_back_button_mobile_clicked)

        # Search UI
        self.search.initialize()

        # Selection UI
        self.selection_ui.initialize()

        self._selection_button_box = self.builder.get_object(
            "selection_button_box")
        self.bind_property(
            "selection-mode", self._selection_button_box, "visible",
            GObject.BindingFlags.SYNC_CREATE)

        self.parent_widget.set_headerbar(self.headerbar)
        self.window.set_titlebar(self.headerbar)
        self.pathbar = Pathbar(self, self.database_manager, self.database_manager.get_root_group())
        # Put pathbar in the right place (top or bottom)
        self.responsive_ui.action_bar()

    # Group and entry browser headerbar
    def set_browser_headerbar(self):
        self.builder.get_object("linkedbox_right").show_all()

        filename_label = self.builder.get_object("filename_label")
        filename_label.set_text(ntpath.basename(self.database_manager.database_path))

        secondary_menupopover_button = self.builder.get_object("secondary_menupopover_button")
        secondary_menupopover_button.hide()

        self.responsive_ui.headerbar_back_button()
        self.responsive_ui.headerbar_selection_button()
        self.responsive_ui.action_bar()
        self.responsive_ui.headerbar_title()

    #
    # Keystrokes
    #

    def bind_accelerator(self, accelerators, widget, accelerator, signal="clicked"):
        key, mod = Gtk.accelerator_parse(accelerator)
        widget.add_accelerator(signal, accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

    #
    # Group and Entry Management
    #

    def show_page_of_new_directory(self, edit_group, new_entry):
        # First, remove stack pages which should not exist because they are scheduled for remove
        self.destroy_current_page_if_scheduled()

        # Creation of group edit page
        if edit_group is True:
            builder = Gtk.Builder()
            builder.add_from_resource("/org/gnome/PasswordSafe/group_page.ui")
            scrolled_window = ScrolledPage(True)
            scrolled_window.properties_list_box = builder.get_object("properties_list_box")

            # Responsive Container
            hdy_page = Handy.Clamp()
            hdy_page.add(scrolled_window.properties_list_box)
            scrolled_window.add(hdy_page)
            scrolled_window.show_all()

            stack_page_uuid = self.current_element.uuid
            if self._stack.get_child_by_name(stack_page_uuid.urn) is not None:
                stack_page = self._stack.get_child_by_name(stack_page_uuid.urn)
                stack_page.destroy()

            self.add_page(scrolled_window, self.current_element.uuid.urn)
            self.switch_page(self.current_element)
            self.group_page.insert_group_properties_into_listbox(scrolled_window.properties_list_box)
            self.group_page.set_group_edit_page_headerbar()
        # If the stack page with current group's uuid isn't existing - we need to create it (first time opening of group/entry)
        elif (not self._stack.get_child_by_name(self.current_element.uuid.urn)
              and not edit_group):
            self.database_manager.set_element_atime(self.current_element)
            # Create not existing stack page for group
            if self.database_manager.check_is_group(self.current_element.uuid):
                builder = Gtk.Builder()
                builder.add_from_resource("/org/gnome/PasswordSafe/unlocked_database.ui")
                list_box = builder.get_object("list_box")
                list_box.connect("row-activated", self.on_list_box_row_activated)

                scrolled_window = ScrolledPage(False)
                viewport = Gtk.Viewport()
                overlay = Gtk.Overlay()

                # Responsive Container
                list_box.set_name("BrowserListBox")
                list_box.set_valign(Gtk.Align.START)

                hdy_browser = Handy.Clamp()
                hdy_browser.set_maximum_size(700)
                hdy_browser.add(list_box)
                overlay.add(hdy_browser)

                viewport.add(overlay)
                scrolled_window.add(viewport)
                scrolled_window.show_all()

                self.add_page(scrolled_window, self.current_element.uuid.urn)
                self.switch_page(self.current_element)

                list_box.hide()

                self.listbox_insert_thread = threading.Thread(target=self.insert_groups_into_listbox, args=(list_box, overlay))
                self.listbox_insert_thread.daemon = True
                self.listbox_insert_thread.start()
            # Create not existing stack page for entry
            else:
                builder = Gtk.Builder()
                builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

                scrolled_window = ScrolledPage(True)

                viewport = Gtk.Viewport()
                scrolled_window.properties_list_box = builder.get_object("properties_list_box")

                # Responsive Container
                hdy_page = Handy.Clamp()
                hdy_page.set_maximum_size(600)
                hdy_page.set_margin_top(18)
                hdy_page.set_margin_bottom(18)
                hdy_page.add(scrolled_window.properties_list_box)
                viewport.add(hdy_page)

                scrolled_window.add(viewport)
                scrolled_window.show_all()

                self.add_page(scrolled_window, self.current_element.uuid.urn)
                self.switch_page(self.current_element)
                if new_entry is True:
                    self.entry_page.insert_entry_properties_into_listbox(scrolled_window.properties_list_box, True)
                else:
                    self.entry_page.insert_entry_properties_into_listbox(scrolled_window.properties_list_box, False)
        # Stack page with current group's uuid already exists, we only need to switch stack page
        else:
            self.database_manager.set_element_atime(self.current_element)
            # For group
            if self.database_manager.check_is_group(self.current_element.uuid):
                self._stack.set_visible_child_name(self.current_element.uuid.urn)
                self.set_browser_headerbar()
            # For entry
            else:
                self._stack.set_visible_child_name(self.current_element.uuid.urn)
                self.entry_page.set_entry_page_headerbar()

    def add_page(self, scrolled_window: ScrolledPage, name: str) -> None:
        """Add a new page to the stack

        :param ScrolledPage scrolled_window: scrolled_page to add
        :param str name: name of the page
        """
        self._stack.add_named(scrolled_window, name)

    def switch_page(self, element: Union[Entry, Group]) -> None:
        """Set the current element and display it

        :param element: Entry or Group
        """
        self.current_element = element

        page_uuid = self.current_element.uuid
        group_page = self.database_manager.check_is_group(page_uuid)

        if page_uuid in self.scheduled_page_destroy:
            stack_page = self._stack.get_child_by_name(page_uuid.urn)
            if stack_page is not None:
                stack_page.destroy()

            self.scheduled_page_destroy.remove(page_uuid)
            self.show_page_of_new_directory(False, False)

        if self._stack.get_child_by_name(page_uuid.urn) is None:
            self.show_page_of_new_directory(False, False)
        else:
            self._stack.set_visible_child_name(page_uuid.urn)

        if group_page:
            self.set_browser_headerbar()
        else:
            self.entry_page.set_entry_page_headerbar()

    def _remove_page(self, element: Union[Entry, Group]) -> None:
        """Remove an element (Entry, Group) from the stack if present."""
        stack_page_name = element.uuid.urn
        stack_page = self._stack.get_child_by_name(stack_page_name)
        if stack_page:
            stack_page.destroy()

    @property
    def current_element(self) -> Union[Entry, Group]:
        return self._current_element

    @current_element.setter
    def current_element(self, element: Union[Entry, Group]) -> None:
        self._current_element = element

    def get_current_page(self) -> ScrolledPage:
        """Returns the page associated with current_element.

        :returns: current page
        :rtype: Gtk.Widget
        """
        element_uuid = self.current_element.uuid
        return self._stack.get_child_by_name(element_uuid.urn)

    def get_pages(self) -> List[ScrolledPage]:
        """Returns all the children of the stack.

        :returns: All the children of the stack.
        :rtype: list
        """
        return self._stack.get_children()

    def schedule_stack_page_for_destroy(self, page_uuid: UUID) -> None:
        """Add page to the list of pages to be destroyed"""
        logging.debug("Scheduling page %s for destruction", page_uuid)
        self.scheduled_page_destroy.append(page_uuid)

    def destroy_current_page_if_scheduled(self) -> None:
        """If the current_element is in self.scheduled_page_destroy, destroy it"""
        page_uuid = self.current_element.uuid
        logging.debug("Test if we should destroy page %s", page_uuid)
        if page_uuid in self.scheduled_page_destroy:
            logging.debug("Yes, destroying page %s", page_uuid)
            stack_page_name = self._stack.get_child_by_name(page_uuid.urn)
            if stack_page_name is not None:
                stack_page_name.destroy()
            self.scheduled_page_destroy.remove(page_uuid)

    #
    # Create Group & Entry Rows
    #

    def insert_groups_into_listbox(self, list_box, overlay):
        groups = NotImplemented
        sorted_list = []

        add_loading_indicator_thread = threading.Thread(target=self.add_loading_indicator_thread, args=(list_box, overlay))
        add_loading_indicator_thread.start()

        groups = self.current_element.subgroups
        GLib.idle_add(self.group_instance_creation, list_box, sorted_list, groups)

        self.insert_entries_into_listbox(list_box, overlay)

    def insert_entries_into_listbox(self, list_box, overlay):
        entries = self.current_element.entries
        sorted_list = []

        GLib.idle_add(self.entry_instance_creation, list_box, sorted_list, entries, overlay)

    def group_instance_creation(self, list_box, sorted_list, groups):
        for group in groups:
            group_row = GroupRow(self, self.database_manager, group)
            sorted_list.append(group_row)

        if self.list_box_sorting == "A-Z":
            sorted_list.sort(key=lambda group: str.lower(group.label), reverse=False)
        elif self.list_box_sorting == "Z-A":
            sorted_list.sort(key=lambda group: str.lower(group.label), reverse=True)

        for group_row in sorted_list:
            list_box.add(group_row)

    def entry_instance_creation(self, list_box, sorted_list, entries, overlay):
        for entry in entries:
            entry_row = EntryRow(self, entry)
            sorted_list.append(entry_row)

        if self.list_box_sorting == "A-Z":
            sorted_list.sort(key=lambda entry: str.lower(entry.label), reverse=False)
        elif self.list_box_sorting == "Z-A":
            sorted_list.sort(key=lambda entry: str.lower(entry.label), reverse=True)

        for entry_row in sorted_list:
            list_box.add(entry_row)

        if list_box.get_children():
            list_box.show()
        else:
            builder = Gtk.Builder()
            builder.add_from_resource("/org/gnome/PasswordSafe/unlocked_database.ui")
            empty_group_overlay = builder.get_object("empty_group_overlay")
            overlay.add_overlay(empty_group_overlay)
            list_box.hide()

    def rebuild_all_pages(self):
        for page in self._stack.get_children():
            if page.check_is_edit_page() is False:
                page.destroy()

        self.show_page_of_new_directory(False, False)

    #
    # Events
    #

    def _on_search_button_clicked(self, btn):
        # pylint: disable=unused-argument
        self.props.search_active = True

    def on_list_box_row_activated(self, _widget, list_box_row):
        self.start_database_lock_timer()

        if list_box_row.get_name() == "LoadMoreRow":
            self.search.on_load_more_row_clicked(list_box_row)

    def on_save_button_clicked(self, widget):
        self.start_database_lock_timer()
        if widget is not None:
            self.builder.get_object("menubutton_popover").popdown()

        if self.database_manager.is_dirty is True:
            if self.database_manager.save_running is False:
                save_thread = threading.Thread(target=self.database_manager.save_database)
                save_thread.daemon = False
                save_thread.start()
                self.show_database_action_revealer(_("Database saved"))
            else:
                # NOTE: In-app notification to inform the user that already an unfinished save job is running
                self.show_database_action_revealer(_("Please wait. Another save is running."))
        else:
            # NOTE: In-app notification to inform the user that no save is necessary because there where no changes made
            self.show_database_action_revealer(_("No changes made"))

    def on_lock_button_clicked(self, _widget):
        # shows save dialog if required
        self.show_save_dialog()
        self.database_manager.props.locked = True

    def on_add_entry_button_clicked(self, _widget):
        """CB when the Add Entry menu was clicked"""
        self.builder.get_object("menubutton_popover").popdown()
        self.start_database_lock_timer()
        self.database_manager.is_dirty = True
        new_entry: Entry = self.database_manager.add_entry_to_database(
            "", "", "", None, None, "0", self.current_element.uuid)
        self.current_element = new_entry
        self.pathbar.add_pathbar_button_to_pathbar(new_entry.uuid)
        self.show_page_of_new_directory(False, True)

    def on_add_group_button_clicked(self, _param: None) -> None:
        """CB when menu entry Add Group is clicked"""
        self.builder.get_object("menubutton_popover").popdown()
        self.start_database_lock_timer()
        self.database_manager.is_dirty = True
        group = self.database_manager.add_group_to_database("", "0", "", self.current_element)
        self.current_element = group
        self.pathbar.add_pathbar_button_to_pathbar(self.current_element.uuid)
        self.show_page_of_new_directory(True, False)

    def on_element_delete_menu_button_clicked(
            self, _action: Gio.SimpleAction, _param: None) -> None:
        """Delete the visible entry from the menu."""
        self.start_database_lock_timer()

        parent_group = self.database_manager.get_parent_group(
            self.current_element)
        self.database_manager.delete_from_database(self.current_element)

        self._remove_page(self.current_element)
        self.current_element = parent_group
        # Remove the parent group from the stack and add it again with
        # a show_page_of_new_directory call to force a full refresh of
        # teh group view.
        # FIXME: This operation is not efficient, it should be possible
        # to update the group view without removing it and adding it
        # again to the stack.
        self._remove_page(parent_group)
        self.show_page_of_new_directory(False, False)
        self.pathbar.rebuild_pathbar(self.current_element)

    def on_entry_duplicate_menu_button_clicked(self, _action, _param):
        self.start_database_lock_timer()

        self.database_manager.duplicate_entry(self.current_element)
        parent_group = self.database_manager.get_parent_group(
            self.current_element)

        if self.database_manager.check_is_root_group(parent_group) is True:
            self.pathbar.on_home_button_clicked(self.pathbar.home_button)
        else:
            for button in self.pathbar:
                if button.get_name() == "PathbarButtonDynamic" and isinstance(button, passwordsafe.pathbar_button.PathbarButton):
                    if button.uuid == parent_group.uuid:
                        self.pathbar.on_pathbar_button_clicked(button)

        # Remove the parent group from the stack and add it again with
        # a show_page_of_new_directory call to force a full refresh of
        # teh group view.
        # FIXME: This operation is not efficient, it should be possible
        # to update the group view without removing it and adding it
        # again to the stack.
        self._remove_page(parent_group)
        self.current_element = parent_group
        self.show_page_of_new_directory(False, False)

    def on_group_edit_button_clicked(self, button: Gtk.Button) -> None:
        """Edit button in a GroupRow was clicked

        button: The edit button in the GroupRow"""
        self.start_database_lock_timer()  # Reset the lock timer
        widget = button
        # Get the ancestor GroupRow object
        while not isinstance(widget, GroupRow):
            widget = widget.get_parent()
        group_uuid = widget.get_uuid()

        self.current_element = self.database_manager.get_group(group_uuid)
        self.pathbar.add_pathbar_button_to_pathbar(group_uuid)
        self.show_page_of_new_directory(True, False)

    def on_copy_secondary_button_clicked(self, widget, _position, _eventbutton):
        self.send_to_clipboard(widget.get_text())

    def send_to_clipboard(self, text):
        self.start_database_lock_timer()
        if self.clipboard_timer is not NotImplemented:
            self.clipboard_timer.cancel()

        replace_string = text
        for ref in re.finditer("({REF:.*?})", text):
            not_valid = False
            code = ref.group()[5]

            try:
                uuid = UUID(self.reference_to_hex_uuid(ref.group()))
            except Exception:
                not_valid = True

            value = NotImplemented

            if not_valid is False:
                if code == "T":
                    try:
                        value = self.database_manager.get_entry_name(uuid)
                    except AttributeError:
                        value = ref.group()
                elif code == "U":
                    try:
                        value = self.database_manager.get_entry_username(uuid)
                    except AttributeError:
                        value = ref.group()
                elif code == "P":
                    try:
                        value = self.database_manager.get_entry_password(uuid)
                    except AttributeError:
                        print("FAIL")
                        value = ref.group()
                elif code == "A":
                    try:
                        value = str(self.database_manager.get_entry_url(uuid))
                    except AttributeError:
                        value = ref.group()
                elif code == "N":
                    try:
                        value = str(self.database_manager.get_notes(uuid))
                    except AttributeError:
                        value = ref.group()

                replace_string = replace_string.replace(ref.group(), value)

        self.clipboard.set_text(replace_string, -1)

        self.show_database_action_revealer(_("Copied to clipboard"))
        clear_clipboard_time = passwordsafe.config_manager.get_clear_clipboard()
        self.clipboard_timer = Timer(clear_clipboard_time, GLib.idle_add, args=[self.clear_clipboard])
        self.clipboard_timer.start()

    def on_database_settings_entry_clicked(self, _action, _param):
        DatabaseSettingsDialog(self)

    def on_sort_menu_button_entry_clicked(self, _action, _param, sorting):
        self.start_database_lock_timer()
        passwordsafe.config_manager.set_sort_order(sorting)
        self.list_box_sorting = sorting
        self.rebuild_all_pages()

    def on_session_lock(self, _connection, _unique_name, _object_path, _interface, _signal, state):
        if state[0] and not self.database_manager.props.locked:
            self.lock_timeout_database()

    def _on_selection_button_clicked(self, button: Gtk.Button) -> None:
        # pylint: disable=unused-argument
        self.props.selection_mode = True

    def on_back_button_mobile_clicked(self, button):
        """Update the view when the back button is clicked.

        This button is only visible in the mobile mode.

        * if an Entry or a Group in edit mode was visible the parent
          group is displayed
        * if the visible group was the parent group, the database is
          locked.

        :param Gtk.Button button: clicked button
        """
        page_uuid = self.current_element.uuid
        scrolled_page = self._stack.get_child_by_name(page_uuid.urn)
        group_page = self.database_manager.check_is_group(page_uuid)

        parent = NotImplemented

        if scrolled_page.edit_page is True and group_page is True:
            parent = self.database_manager.get_parent_group(page_uuid)
        elif scrolled_page.edit_page is True and group_page is False:
            parent = self.database_manager.get_parent_group(page_uuid)
        elif (not scrolled_page.edit_page
              and not self.props.selection_mode
              and not self.props.search_active):
            if self.database_manager.check_is_root_group(self.current_element) is True:
                self.on_lock_button_clicked(None)
                return

            parent = self.database_manager.get_parent_group(page_uuid)

        if self.database_manager.check_is_root_group(parent) is True:
            self.pathbar.on_home_button_clicked(self.pathbar.home_button)
            return

        for button in self.pathbar:
            if button.get_name() == "PathbarButtonDynamic" and isinstance(button, passwordsafe.pathbar_button.PathbarButton):
                if button.uuid == parent.uuid:
                    self.pathbar.on_pathbar_button_clicked(button)

    #
    # Dialog Creator
    #

    def show_save_dialog(self) -> bool:
        """ Show the save confirmation dialog

        Saves the db and closes the tab.
        :returns: True if we saved, False if the whole thing should be aborted
        """
        if not self.database_manager.is_dirty \
           or self.database_manager.save_running:
            return True  # no dirty db, do nothing.
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/save_dialog.ui")
        save_dialog = builder.get_object("save_dialog")
        save_dialog.set_transient_for(self.window)

        res = save_dialog.run()
        save_dialog.destroy()
        if res in (
            Gtk.ResponseType.CANCEL,
            Gtk.ResponseType.NONE,
            Gtk.ResponseType.DELETE_EVENT,
        ):
            # Cancel everything, don't quit. Also activated when pressing escape
            return False

        if res == Gtk.ResponseType.NO:
            # clicked 'Discard'. Close, but don't save
            pass  # We are done with this db.
        elif res == Gtk.ResponseType.YES:
            # "clicked save". Save changes
            save_thread = threading.Thread(
                target=self.database_manager.save_database)
            save_thread.daemon = False
            save_thread.start()
        else:
            assert False, "Unknown Dialog Response!"

        return True

    def show_references_dialog(self, _action, _param):
        ReferencesDialog(self)

    def show_properties_dialog(self, _action: Gio.SimpleAction, _param: None) -> None:
        """Show a Group/Entry property dialog

        Invoked by the app.element.properties action"""
        PropertiesDialog(self).present()

    #
    # Utils
    #

    def show_database_action_revealer(self, message):
        database_action_label = self.builder.get_object("database_action_label")
        database_action_label.set_text(message)

        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())
        revealer_timer = Timer(3.0, GLib.idle_add, args=[self.hide_database_action_revealer])
        revealer_timer.start()

    def hide_database_action_revealer(self):
        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())

    def _on_database_lock_changed(self, database_manager, value):
        # pylint: disable=unused-argument
        locked = self.database_manager.props.locked
        if locked:
            self.cancel_timers()
            self.clipboard.clear()
            self.unregister_dbus_signal()
            self.stop_save_loop()

            if self.database_settings_dialog is not NotImplemented:
                self.database_settings_dialog.close()

            if self.notes_dialog is not NotImplemented:
                self.notes_dialog.close()

            if self.references_dialog is not NotImplemented:
                self.references_dialog.close()

            for tmpfile in self.scheduled_tmpfiles_deletion:
                try:
                    tmpfile.delete()
                except GLib.Error as e:
                    logging.warning(
                        "Skipping deletion of tmpfile %s: %s",
                        tmpfile.get_path(), e.message)

                if passwordsafe.config_manager.get_save_automatically():
                    save_thread = threading.Thread(target=self.database_manager.save_database)
                    save_thread.daemon = False
                    save_thread.start()

            self.overlay.hide()
        else:
            if self.props.search_active:
                self.parent_widget.set_headerbar(self.headerbar_search)
                self.window.set_titlebar(self.headerbar_search)
            else:
                self.parent_widget.set_headerbar(self.headerbar)
                self.window.set_titlebar(self.headerbar)

            self.start_save_loop()
            self.overlay.show()
            self.start_database_lock_timer()

    def lock_timeout_database(self):
        self.database_manager.props.locked = True

        # NOTE: Notification that a safe has been locked, Notification title has the safe file name in it
        self.send_notification(_("%s locked") % (os.path.splitext(ntpath.basename(self.database_manager.database_path))[0]), _("Keepass safe locked due to inactivity"))

    #
    # Helper Methods
    #

    def clear_clipboard(self):
        clear_clipboard_time = passwordsafe.config_manager.get_clear_clipboard()
        if clear_clipboard_time:
            self.clipboard.clear()

    def start_database_lock_timer(self):
        if self.database_manager.props.locked:
            return

        if self.database_lock_timer is not NotImplemented:
            self.database_lock_timer.cancel()
        timeout = passwordsafe.config_manager.get_database_lock_timeout() * 60
        if timeout:
            self.database_lock_timer = Timer(timeout, GLib.idle_add, args=[self.lock_timeout_database])
            self.database_lock_timer.start()

    def cancel_timers(self):
        if self.clipboard_timer is not NotImplemented:
            self.clipboard_timer.cancel()

        if self.database_lock_timer is not NotImplemented:
            self.database_lock_timer.cancel()

    def send_notification(self, title, text):
        notification = Gio.Notification.new(title)
        notification.set_body(text)
        self.window.application.send_notification(None, notification)

    def start_save_loop(self):
        self.save_loop = True
        save_loop_thread = threading.Thread(target=self.threaded_save_loop)
        save_loop_thread.daemon = True
        save_loop_thread.start()

    def threaded_save_loop(self):
        while self.save_loop is True:
            if passwordsafe.config_manager.get_save_automatically() is True:
                self.builder.get_object("save_button").set_sensitive(False)
                self.database_manager.save_database()
            else:
                self.builder.get_object("save_button").set_sensitive(True)
            time.sleep(30)

    def stop_save_loop(self):
        self.builder.get_object("save_button").set_sensitive(True)
        self.save_loop = False

    def add_loading_indicator_thread(self, list_box, overlay):
        time.sleep(1)
        if list_box.is_visible() is False and len(overlay.get_children()) < 2:
            GLib.idle_add(self.show_loading_indicator, list_box, overlay)

    def show_loading_indicator(self, list_box, overlay):
        spinner = Gtk.Spinner()
        spinner.show()
        spinner.start()
        overlay.add_overlay(spinner)

        remove_loading_indicator_thread = threading.Thread(target=self.remove_loading_indicator_thread, args=(list_box, overlay, spinner))
        remove_loading_indicator_thread.start()

    def remove_loading_indicator_thread(self, list_box, overlay, spinner):
        while list_box.is_visible() is False:
            continue
        else:
            GLib.idle_add(self.remove_loading_indicator, overlay, spinner)

    def remove_loading_indicator(self, overlay, spinner):
        overlay.remove(spinner)

    def reference_to_hex_uuid(self, reference_string):
        return reference_string[9:-1].lower()

    #
    # DBus
    #

    def register_dbus_signal(self):
        app = Gio.Application.get_default
        self.dbus_subscription_id = app().get_dbus_connection().signal_subscribe(None, "org.gnome.ScreenSaver", "ActiveChanged", "/org/gnome/ScreenSaver", None, Gio.DBusSignalFlags.NONE, self.on_session_lock)

    def unregister_dbus_signal(self):
        app = Gio.Application.get_default
        app().get_dbus_connection().signal_unsubscribe(self.dbus_subscription_id)

    @GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    def search_active(self) -> bool:
        """Property to know if search is active.

        It is used by Search to update the widgets (mainly the
        headerbar) accordingly.

        :returns: True is search is active
        :rtype: bool
        """
        return self._search_active

    @search_active.setter  # type: ignore
    def search_active(self, value: bool) -> None:
        """Set the search mode

        :param value: new search_active
        """
        self._search_active = value
        if self._search_active:
            self._stack.set_visible_child(
                self._stack.get_child_by_name("search"))
        else:
            self.show_page_of_new_directory(False, False)

    @GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    def database_locked(self):
        """Get database lock status

        :returns: True if the database is locked
        :rtype: bool
        """
        return self.database_manager.props.locked
