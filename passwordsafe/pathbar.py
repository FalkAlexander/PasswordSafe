# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from typing import Union
from uuid import UUID

from gi.repository import Gio, Gtk
from pykeepass.group import Group

from passwordsafe.pathbar_button import PathbarButton

if typing.TYPE_CHECKING:
    from gi.repository import GObject

    from passwordsafe.safe_entry import SafeEntry
    from passwordsafe.unlocked_database import UnlockedDatabase


class Pathbar(Gtk.Box):
    """Pathbar provides a breadcrumb-style Box with the current hierarchy"""
    unlocked_database = NotImplemented
    database_manager = NotImplemented
    path = NotImplemented
    builder = NotImplemented
    home_button = NotImplemented

    buttons = Gio.ListStore.new(PathbarButton)

    def __init__(self, unlocked_database, dbm):
        super().__init__()
        self.set_name("Pathbar")
        self.unlocked_database = unlocked_database
        self.database_manager = dbm

        self.builder = Gtk.Builder()
        self.builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_database.ui")

        self.assemble_pathbar()

    #
    # Build Pathbar
    #

    def assemble_pathbar(self):
        self.first_appearance()
        self.set_halign(Gtk.Align.START)
        self.show_all()

    def new_home_button(self) -> PathbarButton:
        home_button = PathbarButton(self.database_manager.get_root_group())
        home_button.connect("clicked", self.on_home_button_clicked)
        home_button_image = self.builder.get_object("root_button_picture")
        home_button.add(home_button_image)
        return home_button

    def first_appearance(self):
        self.home_button = self.new_home_button()
        self.set_active_style(self.home_button)
        self.add(self.home_button)
        self.buttons.append(self.home_button)

        separator_label = PathbarSeparator(self.unlocked_database)
        self.add(separator_label)

    def add_home_button(self):
        self.home_button = self.new_home_button()
        self.home_button.connect("clicked", self.on_home_button_clicked)

        self.add(self.home_button)
        self.buttons.append(self.home_button)

    def add_separator_label(self):
        separator_label = PathbarSeparator(self.unlocked_database)
        self.add(separator_label)

    #
    # Pathbar Modifications
    #
    def add_pathbar_button_to_pathbar(
            self, element: Union[SafeEntry, Group]) -> None:
        self.clear_pathbar()
        parent_group = element.parentgroup

        self.buttons.append(self.home_button)

        while not parent_group.is_root_group:
            self.buttons.insert(1, self.create_pathbar_button(parent_group))
            parent_group = parent_group.parentgroup

        for button in self.buttons:
            self.add(button)
            self.add_separator_label()

        pathbar_button_active = self.create_pathbar_button(element)
        self.set_active_style(pathbar_button_active)
        self.add(pathbar_button_active)
        self.buttons.append(pathbar_button_active)

        self.show_all()

    def create_pathbar_button(self, element: Union[SafeEntry, Group]) -> PathbarButton:
        pathbar_button = PathbarButton(element)

        pathbar_button_name = NotImplemented

        if self.database_manager.check_is_group_object(element):
            pathbar_button_name = self.database_manager.get_group_name(element)
        else:
            pathbar_button_name = element.props.name

        if pathbar_button_name is not None:
            pathbar_button.set_label(pathbar_button_name)
        else:
            pathbar_button.set_label("Noname")

        pathbar_button.set_relief(Gtk.ReliefStyle.NONE)
        pathbar_button.activate()
        pathbar_button.connect("clicked", self.on_pathbar_button_clicked)

        return pathbar_button

    def clear_pathbar(self):
        self.remove_active_style()
        self.buttons.remove_all()
        for widget in self.get_children():
            self.remove(widget)

    def set_active_style(self, pathbar_button):
        context = pathbar_button.get_style_context()
        context.add_class('PathbarButtonActive')

    def remove_active_style(self):
        for pathbar_button in self.buttons:
            context = pathbar_button.get_style_context()
            context.remove_class('PathbarButtonActive')

    def rebuild_pathbar(self, group: Group) -> None:
        """Rebuild the pathbar up to a certain group"""
        if self.database_manager.check_is_root_group(group):
            self.clear_pathbar()
            self.first_appearance()
            self.show_all()
        else:
            self.add_pathbar_button_to_pathbar(group)

    #
    # Events
    #

    def on_home_button_clicked(self, widget):
        self.unlocked_database.start_database_lock_timer()
        self.remove_active_style()
        self.set_active_style(widget)

        if self.check_values_of_edit_page(self.database_manager.get_root_group()) is False:
            self.query_page_update()

        self.unlocked_database.switch_page(
            self.database_manager.get_root_group())
        self.rebuild_pathbar(self.database_manager.get_root_group())

    def on_pathbar_button_clicked(self, pathbar_button):
        self.unlocked_database.start_database_lock_timer()
        pathbar_button_elem = pathbar_button.element
        current_elem_uuid = self.unlocked_database.current_element.uuid

        if pathbar_button_elem.uuid != current_elem_uuid:
            is_group = pathbar_button.is_group
            selection_mode = self.unlocked_database.props.selection_mode
            if (is_group
                    or (not is_group and not selection_mode)):
                self.remove_active_style()
                self.set_active_style(pathbar_button)

                if (is_group
                        and not self.check_values_of_edit_page(pathbar_button_elem)):
                    self.query_page_update()

                self.unlocked_database.switch_page(pathbar_button_elem)
                self.rebuild_pathbar(pathbar_button_elem)
    #
    # Helper Methods
    #

    def query_page_update(self) -> None:
        """When a group/entry was edited, schedule modified page for destruction

        When the page was modified, schedule the parent page for
        destruction, otherwise, just the current one.
        """
        current_ele = self.unlocked_database.current_element
        page = self.unlocked_database.get_current_page()

        if not page.edit_page:
            # Do nothing on non-edit pages
            return

        if page.is_dirty:
            # page is dirty, parent page needs to be rebuild too
            parent_group = current_ele.parentgroup
            page_uuid = parent_group.uuid
            self.unlocked_database.schedule_stack_page_for_destroy(page_uuid)
            page.is_dirty = False

        # Destroy edited page so we rebuild when needed
        self.unlocked_database.schedule_stack_page_for_destroy(current_ele.uuid)

    def check_values_of_edit_page(self, parent_group: Group) -> bool:
        """Check all values of the current group/entry which we finished editing

        If all are blank we delete the entry/group and return True.
        It also schedules the parent page for destruction if the
        SafeEntry/Group has been deleted.
        """
        current_elt: Union[SafeEntry, Group] = self.unlocked_database.current_element

        if self.database_manager.check_is_group_object(current_elt):
            group_name = self.database_manager.get_group_name(current_elt)
            notes = self.database_manager.get_notes(current_elt)
            icon = self.database_manager.get_icon(current_elt)
            if not (group_name or notes or icon):
                parent_group = current_elt.parentgroup
                self.database_manager.delete_from_database(current_elt)
                self.rebuild_pathbar(parent_group)
                self.unlocked_database.schedule_stack_page_for_destroy(parent_group.uuid)
                return True

            return False

        # current_elt is a SafeEntry
        if not (
            current_elt.props.name
            or current_elt.props.username
            or current_elt.props.password
            or current_elt.props.url
            or current_elt.props.notes
            or (current_elt.props.icon != "0")
            or current_elt.props.attributes
        ):
            parent_group = self.database_manager.parentgroup
            self.database_manager.delete_from_database(current_elt.entry)
            self.rebuild_pathbar(parent_group)
            self.unlocked_database.schedule_stack_page_for_destroy(parent_group.uuid)
            return True

        return False

    def uuid_in_pathbar(self, uuid: UUID) -> bool:
        """Return True if the uuid entry is visible in the bar"""
        for button in self.buttons:
            if button.element.uuid == uuid:
                return True
        return False


class PathbarSeparator(Gtk.Label):
    def __init__(self, unlocked_database):
        super().__init__()

        self.unlocked_database = unlocked_database

        self.set_text("/")

        context = self.get_style_context()
        if not self.unlocked_database.props.selection_mode:
            context.add_class("dim-label")

        self.unlocked_database.connect("notify::selection-mode", self._on_selection_mode_changed)

    def _on_selection_mode_changed(
        self, unlocked_database: UnlockedDatabase, _value: GObject.ParamSpecBoolean
    ) -> None:
        context = self.get_style_context()
        if unlocked_database.props.selection_mode:
            context.remove_class("dim-label")
        else:
            context.add_class("dim-label")
