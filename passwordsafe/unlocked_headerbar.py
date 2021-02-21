# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing

from gi.repository import Adw, GObject, Gtk

if typing.TYPE_CHECKING:
    from passwordsafe.main_window import MainWindow


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/unlocked_headerbar.ui")
class UnlockedHeaderBar(Adw.HeaderBar):

    __gtype_name__ = "UnlockedHeaderBar"

    _pathbar_bin = Gtk.Template.Child()

    def __init__(self, unlocked_database):
        """HearderBar of an UnlockedDatabase

        :param UnlockedDatabase unlocked_database: unlocked_database
        """
        super().__init__()

        self._unlocked_database = unlocked_database
        self._action_bar = unlocked_database.action_bar
        self._pathbar = unlocked_database.pathbar
        self._window = unlocked_database.window

        self._setup_widgets()
        self._setup_signals()

    def _setup_widgets(self):
        is_mobile = self._window.props.mobile_layout

        self._pathbar_bin.set_child(self._pathbar)

        self._unlocked_database.action_bar.props.revealed = is_mobile

    def _setup_signals(self):
        self._window.connect(
            "notify::mobile-layout", self._on_mobile_layout_changed)

        self._on_mobile_layout_changed(None, None)

        self._pathbar.bind_property(
            "visible", self._action_bar, "revealed",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.INVERT_BOOLEAN,
        )

    @Gtk.Template.Callback()
    def _on_selection_button_clicked(self, _button: Gtk.Button) -> None:
        self._unlocked_database.props.selection_mode = True

    def _on_mobile_layout_changed(
        self, _window: MainWindow, _value: GObject.ParamSpecBoolean
    ) -> None:
        is_mobile = self._window.props.mobile_layout
        self._unlocked_database.action_bar.props.revealed = is_mobile
