# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Adw, GObject, Gtk

from gsecrets.safe_element import SafeGroup
from gsecrets.widgets.notes_dialog import NotesDialog


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/group_page.ui")
class GroupPage(Adw.Bin):
    __gtype_name__ = "GroupPage"

    title_entry_row = Gtk.Template.Child()
    notes_text_view = Gtk.Template.Child()
    _window_title = Gtk.Template.Child()

    safe_group = GObject.Property(type=SafeGroup)

    def __init__(self, unlocked_database, safe_group):
        super().__init__(safe_group=safe_group)

        self.unlocked_database = unlocked_database

        safe_group = self.props.safe_group

        # Setup Widgets
        notes_buffer = self.notes_text_view.get_buffer()

        # Connect Signals
        safe_group.updated.connect(self._on_safe_group_updated)
        safe_group.bind_property(
            "name",
            self.title_entry_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        safe_group.bind_property(
            "notes",
            notes_buffer,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        safe_group.connect("notify::name", self._on_name_notify)
        self._set_title(safe_group)

    def _set_title(self, group):
        if group.parentgroup.is_root_group:
            title = group.name
        else:
            title = f"{group.parentgroup.name}  ⟩ {group.name}"

        self._window_title.props.title = title

    def _on_name_notify(self, group, _pspec):
        self._set_title(group)

    @Gtk.Template.Callback()
    def on_notes_detach_button_clicked(self, _button):
        self.unlocked_database.start_database_lock_timer()
        safe_group = self.props.safe_group
        NotesDialog(self.unlocked_database, safe_group).present(self)

    def _on_safe_group_updated(self, _safe_group: SafeGroup) -> None:
        self.unlocked_database.start_database_lock_timer()
