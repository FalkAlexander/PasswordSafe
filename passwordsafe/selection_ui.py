# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _
from typing import List
from gi.repository import GObject, Gtk

import passwordsafe.pathbar_button
from passwordsafe.entry_row import EntryRow
from passwordsafe.group_row import GroupRow
if typing.TYPE_CHECKING:
    from passwordsafe.unlocked_database import UnlockedDatabase


class SelectionUI:
    #
    # Global Variables
    #

    unlocked_database = NotImplemented

    cut_mode = True

    entries_selected: List[EntryRow] = []
    groups_selected: List[GroupRow] = []

    entries_cut: List[EntryRow] = []
    groups_cut: List[GroupRow] = []

    #
    # Init
    #

    def __init__(self, u_d):
        self.unlocked_database = u_d

        self.unlocked_database.connect(
            "notify::selection-mode", self._on_selection_mode_changed)

    def initialize(self):
        # Selection Headerbar
        selection_cancel_button = self.unlocked_database.headerbar.builder.get_object("selection_cancel_button")
        selection_cancel_button.connect("clicked", self.on_selection_cancel_button_clicked)

        selection_delete_button = self.unlocked_database.headerbar.builder.get_object("selection_delete_button")
        selection_delete_button.connect("clicked", self.on_selection_delete_button_clicked)

        selection_cut_button = self.unlocked_database.headerbar.builder.get_object("selection_cut_button")
        selection_cut_button.connect("clicked", self.on_selection_cut_button_clicked)

    def _on_selection_mode_changed(
            self, unlocked_database: UnlockedDatabase,
            value: GObject.ParamSpec) -> None:
        # pylint: disable=unused-argument
        if self.unlocked_database.selection_mode:
            self._enter_selection_mode()
        else:
            self._exit_selection_mode()

    #
    # Selection Mode
    #

    # Selection headerbar
    def _enter_selection_mode(self):
        self.unlocked_database.headerbar.builder.get_object("selection_delete_button").set_sensitive(False)
        self.unlocked_database.headerbar.builder.get_object("selection_cut_button").set_sensitive(False)

        for stack_page in self.unlocked_database.get_pages():
            if not stack_page.check_is_edit_page():
                list_box = stack_page.get_children()[0].get_children()[0].get_children()[0].get_children()[0]
                for row in list_box:
                    if hasattr(row, "selection_checkbox"):
                        row.selection_checkbox.show()
                    if hasattr(row, "edit_button"):
                        row.edit_button.hide()

    def _exit_selection_mode(self):
        for stack_page in self.unlocked_database.get_pages():
            if stack_page.check_is_edit_page() is False:
                list_box = stack_page.get_children()[0].get_children()[0].get_children()[0].get_children()[0]
                for row in list_box:
                    row.show()
                    if hasattr(row, "selection_checkbox"):
                        row.selection_checkbox.hide()
                        row.selection_checkbox.set_active(False)
                    if hasattr(row, "edit_button") is True:
                        row.edit_button.show_all()

        self.cut_mode = True

        for element in self.unlocked_database.pathbar.get_children():
            if element.get_name() == "SeperatorLabel":
                el_context = element.get_style_context()
                el_context.remove_class('SeperatorLabelSelectedMode')
                el_context.add_class('SeperatorLabel')

        self.unlocked_database.show_page_of_new_directory(False, False)

    #
    # Events
    #

    def on_selection_cancel_button_clicked(self, _widget):
        self.unlocked_database.props.selection_mode = False
        self.unlocked_database.show_page_of_new_directory(False, False)

    def on_selection_delete_button_clicked(self, _widget):
        rebuild_pathbar = False
        reset_stack_page = False
        group = None

        for entry_row in self.entries_selected:
            entry = self.unlocked_database.database_manager.get_entry_object_from_uuid(entry_row.get_uuid())
            self.unlocked_database.database_manager.delete_from_database(entry)
            # If the deleted entry is in the pathbar, we need to rebuild the pathbar
            if self.unlocked_database.pathbar.uuid_in_pathbar(entry_row.get_uuid()) is True:
                rebuild_pathbar = True

        for group_row in self.groups_selected:
            group = self.unlocked_database.database_manager.get_group(group_row.get_uuid())
            self.unlocked_database.database_manager.delete_from_database(group)
            # If the deleted group is in the pathbar, we need to rebuild the pathbar
            if self.unlocked_database.pathbar.uuid_in_pathbar(group_row.get_uuid()) is True:
                rebuild_pathbar = True

            group_uuid = group.uuid
            current_uuid = self.unlocked_database.current_element.uuid
            if group_uuid == current_uuid:
                rebuild_pathbar = True
                reset_stack_page = True

        for stack_page in self.unlocked_database.get_pages():
            if stack_page.check_is_edit_page() is False:
                stack_page.destroy()

        self.unlocked_database.show_page_of_new_directory(False, False)

        if rebuild_pathbar is True:
            self.unlocked_database.pathbar.rebuild_pathbar(
                self.unlocked_database.current_element)

        if reset_stack_page is True:
            root_group = self.unlocked_database.database_manager.get_root_group()
            self.unlocked_database.current_element = root_group

        self.unlocked_database.show_database_action_revealer(_("Deletion completed"))

        self.entries_selected.clear()
        self.groups_selected.clear()
        self.unlocked_database.headerbar.builder.get_object("selection_delete_button").set_sensitive(False)
        self.unlocked_database.headerbar.builder.get_object("selection_cut_button").set_sensitive(False)

        # It is more efficient to do this here and not in the database manager loop
        self.unlocked_database.database_manager.is_dirty = True

    def on_selection_cut_button_clicked(self, widget):
        # pylint: disable=too-many-branches
        rebuild_pathbar = False

        if self.cut_mode is True:
            self.entries_cut = self.entries_selected
            self.groups_cut = self.groups_selected
            widget.get_children()[0].set_from_icon_name("edit-paste-symbolic", Gtk.IconSize.BUTTON)
            for group_row in self.groups_selected:
                group_row.hide()
            for entry_row in self.entries_selected:
                entry_row.hide()

            rebuild = False
            for button in self.unlocked_database.pathbar:
                if button.get_name() == "PathbarButtonDynamic" and isinstance(
                    button, passwordsafe.pathbar_button.PathbarButton
                ):
                    for group_row in self.groups_cut:
                        if button.uuid == group_row.get_uuid():
                            rebuild = True

            if rebuild is True:
                self.unlocked_database.pathbar.rebuild_pathbar(
                    self.unlocked_database.current_element)

            self.cut_mode = False
            return

        widget.get_children()[0].set_from_icon_name(
            "edit-cut-symbolic", Gtk.IconSize.BUTTON
        )
        self.cut_mode = True

        for entry_row in self.entries_cut:
            entry_uuid = entry_row.get_uuid()
            self.unlocked_database.database_manager.move_entry(
                entry_uuid, self.unlocked_database.current_element)
            # If the moved entry is in the pathbar, we need to rebuild the pathbar
            if self.unlocked_database.pathbar.uuid_in_pathbar(entry_row.get_uuid()) is True:
                rebuild_pathbar = True

        move_conflict = False

        for group_row in self.groups_cut:
            group_uuid = group_row.get_uuid()
            group = self.unlocked_database.database_manager.get_group(group_uuid)
            current_element = self.unlocked_database.current_element
            if not self.unlocked_database.database_manager.parent_checker(
                current_element, group
            ):
                self.unlocked_database.database_manager.move_group(
                    group, current_element
                )
            else:
                move_conflict = True
            # If the moved group is in the pathbar, we need to rebuild the pathbar
            if self.unlocked_database.pathbar.uuid_in_pathbar(group_uuid):
                rebuild_pathbar = True

        for stack_page in self.unlocked_database.get_pages():
            if stack_page.check_is_edit_page() is False:
                stack_page.destroy()

        self.unlocked_database.show_page_of_new_directory(False, False)

        if rebuild_pathbar is True:
            self.unlocked_database.pathbar.rebuild_pathbar(
                self.unlocked_database.current_element)

        if move_conflict is False:
            self.unlocked_database.show_database_action_revealer(_("Move completed"))
        else:
            self.unlocked_database.show_database_action_revealer(_("Skipped moving group into itself"))

        self.entries_cut.clear()
        self.groups_cut.clear()
        self.entries_selected.clear()
        self.groups_selected.clear()
        self.unlocked_database.headerbar.builder.get_object("selection_delete_button").set_sensitive(False)
        self.unlocked_database.headerbar.builder.get_object("selection_cut_button").set_sensitive(False)

    def on_selection_popover_button_clicked(self, _action, _param, selection_type):
        page = self.unlocked_database.get_current_page()
        viewport = page.get_children()[0]
        overlay = viewport.get_children()[0]
        list_box = NotImplemented

        column = overlay.get_children()[0]
        list_box = column.get_children()[0]

        for row in list_box:
            if selection_type == "all":
                row.selection_checkbox.set_active(True)
            else:
                row.selection_checkbox.set_active(False)

    #
    # Helper
    #

    def add_entry(self, entry: EntryRow) -> None:
        """Add an entry to selection

        :param EntryRow group: entry_row to add
        """
        self.entries_selected.append(entry)
        self._update_selection()

    def remove_entry(self, entry: EntryRow) -> None:
        """Remove an entry from selection

        :param EntryRow group: entry_row to remove
        """
        self.entries_selected.remove(entry)
        self._update_selection()

    def add_group(self, group: GroupRow) -> None:
        """Add a group to selection

        :param GroupRow group: group_row to add
        """
        if group not in self.groups_selected:
            self.groups_selected.append(group)
            self._update_selection()

    def remove_group(self, group: GroupRow) -> None:
        """Remove a group from selection

        :param GroupRow group: group_row to remove
        """
        if group in self.groups_selected:
            self.groups_selected.remove(group)
            self._update_selection()

    def _update_selection(self) -> None:
        selection_cut_button = self.unlocked_database.headerbar.builder.get_object(
            "selection_cut_button")
        selection_delete_button = self.unlocked_database.headerbar.builder.get_object(
            "selection_delete_button")

        non_empty_selection = self.entries_selected or self.groups_selected
        selection_cut_button.set_sensitive(non_empty_selection)
        selection_delete_button.set_sensitive(non_empty_selection)

        if not self.cut_mode:
            self.entries_cut.clear()
            self.groups_cut.clear()
            selection_cut_button.get_children()[0].set_from_icon_name(
                "edit-cut-symbolic", Gtk.IconSize.BUTTON)
