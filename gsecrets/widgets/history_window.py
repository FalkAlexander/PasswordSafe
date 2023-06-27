# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Adw, Gtk, Gio

from gsecrets.safe_element import SafeElement
from gsecrets.widgets.history_row import HistoryRow


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/history_window.ui")
class HistoryWindow(Adw.Window):
    __gtype_name__ = "HistoryWindow"

    listbox = Gtk.Template.Child()

    def __init__(self, safe_entry, unlocked_database):
        super().__init__()

        self.list_model = Gio.ListStore.new(SafeElement)
        self.safe_entry = safe_entry
        self.unlocked_database = unlocked_database
        self.set_transient_for(unlocked_database.window)

        history = safe_entry.history[::-1]  # Reversed, order by newest first.
        self.list_model.splice(0, 0, history)
        self.listbox.bind_model(self.list_model, HistoryRow, self)

        self.unlocked_database.database_manager.connect(
            "notify::locked", self._on_locked
        )

    def _on_locked(self, database_manager, _value):
        if database_manager.props.locked:
            self.close()
