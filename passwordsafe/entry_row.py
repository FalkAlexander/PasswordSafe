# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations
from gettext import gettext as _
from uuid import UUID
from typing import Optional
from gi.repository import Gtk

import passwordsafe.config_manager
import passwordsafe.icon
from passwordsafe.color_widget import Color


class EntryRow(Gtk.ListBoxRow):
    builder = Gtk.Builder()

    selection_checkbox = NotImplemented
    color = NotImplemented
    type = "EntryRow"

    targets = NotImplemented

    def __init__(self, unlocked_database, dbm, entry):
        Gtk.ListBoxRow.__init__(self)
        self.set_name("EntryRow")

        self.unlocked_database = unlocked_database
        self.database_manager = dbm

        self.entry_uuid = entry.uuid
        self.icon: Optional[int] = dbm.get_icon(entry)
        self.label: str = entry.title or ""
        self.color = dbm.get_entry_color(entry)
        self.username: str = entry.username or ""
        if self.username.startswith("{REF:U"):
            # Loopup reference and put in the "real" username
            uuid = UUID(self.unlocked_database.reference_to_hex_uuid(self.username))
            self.username = self.database_manager.get_entry_username(uuid)

        self.assemble_entry_row()

    def assemble_entry_row(self):
        self.builder.add_from_resource("/org/gnome/PasswordSafe/unlocked_database.ui")
        entry_event_box = self.builder.get_object("entry_event_box")
        entry_event_box.connect("button-press-event", self.unlocked_database.on_entry_row_button_pressed)

        entry_icon = self.builder.get_object("entry_icon")
        entry_name_label = self.builder.get_object("entry_name_label")
        entry_subtitle_label = self.builder.get_object("entry_subtitle_label")
        entry_copy_button = self.builder.get_object("entry_copy_button")
        entry_color_button = self.builder.get_object("entry_color_button")

        # Icon
        icon_name: str = passwordsafe.icon.get_icon_name(self.icon)
        entry_icon.set_from_icon_name(icon_name, 20)
        # Title/Name
        if self.label:
            entry_name_label.set_text(self.label)
        else:
            entry_name_label.set_markup("<span font-style=\"italic\">" + _("Title not specified") + "</span>")

        # Subtitle
        if self.username:
            entry_subtitle_label.set_text(self.username)
        else:
            entry_subtitle_label.set_markup("<span font-style=\"italic\">" + _("No username specified") + "</span>")

        entry_copy_button.connect("clicked", self.on_entry_copy_button_clicked)

        # Color Button
        entry_color_button.set_name(self.color + "List")
        image = entry_color_button.get_children()[0]
        image_style = image.get_style_context()
        if self.color != Color.NONE.value:
            image_style.add_class("BrightIcon")
        else:
            image_style.add_class("DarkIcon")

        self.add(entry_event_box)
        self.show()

        # Selection Mode Checkboxes
        self.selection_checkbox = self.builder.get_object("selection_checkbox_entry")
        self.selection_checkbox.connect("toggled", self.on_selection_checkbox_toggled)
        if self.unlocked_database.selection_ui.selection_mode_active is True:
            self.selection_checkbox.show()

    def get_uuid(self):
        return self.entry_uuid

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label

    def get_type(self):
        return self.type

    def on_selection_checkbox_toggled(self, _widget):
        if self.selection_checkbox.get_active() is True:
            if self not in self.unlocked_database.selection_ui.entries_selected:
                self.unlocked_database.selection_ui.entries_selected.append(self)
        else:
            if self in self.unlocked_database.selection_ui.entries_selected:
                self.unlocked_database.selection_ui.entries_selected.remove(self)

        if (self.unlocked_database.selection_ui.entries_selected
                or self.unlocked_database.selection_ui.groups_selected):
            self.unlocked_database.builder.get_object("selection_cut_button").set_sensitive(True)
            self.unlocked_database.builder.get_object("selection_delete_button").set_sensitive(True)
        else:
            self.unlocked_database.builder.get_object("selection_cut_button").set_sensitive(False)
            self.unlocked_database.builder.get_object("selection_delete_button").set_sensitive(False)

        if self.unlocked_database.selection_ui.cut_mode is False:
            self.unlocked_database.selection_ui.entries_cut.clear()
            self.unlocked_database.selection_ui.groups_cut.clear()
            self.unlocked_database.builder.get_object("selection_cut_button").get_children()[0].set_from_icon_name("edit-cut-symbolic", Gtk.IconSize.BUTTON)
            # self.unlocked_database.selection_ui.cut_mode is True

    def on_entry_copy_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(self.database_manager.get_entry_password(self.entry_uuid))

    def update_color(self, color):
        self.color = color

    def get_color(self):
        return self.color
