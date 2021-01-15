# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _
from typing import List

from gi.repository import Gio, GObject, Gtk

from passwordsafe.entry_row import EntryRow
from passwordsafe.group_row import GroupRow

if typing.TYPE_CHECKING:
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/selection_ui.ui")
class SelectionUI(Gtk.Box):
    #
    # Global Variables
    #

    __gtype_name__ = "SelectionUI"

    unlocked_database = NotImplemented

    cut_mode = True

    entries_selected: List[EntryRow] = []
    groups_selected: List[GroupRow] = []

    entries_cut: List[EntryRow] = []
    groups_cut: List[GroupRow] = []

    hidden_rows = Gio.ListStore.new(Gtk.ListBoxRow)

    _cancel_button = Gtk.Template.Child()
    _cut_paste_button = Gtk.Template.Child()
    _cut_paste_image = Gtk.Template.Child()
    _delete_button = Gtk.Template.Child()

    #
    # Init
    #

    def __init__(self, u_d):
        super().__init__()

        self.unlocked_database = u_d

        self.unlocked_database.connect(
            "notify::selection-mode", self._on_selection_mode_changed)

        self.unlocked_database.bind_property(
            "selection-mode", self, "visible",
            GObject.BindingFlags.SYNC_CREATE)

    def _on_selection_mode_changed(
        self, unlocked_database: UnlockedDatabase, _value: GObject.ParamSpec
    ) -> None:
        if not unlocked_database.selection_mode:
            self._clear_all()

    #
    # Events
    #

    @Gtk.Template.Callback()
    def _on_cancel_button_clicked(self, _widget):
        self.unlocked_database.props.selection_mode = False

    @Gtk.Template.Callback()
    def _on_delete_button_clicked(self, _widget):
        # Abort the operation if there is a groups which is in the pathbar,
        # i.e. if it is a parent of the current view.
        for group_row in self.groups_selected:
            group_uuid = group_row.safe_group.uuid
            group = self.unlocked_database.database_manager.get_group(group_uuid)
            if self.unlocked_database.database_manager.parent_checker(
                    self.unlocked_database.current_element,
                    group
            ):
                self.unlocked_database.window.notify(_("Operation aborted: Deleting currently active group"))
                return

        for entry_row in self.entries_selected:
            safe_entry = entry_row.safe_entry
            self.unlocked_database.database_manager.delete_from_database(
                safe_entry.entry)

        for group_row in self.groups_selected:
            safe_group = group_row.safe_group
            self.unlocked_database.database_manager.delete_from_database(safe_group.group)

        self.unlocked_database.window.notify(_("Deletion completed"))

        self._clear_all()

    @Gtk.Template.Callback()
    def _on_cut_paste_button_clicked(self, _widget):
        # pylint: disable=too-many-branches
        if self.cut_mode is True:
            self.entries_cut = self.entries_selected
            self.groups_cut = self.groups_selected
            self._cut_paste_image.set_from_icon_name("edit-paste-symbolic", Gtk.IconSize.BUTTON)
            for group_row in self.groups_selected:
                group_row.hide()
                self.hidden_rows.append(group_row)
            for entry_row in self.entries_selected:
                entry_row.hide()
                self.hidden_rows.append(entry_row)

            # Do not allow to delete the entries or rows
            # that were selected to be cut.
            if self.entries_selected or self.groups_selected:
                self._delete_button.set_sensitive(False)

            self.cut_mode = False
            return

        self._cut_paste_image.set_from_icon_name(
            "edit-cut-symbolic", Gtk.IconSize.BUTTON
        )
        self.cut_mode = True

        # Abort the entire operation if one of the selected groups is a parent of
        # the current group.
        for group_row in self.groups_cut:
            group = group_row.safe_group.group
            current_element = self.unlocked_database.current_element
            if self.unlocked_database.database_manager.parent_checker(
                current_element, group
            ):
                self.unlocked_database.window.notify(
                    _("Operation aborted: Moving currently active group")
                )
                self._clear_all()
                return

        for entry_row in self.entries_cut:
            safe_entry = entry_row.safe_entry
            self.unlocked_database.database_manager.move_entry(
                safe_entry.uuid, self.unlocked_database.current_element.group)

        for group_row in self.groups_cut:
            group = group_row.safe_group.group
            current_element = self.unlocked_database.current_element
            self.unlocked_database.database_manager.move_group(
                group, current_element.element
            )

        self.unlocked_database.window.notify(_("Move completed"))
        self._clear_all()

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
        if entry in self.entries_selected:
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
        non_empty_selection = self.entries_selected or self.groups_selected
        self._cut_paste_button.set_sensitive(non_empty_selection)
        self._delete_button.set_sensitive(non_empty_selection)

        if not self.cut_mode:
            self.entries_cut.clear()
            self.groups_cut.clear()
            self._cut_paste_image.set_from_icon_name(
                "edit-cut-symbolic", Gtk.IconSize.BUTTON)

    def _clear_all(self) -> None:
        """Resets everything to the default state"""
        self.cut_mode = True
        self.entries_cut.clear()
        self.groups_cut.clear()
        self.entries_selected.clear()
        self.groups_selected.clear()
        self._delete_button.set_sensitive(False)
        self._cut_paste_button.set_sensitive(False)
        self._cut_paste_image.set_from_icon_name(
            "edit-cut-symbolic", Gtk.IconSize.BUTTON
        )
        for row in self.hidden_rows:
            row.show()

        self.hidden_rows.remove_all()
