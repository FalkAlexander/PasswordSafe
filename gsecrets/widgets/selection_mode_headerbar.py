# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _
from gettext import ngettext
from logging import debug

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from gsecrets.entry_row import EntryRow
from gsecrets.group_row import GroupRow
from gsecrets.pathbar import Pathbar

if typing.TYPE_CHECKING:
    from gsecrets.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/selection_mode_headerbar.ui")
class SelectionModeHeaderbar(Adw.Bin):

    __gtype_name__ = "SelectionModeHeaderbar"

    unlocked_database = NotImplemented

    _cut_mode = True

    entries_selected: list[EntryRow] = []
    groups_selected: list[GroupRow] = []

    entries_cut: list[EntryRow] = []
    groups_cut: list[GroupRow] = []

    hidden_rows = Gio.ListStore.new(Gtk.ListBoxRow)

    _cut_button = Gtk.Template.Child()
    _cut_paste_button_stack = Gtk.Template.Child()
    _delete_button = Gtk.Template.Child()
    _paste_button = Gtk.Template.Child()
    _pathbar_bin = Gtk.Template.Child()
    _selection_options_button = Gtk.Template.Child()

    selected_elements = GObject.Property(type=int, default=0)

    def __init__(self, unlocked_database):
        super().__init__()

        pathbar = Pathbar(unlocked_database)
        self._pathbar_bin.set_child(pathbar)
        unlocked_database.action_bar.bind_property(
            "revealed",
            pathbar,
            "visible",
            GObject.BindingFlags.INVERT_BOOLEAN | GObject.BindingFlags.SYNC_CREATE,
        )

        self.unlocked_database = unlocked_database

        unlocked_database.connect(
            "notify::selection-mode", self._on_selection_mode_changed
        )
        unlocked_database.bind_property(
            "selection-mode", self, "visible", GObject.BindingFlags.SYNC_CREATE
        )
        self.connect("notify::selected-elements", self.on_selected_entries_changed)

    def on_selected_entries_changed(self, selection_ui, _value):
        new_number = selection_ui.props.selected_elements
        if new_number == 0:
            label = _("_Select Items")
        else:
            label = ngettext("{} _Selected", "{} _Selected", new_number).format(
                new_number
            )

        self._selection_options_button.props.label = label

    def _on_selection_mode_changed(
        self, unlocked_database: UnlockedDatabase, _value: GObject.ParamSpec
    ) -> None:
        if not unlocked_database.selection_mode:
            self._clear_all()

    # Events

    @Gtk.Template.Callback()
    def _on_delete_button_clicked(self, _widget):
        self.unlocked_database.start_database_lock_timer()

        # Abort the operation if there is a groups which is in the pathbar,
        # i.e. if it is a parent of the current view.
        for group_row in self.groups_selected:
            group = group_row.safe_group.group
            if self.unlocked_database.database_manager.parent_checker(
                self.unlocked_database.current_element, group
            ):
                self.unlocked_database.window.send_notification(
                    _("Operation aborted: deleting currently active group")
                )
                return

        # Before deleting we check if there is a mix of elements in the trash
        # bin and regular elements
        in_trash = False
        outside_trash = False
        for entry_row in self.entries_selected:
            element = entry_row.safe_entry
            parent = element.parentgroup
            if parent.is_trash_bin:
                in_trash = True
            else:
                outside_trash = True

        for group_row in self.groups_selected:
            element = group_row.safe_group
            parent = element.parentgroup
            if parent.is_trash_bin or element.is_trash_bin:
                in_trash = True
            else:
                outside_trash = True

        mixed = in_trash and outside_trash

        def delete_elements():
            # List of possible undos
            undo_elements = []
            for entry_row in self.entries_selected:
                element = entry_row.safe_entry
                parent = element.parentgroup
                if entry_row.safe_entry.trash():
                    self.unlocked_database.delete_page(element)
                else:
                    undo_elements.append((element, parent))

            for group_row in self.groups_selected:
                element = group_row.safe_group
                parent = element.parentgroup
                if group_row.safe_group.trash():
                    self.unlocked_database.delete_page(element)
                else:
                    undo_elements.append((element, parent))

            self.unlocked_database.deleted_notification(undo_elements)
            self._clear_all()

        if mixed:
            def response_delete_cb(dialog, response):
                delete_elements()

            dialog = Adw.MessageDialog.new(
                self.get_root(),
                _("Warning"),
                _(
                    "You are deleting elements in the trash bin, these deletions cannot be undone."  # pylint: disable=line-too-long # noqa: E501
                ),
            )
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("delete", _("Delete"))
            dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response::delete", response_delete_cb)
            dialog.present()
        else:
            delete_elements()

    @Gtk.Template.Callback()
    def _on_cut_button_clicked(self, _widget):
        self.unlocked_database.start_database_lock_timer()

        self.entries_cut = self.entries_selected
        self.groups_cut = self.groups_selected
        for group_row in self.groups_selected:
            group_row.props.sensitive = False
            self.hidden_rows.append(group_row)
        for entry_row in self.entries_selected:
            entry_row.props.sensitive = False
            self.hidden_rows.append(entry_row)

        # Do not allow to delete the entries or rows
        # that were selected to be cut.
        if self.entries_selected or self.groups_selected:
            self._delete_button.set_sensitive(False)

        self.props.cut_mode = False

    @Gtk.Template.Callback()
    def _on_paste_button_clicked(self, _widget):
        self.unlocked_database.start_database_lock_timer()

        # Abort the entire operation if one of the selected groups is a parent of
        # the current group.
        for group_row in self.groups_cut:
            group = group_row.safe_group.group
            current_element = self.unlocked_database.current_element
            if self.unlocked_database.database_manager.parent_checker(
                current_element, group
            ):
                self.unlocked_database.window.send_notification(
                    _("Operation aborted: moving currently active group")
                )
                self._clear_all()
                return

        current_element = self.unlocked_database.current_element

        for entry_row in self.entries_cut:
            safe_entry = entry_row.safe_entry
            safe_entry.move_to(current_element)

        for group_row in self.groups_cut:
            safe_group = group_row.safe_group
            safe_group.move_to(current_element)

        self.unlocked_database.window.send_notification(_("Move completed"))
        self._clear_all()

    def on_selection_action(self, variant: GLib.Variant) -> None:
        self.unlocked_database.start_database_lock_timer()

        selection_type = variant.get_string()
        page = self.unlocked_database.get_current_page()
        list_box = page.list_box

        for row in list_box:
            if selection_type == "all":
                row.selection_checkbox.set_active(True)
            else:
                row.selection_checkbox.set_active(False)

    # Helpers

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
        self._cut_button.set_sensitive(non_empty_selection)
        self._delete_button.set_sensitive(non_empty_selection)

        self.props.selected_elements = len(self.entries_selected) + len(
            self.groups_selected
        )

    def _clear_all(self) -> None:
        """Resets everything to the default state"""
        self.props.selected_elements = 0
        self.props.cut_mode = True
        self.entries_cut.clear()
        self.groups_cut.clear()
        self.entries_selected.clear()
        self.groups_selected.clear()
        self._delete_button.set_sensitive(False)
        self._cut_button.set_sensitive(False)
        for row in self.hidden_rows:
            row.props.sensitive = True

        self.hidden_rows.remove_all()
        self.emit("clear-selection")

    @GObject.Signal()
    def clear_selection(self):
        """Signal emitted to tell all list models that they should unselect
        their entries. It differs from the action app.selection.none, since
        the later removes selected entries only for the visible listbox."""
        debug("Clear selection signal emitted")

    @GObject.Property(type=bool, default=True)
    def cut_mode(self) -> bool:
        return self._cut_mode

    @cut_mode.setter  # type: ignore
    def cut_mode(self, mode: bool) -> None:
        stack = self._cut_paste_button_stack
        self._cut_mode = mode
        if mode:
            stack.set_visible_child(self._cut_button)
        else:
            stack.set_visible_child(self._paste_button)
