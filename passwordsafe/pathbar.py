# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing

from gi.repository import Gio, GObject, Gtk

from passwordsafe.pathbar_button import PathbarButton
from passwordsafe.safe_element import SafeElement

if typing.TYPE_CHECKING:
    from passwordsafe.unlocked_database import UnlockedDatabase


class Pathbar(Gtk.Box):
    """Pathbar provides a breadcrumb-style Box with the current hierarchy"""
    buttons = Gio.ListStore.new(PathbarButton)

    current_element = GObject.Property(
        type=SafeElement, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, unlocked_database, dbm):
        super().__init__()
        self.set_name("Pathbar")
        self.unlocked_database = unlocked_database
        self.database_manager = dbm

        unlocked_database.bind_property(
            "current-element", self, "current-element",
            GObject.BindingFlags.SYNC_CREATE)
        self.connect("notify::current-element", self._on_current_element_changed)

    def _on_current_element_changed(self, _pathbar, _value):
        self.clear_pathbar()
        self.build_button_list()
        self.build_pathbar()

    def build_button_list(self):
        current_element = self.current_element
        button = self.add_button(current_element)
        self.buttons.insert(0, button)

        while not current_element.is_root_group:
            current_element = current_element.parentgroup
            button = self.add_button(current_element)
            self.buttons.insert(0, button)

    def build_pathbar(self):
        for button in self.buttons:
            self.add(button)
            if not button == self.buttons[-1]:
                self.add_separator_label()

        self.buttons[-1].set_active_style()
        self.show_all()

    def add_separator_label(self):
        separator_label = PathbarSeparator(self.unlocked_database)
        self.add(separator_label)

    def add_button(self, element: SafeElement) -> PathbarButton:
        pathbar_button = PathbarButton(element)
        pathbar_button.connect("clicked", self.on_pathbar_button_clicked)

        return pathbar_button

    def clear_pathbar(self):
        self.buttons.remove_all()
        for widget in self.get_children():
            self.remove(widget)

    def on_pathbar_button_clicked(self, pathbar_button):
        self.unlocked_database.start_database_lock_timer()
        pathbar_button_elem = pathbar_button.element
        current_elem_uuid = self.unlocked_database.current_element.uuid

        if pathbar_button_elem.uuid != current_elem_uuid:
            is_group = pathbar_button.is_group
            if is_group:
                self.unlocked_database.show_browser_page(pathbar_button_elem)


class PathbarSeparator(Gtk.Label):
    def __init__(self, unlocked_database):
        super().__init__()

        self.unlocked_database = unlocked_database

        self.set_text("/")

        context = self.get_style_context()
        if not self.unlocked_database.props.selection_mode:
            context.add_class("dim-label")

        self.unlocked_database.connect("notify::selection-mode", self._on_selection_mode_changed)

    def _on_selection_mode_changed(
        self, unlocked_database: UnlockedDatabase, _value: GObject.ParamSpecBoolean
    ) -> None:
        context = self.get_style_context()
        if unlocked_database.props.selection_mode:
            context.remove_class("dim-label")
        else:
            context.add_class("dim-label")
