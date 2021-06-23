# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk

from gsecrets.utils import format_time


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/history_row.ui")
class HistoryRow(Adw.ActionRow):

    __gtype_name__ = "HistoryRow"

    visibility_button = Gtk.Template.Child()

    _reveal: bool = False

    def __init__(self, history_entry, window):
        super().__init__()

        self.history_entry = history_entry
        self.list_model = window.list_model
        self.password = history_entry.password
        self.safe_entry = window.safe_entry
        self.unlocked_database = window.unlocked_database
        self.window = window

        self.props.subtitle = format_time(history_entry.mtime)
        self.props.title = "•" * len(self.password)

        self.install_property_action("historyrow.reveal", "reveal")

    @GObject.Property(type=bool, default=False)
    def reveal(self) -> bool:
        return self._reveal

    @reveal.setter  # type: ignore
    def reveal(self, reveal) -> bool:
        button = self.visibility_button
        if reveal:
            button.props.icon_name = "eye-not-looking-symbolic"
            button.props.tooltip_text = _("Hide Text")
            self.props.title = self.password
        else:
            button.props.icon_name = "eye-open-negative-filled-symbolic"
            button.props.tooltip_text = _("Show Text")
            self.props.title = "•" * len(self.password)

        self._reveal = reveal

    @Gtk.Template.Callback()
    def _on_copy_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(self.password)

    @Gtk.Template.Callback()
    def _on_delete_button_clicked(self, _button):
        self.safe_entry.delete_history(self.history_entry)
        found, pos = self.list_model.find(self.history_entry)
        if found:
            self.list_model.remove(pos)

        if self.list_model.get_n_items() == 0:
            self.window.close()
