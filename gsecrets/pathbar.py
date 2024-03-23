# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gio, GObject, Gtk

from gsecrets.pathbar_button import PathbarButton
from gsecrets.safe_element import SafeElement


class Pathbar(Gtk.Box):
    """Pathbar provides a breadcrumb-style Box with the current hierarchy."""

    buttons = Gio.ListStore.new(PathbarButton)

    current_element = GObject.Property(type=SafeElement)

    def __init__(self, unlocked_database):
        super().__init__()

        self.set_name("Pathbar")
        self.unlocked_database = unlocked_database
        self.database_manager = unlocked_database.database_manager

        unlocked_database.bind_property(
            "current-element",
            self,
            "current-element",
            GObject.BindingFlags.SYNC_CREATE,
        )
        self.connect("notify::current-element", self._on_current_element_changed)
        self.setup_widgets()

    def setup_widgets(self):
        self.clear_pathbar()
        self.build_button_list()
        self.build_pathbar()

    def _on_current_element_changed(self, _pathbar, _value):
        self.setup_widgets()

    def build_button_list(self):
        current_element = self.current_element
        button = self.add_button(current_element)
        self.buttons.insert(0, button)

        # pylint: disable=no-member
        while not current_element.is_root_group:
            # pylint: disable=no-member
            current_element = current_element.parentgroup
            button = self.add_button(current_element)
            self.buttons.insert(0, button)

    def build_pathbar(self):
        for button in self.buttons:
            self.append(button)
            if button != self.buttons[-1]:
                self.add_separator_label()

        self.buttons[-1].set_active_style()

    def add_separator_label(self):
        separator_label = Gtk.Label.new("/")
        self.append(separator_label)

    def add_button(self, element: SafeElement) -> PathbarButton:
        pathbar_button = PathbarButton(element)
        pathbar_button.connect("clicked", self.on_pathbar_button_clicked)

        return pathbar_button

    def clear_pathbar(self):
        self.buttons.remove_all()
        while self.get_first_child():
            self.remove(self.get_first_child())

    def on_pathbar_button_clicked(self, pathbar_button):
        self.unlocked_database.start_database_lock_timer()
        pathbar_button_elem = pathbar_button.element
        current_elem_uuid = self.unlocked_database.current_element.uuid

        if pathbar_button_elem.uuid != current_elem_uuid:
            is_group = pathbar_button.is_group
            if is_group:
                self.unlocked_database.show_browser_page(pathbar_button_elem)
