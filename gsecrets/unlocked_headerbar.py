# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlocked_headerbar.ui")
class UnlockedHeaderBar(Adw.Bin):

    __gtype_name__ = "UnlockedHeaderBar"

    _go_back_button = Gtk.Template.Child()

    def __init__(self, unlocked_database):
        """HearderBar of an UnlockedDatabase

        :param UnlockedDatabase unlocked_database: unlocked_database
        """
        super().__init__()

        self._unlocked_database = unlocked_database
        unlocked_database.connect(
            "notify::current-element", self._on_current_element_notify
        )

    @Gtk.Template.Callback()
    def _on_selection_button_clicked(self, _button: Gtk.Button) -> None:
        self._unlocked_database.props.selection_mode = True

    @Gtk.Template.Callback()
    def _on_go_back_button_clicked(self, _button):
        group = self._unlocked_database.current_element
        self._unlocked_database.show_browser_page(group.parentgroup)

    def _on_current_element_notify(self, unlocked_db, _pspec):
        sensitive = not unlocked_db.current_element.is_root_group
        self._go_back_button.props.sensitive = sensitive
