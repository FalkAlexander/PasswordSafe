# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import os
import typing
from enum import IntEnum
from typing import Optional

from gi.repository import GObject, Gtk, Handy

if typing.TYPE_CHECKING:
    from passwordsafe.main_window import MainWindow
    from passwordsafe.unlocked_database import UnlockedDatabase


class UnlockedHeaderBar(Handy.HeaderBar):

    __gtype_name__ = "UnlockedHeaderBar"

    class Mode(IntEnum):
        GROUP = 0
        GROUP_EDIT = 1
        ENTRY = 2
        SELECTION = 3

    def __new__(cls, unlocked_database):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_headerbar.ui")

        new_object = builder.get_object("headerbar")
        new_object.finish_initializing(builder, unlocked_database)
        return new_object

    def finish_initializing(self, builder, unlocked_database):
        self.builder = builder
        self._unlocked_database = unlocked_database
        self._db_manager = unlocked_database.database_manager
        self._pathbar = unlocked_database.pathbar
        self._window = unlocked_database.window

        self._headerbar_box = self.builder.get_object("headerbar_box")
        self._show_pathbar = True

        self._search_button = self.builder.get_object("search_button")
        self._search_button.connect("clicked", self._on_search_button_clicked)
        self._unlocked_database.bind_accelerator(self._search_button, "<Control>f")

        self._selection_button_box = self.builder.get_object(
            "selection_button_box")
        self._unlocked_database.bind_property(
            "selection-mode", self._selection_button_box, "visible",
            GObject.BindingFlags.SYNC_CREATE)

        self._selection_button = self.builder.get_object("selection_button")
        self._selection_button.connect(
            "clicked", self._on_selection_button_clicked)

        self._selection_button_mobile = builder.get_object("selection_button_mobile")
        self._selection_button_mobile.connect(
            "clicked", self._on_selection_button_clicked)

        self._selection_options_button = self.builder.get_object(
            "selection_options_button")
        self._unlocked_database.bind_property(
            "selection-mode", self._selection_options_button, "visible",
            GObject.BindingFlags.SYNC_CREATE)

        self._secondary_menu_button = self.builder.get_object("secondary_menu_button")
        self._entry_menu = self.builder.get_object("entry_menu")
        self._group_menu = self.builder.get_object("group_menu")
        self._linkedbox_right = self.builder.get_object("linkedbox_right")

        self._title_label = self.builder.get_object("title_label")
        self._window.connect(
            "notify::mobile-width", self._on_mobile_width_changed)

        self._mode: int = UnlockedHeaderBar.Mode.GROUP
        self.props.mode: int = UnlockedHeaderBar.Mode.GROUP
        self._unlocked_database.connect(
            "notify::selection-mode", self._on_selection_mode_changed)

    def _on_search_button_clicked(self, _btn: Gtk.Button) -> None:
        self._unlocked_database.props.search_active = True

    def _on_selection_button_clicked(self, _button: Gtk.Button) -> None:
        self._unlocked_database.props.selection_mode = True

    def _on_selection_mode_changed(
            self, _unlocked_database: UnlockedDatabase,
            _value: GObject.ParamSpecInt) -> None:
        if self._unlocked_database.props.selection_mode:
            self.props.mode = UnlockedHeaderBar.Mode.SELECTION

    def _on_mobile_width_changed(
            self, _klass: Optional[MainWindow],
            _value: GObject.ParamSpecBoolean) -> None:
        is_mobile = self._window.props.mobile_width
        scrolled_page = self._unlocked_database.get_current_page()
        cur_elt = self._unlocked_database.current_element

        if is_mobile and not self._unlocked_database.props.selection_mode:
            if not scrolled_page or not scrolled_page.edit_page:
                # No edit page, show safe filename
                title = os.path.basename(self._db_manager.database_path)
            elif self._db_manager.check_is_group_object(cur_elt):
                # on group edit page, show entry title
                title = cur_elt.name or ""
            else:
                # on entry edit page, show entry title
                title = cur_elt.title or ""

            self._title_label.props.label = title

        show = is_mobile and not self._unlocked_database.props.selection_mode
        self._title_label.props.visible = show

    @GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    def show_pathbar(self):
        return self._show_pathbar

    @show_pathbar.setter  # type: ignore
    def show_pathbar(self, value):
        self._show_pathbar = value

        if self._show_pathbar:
            self._headerbar_box.add(self._pathbar)
        else:
            self._headerbar_box.remove(self._pathbar)

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
            self._linkedbox_right.props.visible = not selection_mode
        elif new_mode == UnlockedHeaderBar.Mode.GROUP_EDIT:
            self._secondary_menu_button.props.menu_model = self._group_menu
            self._secondary_menu_button.props.visible = True
            self._linkedbox_right.props.visible = False
        elif new_mode == UnlockedHeaderBar.Mode.ENTRY:
            self._secondary_menu_button.props.menu_model = self._entry_menu
            self._secondary_menu_button.props.visible = True
            self._linkedbox_right.props.visible = False
        else:
            self._secondary_menu_button.props.visible = False
            self._linkedbox_right.props.visible = False

        self._on_mobile_width_changed(None, None)
