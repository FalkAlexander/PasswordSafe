# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from enum import IntEnum

from gi.repository import GObject, Gtk, Adw

if typing.TYPE_CHECKING:
    from passwordsafe.main_window import MainWindow
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/unlocked_headerbar.ui")
class UnlockedHeaderBar(Adw.HeaderBar):

    __gtype_name__ = "UnlockedHeaderBar"

    class Mode(IntEnum):
        GROUP = 0
        GROUP_EDIT = 1
        ENTRY = 2
        SELECTION = 3

    _add_button = Gtk.Template.Child()
    _pathbar_bin = Gtk.Template.Child()
    _headerbar_right_box = Gtk.Template.Child()
    _linkedbox_right = Gtk.Template.Child()
    search_button = Gtk.Template.Child()

    def __init__(self, unlocked_database):
        """HearderBar of an UnlockedDatabase

        :param UnlockedDatabase unlocked_database: unlocked_database
        """
        super().__init__()

        self._unlocked_database = unlocked_database
        self._action_bar = unlocked_database.action_bar
        self._db_manager = unlocked_database.database_manager
        self._pathbar = unlocked_database.pathbar
        self._window = unlocked_database.window

        self._mode: int = UnlockedHeaderBar.Mode.GROUP
        self.props.mode: int = UnlockedHeaderBar.Mode.GROUP

        self._setup_widgets()
        self._setup_signals()

    def _setup_widgets(self):
        is_mobile = self._window.props.mobile_layout

        self._pathbar_bin.set_child(self._pathbar)

        self._unlocked_database.action_bar.props.revealed = is_mobile

    def _setup_signals(self):
        self._window.connect(
            "notify::mobile-layout", self._on_mobile_layout_changed)

        self._unlocked_database.connect(
            "notify::search-active", self._on_search_active)

        self._on_mobile_layout_changed(None, None)

        self._pathbar.bind_property(
            "visible", self._action_bar, "revealed",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.INVERT_BOOLEAN,
        )

    def _on_search_active(
            self, _unlocked_database: UnlockedDatabase,
            _value: GObject.ParamSpecBoolean) -> None:
        self._update_action_bar()

    @Gtk.Template.Callback()
    def _on_search_button_clicked(self, _btn: Gtk.Button) -> None:
        self._unlocked_database.props.search_active = True

    @Gtk.Template.Callback()
    def _on_selection_button_clicked(self, _button: Gtk.Button) -> None:
        self._unlocked_database.props.selection_mode = True

    def _on_mobile_layout_changed(
            self, _klass: MainWindow | None,
            _value: GObject.ParamSpecBoolean) -> None:
        self._update_action_bar()

    def _update_action_bar(self):
        """Move pathbar between top headerbar and bottom actionbar if needed"""
        is_mobile = self._window.props.mobile_layout

        if self._unlocked_database.props.search_active:
            # No pathbar in search mode
            self._unlocked_database.action_bar.props.revealed = False
            return

        self._unlocked_database.action_bar.props.revealed = is_mobile

    @GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)
    def mode(self) -> int:
        """Get headerbar mode

        :returns: headerbar mode
        :rtype: int
        """
        return self._mode

    @mode.setter  # type: ignore
    def mode(self, new_mode: int) -> None:
        """Set headerbar mode

        :param int new_mode: new headerbar mode
        """
        self._mode = new_mode
