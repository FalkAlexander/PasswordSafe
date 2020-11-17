# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from typing import Optional, Union
from uuid import UUID

from gi.repository import Gtk
from pykeepass.group import Group

from passwordsafe.pathbar_button import PathbarButton

if typing.TYPE_CHECKING:
    from passwordsafe.safe_entry import SafeEntry


class Pathbar(Gtk.Box):
    """Pathbar provides a breadcrumb-style Box with the current hierarchy"""
    unlocked_database = NotImplemented
    database_manager = NotImplemented
    path = NotImplemented
    builder = NotImplemented
    home_button = NotImplemented

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

    def first_appearance(self):
        self.home_button = self.builder.get_object("home_button")
        self.home_button.connect("clicked", self.on_home_button_clicked)
        self.set_active_style(self.home_button)
        self.pack_start(self.home_button, True, True, 0)

        seperator_label = Gtk.Label()
        seperator_label.set_text("/")
        seperator_label.set_name("SeperatorLabel")
        context = seperator_label.get_style_context()
        if not self.unlocked_database.props.selection_mode:
            context.add_class('SeperatorLabel')
        else:
            context.add_class('SeperatorLabelSelectedMode')
        self.pack_end(seperator_label, True, True, 0)

    def add_home_button(self):
        self.home_button = self.builder.get_object("home_button")
        self.home_button.connect("clicked", self.on_home_button_clicked)

        self.pack_end(self.home_button, True, True, 0)

    def add_seperator_label(self):
        seperator_label = Gtk.Label()
        seperator_label.set_text("/")
        seperator_label.set_name("SeperatorLabel")
        context = seperator_label.get_style_context()
        if not self.unlocked_database.props.selection_mode:
            context.add_class('SeperatorLabel')
        else:
            context.add_class('SeperatorLabelSelectedMode')
        self.pack_end(seperator_label, True, True, 0)

    #
    # Pathbar Modifications
    #
    def add_pathbar_button_to_pathbar(
            self, element: Union[SafeEntry, Group]) -> None:
        self.clear_pathbar()
        pathbar_button_active = self.create_pathbar_button(element)

        self.remove_active_style()
        self.set_active_style(pathbar_button_active)
        self.pack_end(pathbar_button_active, True, True, 0)

        self.add_seperator_label()

        parent_group = element.parentgroup
        while not parent_group.is_root_group:
            self.pack_end(
                self.create_pathbar_button(parent_group),
                True, True, 0)
            self.add_seperator_label()
            parent_group = parent_group.parentgroup

        self.add_home_button()
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
        for widget in self.get_children():
            self.remove(widget)

    def set_active_style(self, pathbar_button):
        context = pathbar_button.get_style_context()
        context.add_class('PathbarButtonActive')

    def remove_active_style(self):
        for pathbar_button in self.get_children():
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

        if not page.check_is_edit_page():
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
            or (current_elt.props.icon != 0)
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
        for button in self.get_children():
            if button.get_name() == "PathbarButtonDynamic" and \
               button.element.uuid == uuid:
                return True
        return False

    def get_pathbar_button(self, uuid: UUID) -> Optional["PathbarButton"]:
        for pathbar_button in self.get_children():
            if pathbar_button.get_name() == "PathbarButtonDynamic":
                if pathbar_button.element.uuid == uuid:
                    return pathbar_button
        logging.warning("requested get_pathbar_button on an inexisting uuid")
        return None
