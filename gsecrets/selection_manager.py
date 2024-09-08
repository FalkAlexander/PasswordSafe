# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, Gio, GObject

from gsecrets.safe_element import SafeElement

if typing.TYPE_CHECKING:
    from gsecrets.unlocked_database import UnlockedDatabase


class SelectionManager(GObject.Object):
    __gtype_name__ = "SelectionManager"

    entries_selected: list[SafeElement] = []
    groups_selected: list[SafeElement] = []

    entries_cut: list[SafeElement] = []
    groups_cut: list[SafeElement] = []

    hidden_rows = Gio.ListStore.new(SafeElement)

    selected_elements = GObject.Property(type=int, default=0)
    cut_mode = GObject.Property(type=bool, default=True)

    def __init__(self, unlocked_database):
        super().__init__()

        self.unlocked_database = unlocked_database

        unlocked_database.connect(
            "notify::selection-mode",
            self._on_selection_mode_changed,
        )

    def _on_selection_mode_changed(
        self,
        unlocked_database: UnlockedDatabase,
        _value: GObject.ParamSpec,
    ) -> None:
        if not unlocked_database.props.selection_mode:
            self._clear_all()

    # Events

    def delete_selection(self):
        # Abort the operation if there is a groups which is in the pathbar,
        # i.e. if it is a parent of the current view.
        for safe_group in self.groups_selected:
            if self.unlocked_database.database_manager.parent_checker(
                self.unlocked_database.current_element,
                safe_group.group,
            ):
                self.unlocked_database.window.send_notification(
                    _("Operation aborted: deleting currently active group"),
                )
                return

        # Before deleting we check if there is a mix of elements in the trash
        # bin and regular elements
        in_trash = False
        outside_trash = False
        for element in self.entries_selected:
            parent = element.parentgroup
            if parent.is_trash_bin:
                in_trash = True
            else:
                outside_trash = True

        for element in self.groups_selected:
            parent = element.parentgroup
            if parent.is_trash_bin or element.is_trash_bin:
                in_trash = True
            else:
                outside_trash = True

        mixed = in_trash and outside_trash

        def delete_elements():
            # List of possible undos
            undo_elements = []
            for element in self.entries_selected:
                parent = element.parentgroup
                if not element.trash():
                    self.unlocked_database.browsing_panel.unselect(element)
                    undo_elements.append((element, parent))

            for element in self.groups_selected:
                parent = element.parentgroup
                self.unlocked_database.browsing_panel.unselect(element)
                if not element.trash():
                    undo_elements.append((element, parent))

            self.unlocked_database.deleted_notification(undo_elements)
            self._clear_all()

        if mixed:

            def response_delete_cb(_dialog, _response):
                delete_elements()

            dialog = Adw.AlertDialog.new(
                _("Warning"),
                _(
                    "You are deleting elements in the trash bin, these deletions cannot be undone.",  # noqa: E501
                ),
            )
            dialog.add_response("cancel", _("_Cancel"))
            dialog.add_response("delete", _("_Delete"))
            dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response::delete", response_delete_cb)
            dialog.present(self)
        else:
            delete_elements()

    def cut_selection(self):
        self.entries_cut = self.entries_selected
        self.groups_cut = self.groups_selected
        for group in self.groups_selected:
            group.props.sensitive = False
            self.hidden_rows.append(group)

        for entry in self.entries_selected:
            entry.props.sensitive = False
            self.hidden_rows.append(entry)

        self.props.cut_mode = False

    def paste_selection(self):
        # Abort the entire operation if one of the selected groups is a parent of
        # the current group.
        for safe_group in self.groups_cut:
            current_element = self.unlocked_database.current_element
            if self.unlocked_database.database_manager.parent_checker(
                current_element,
                safe_group.group,
            ):
                self.unlocked_database.window.send_notification(
                    _("Operation aborted: moving currently active group"),
                )
                self._clear_all()
                return

        current_element = self.unlocked_database.current_element

        for safe_entry in self.entries_cut:
            safe_entry.move_to(current_element)

        for safe_group in self.groups_cut:
            safe_group.move_to(current_element)

        self.unlocked_database.window.send_notification(_("Move completed"))
        self._clear_all()

    # Helpers

    def add_entry(self, entry: SafeElement) -> None:
        """Add an entry to selection.

        :param EntryRow group: entry_row to add
        """
        if entry not in self.entries_selected:
            self.entries_selected.append(entry)
            self._update_selection()

    def remove_entry(self, entry: SafeElement) -> None:
        """Remove an entry from selection.

        :param EntryRow group: entry_row to remove
        """
        if entry in self.entries_selected:
            self.entries_selected.remove(entry)

        self._update_selection()

    def add_group(self, group: SafeElement) -> None:
        """Add a group to selection.

        :param GroupRow group: group_row to add
        """
        if group not in self.groups_selected:
            self.groups_selected.append(group)
            self._update_selection()

    def remove_group(self, group: SafeElement) -> None:
        """Remove a group from selection.

        :param GroupRow group: group_row to remove
        """
        if group in self.groups_selected:
            self.groups_selected.remove(group)

        self._update_selection()

    def _update_selection(self) -> None:
        self.selected_elements = len(self.entries_selected) + len(self.groups_selected)

    def _clear_all(self) -> None:
        """Reset everything to the default state."""
        for group in reversed(self.groups_selected):
            group.selected = False

        for entry in reversed(self.entries_selected):
            entry.selected = False

        self.entries_selected.clear()
        self.groups_selected.clear()

        for element in self.hidden_rows:
            element.props.sensitive = True

        self.selected_elements = 0
        self.cut_mode = True
        self.entries_cut.clear()

        self.groups_cut.clear()
        self.hidden_rows.remove_all()

    def clear_selection(self):
        """Emit when the selection is cleared.

        Signal emitted to tell all list models that they should unselect
        their entries. It differs from the action app.selection.none, since
        the later removes selected entries only for the visible listbox.
        """
        for element in reversed(self.entries_selected):
            element.props.selected = False

        for element in reversed(self.groups_selected):
            element.props.selected = False
