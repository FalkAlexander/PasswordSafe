# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _, ngettext
import typing
from enum import IntEnum

from gi.repository import GObject, Gtk, Handy

from passwordsafe.selection_ui import SelectionUI
if typing.TYPE_CHECKING:
    from passwordsafe.main_window import MainWindow
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/unlocked_headerbar.ui")
class UnlockedHeaderBar(Handy.HeaderBar):

    __gtype_name__ = "UnlockedHeaderBar"

    class Mode(IntEnum):
        GROUP = 0
        GROUP_EDIT = 1
        ENTRY = 2
        SELECTION = 3

    _add_button = Gtk.Template.Child()
    _entry_menu = Gtk.Template.Child()
    _back_button = Gtk.Template.Child()
    _group_menu = Gtk.Template.Child()
    _headerbar_box = Gtk.Template.Child()
    _headerbar_right_box = Gtk.Template.Child()
    _linkedbox_left = Gtk.Template.Child()
    _linkedbox_right = Gtk.Template.Child()
    _secondary_menu_button = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    _selection_options_button = Gtk.Template.Child()
    _title_label = Gtk.Template.Child()

    def __init__(self, unlocked_database):
        """HearderBar of an UnlockedDatabase

        :param UnlockedDatabase unlocked_database: unlocked_database
        """
        super().__init__()

        self._unlocked_database = unlocked_database
        self._action_bar = unlocked_database.action_bar
        self._db_manager = unlocked_database.database_manager
        self._pathbar = unlocked_database.pathbar
        self._mobile_pathbar = unlocked_database.mobile_pathbar
        self._window = unlocked_database.window

        self._selection_ui = SelectionUI(self._unlocked_database)
        self._headerbar_right_box.append(self._selection_ui)

        self._mode: int = UnlockedHeaderBar.Mode.GROUP
        self.props.mode: int = UnlockedHeaderBar.Mode.GROUP

        self._setup_widgets()
        self._setup_signals()
        self._setup_accelerators()

    def _setup_widgets(self):
        is_mobile = self._window.props.mobile_layout

        self._action_bar.pack_start(self._mobile_pathbar)
        self._headerbar_box.append(self._pathbar)

        self._unlocked_database.action_bar.props.revealed = is_mobile

    def _setup_signals(self):
        self._window.connect(
            "notify::mobile-layout", self._on_mobile_layout_changed)

        self._unlocked_database.bind_property(
            "selection-mode", self._selection_options_button, "visible",
            GObject.BindingFlags.SYNC_CREATE)
        self._unlocked_database.connect(
            "notify::selection-mode", self._on_selection_mode_changed)

        self._unlocked_database.connect(
            "notify::search-active", self._on_search_active)

        self._selection_ui.connect(
            "notify::selected-elements", self.on_selected_entries_changed)

        self._on_mobile_layout_changed(None, None)

        self._pathbar.bind_property(
            "visible", self._action_bar, "revealed",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.INVERT_BOOLEAN,
        )

    def _setup_accelerators(self):
        self._unlocked_database.bind_accelerator(self.search_button, "<primary>f")

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

    def _on_selection_mode_changed(
            self, _unlocked_database: UnlockedDatabase,
            _value: GObject.ParamSpecInt) -> None:
        style_context = self.get_style_context()
        if self._unlocked_database.props.selection_mode:
            style_context.add_class("selection-mode")
            self.props.mode = UnlockedHeaderBar.Mode.SELECTION
        else:
            style_context.remove_class("selection-mode")
            self.props.mode = UnlockedHeaderBar.Mode.GROUP

    def _on_mobile_layout_changed(
            self, _klass: MainWindow | None,
            _value: GObject.ParamSpecBoolean) -> None:
        self._update_action_bar()

    def on_selected_entries_changed(self, selection_ui, _value):
        new_number = selection_ui.props.selected_elements
        if new_number == 0:
            label = _("Click on a checkbox to select")
        else:
            label = ngettext(
                "{} Selected entry", "{} Selected entries",
                new_number).format(new_number)

        self._selection_options_button.props.label = label

    def _update_action_bar(self):
        """Move pathbar between top headerbar and bottom actionbar if needed"""
        is_mobile = self._window.props.mobile_layout

        if self._unlocked_database.props.search_active:
            # No pathbar in search mode
            self._unlocked_database.action_bar.props.revealed = False
            return

        self._unlocked_database.action_bar.props.revealed = is_mobile

    @property
    def selection_ui(self) -> SelectionUI:
        """SelectionUI getter

        :returns: selection box
        :rtype: SelectionUI
        """
        return self._selection_ui

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

        if new_mode == UnlockedHeaderBar.Mode.GROUP:
            self._secondary_menu_button.props.visible = False
            selection_mode = self._unlocked_database.props.selection_mode
            self._add_button.props.visible = not selection_mode
            self._linkedbox_right.props.visible = not selection_mode
            self._linkedbox_left.set_visible_child(self._add_button)
        elif new_mode == UnlockedHeaderBar.Mode.GROUP_EDIT:
            self._add_button.props.visible = False
            self._secondary_menu_button.props.menu_model = self._group_menu
            self._secondary_menu_button.props.visible = True
            self._linkedbox_right.props.visible = False
            self._linkedbox_left.set_visible_child(self._back_button)
        elif new_mode == UnlockedHeaderBar.Mode.ENTRY:
            self._add_button.props.visible = False
            self._secondary_menu_button.props.menu_model = self._entry_menu
            self._secondary_menu_button.props.visible = True
            self._linkedbox_right.props.visible = False
            self._linkedbox_left.set_visible_child(self._back_button)
        else:
            self._add_button.props.visible = False
            self._secondary_menu_button.props.visible = False
            self._linkedbox_right.props.visible = False
            self._linkedbox_left.set_visible_child(self._add_button)
