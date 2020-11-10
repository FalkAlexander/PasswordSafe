# SPDX-License-Identifier: GPL-3.0-only
from gettext import gettext as _
from gi.repository import Gtk


class GroupRow(Gtk.ListBoxRow):
    unlocked_database = NotImplemented
    group_uuid = NotImplemented
    label = NotImplemented
    selection_checkbox = NotImplemented
    checkbox_box = NotImplemented
    edit_button = NotImplemented
    type = "GroupRow"

    def __init__(self, unlocked_database, dbm, group):
        Gtk.ListBoxRow.__init__(self)
        self.set_name("GroupRow")

        self.unlocked_database = unlocked_database

        self.group_uuid = group.uuid
        self.label = dbm.get_group_name(group)

        self.assemble_group_row()

    def assemble_group_row(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_database.ui")
        group_event_box = builder.get_object("group_event_box")
        group_event_box.connect("button-press-event", self.unlocked_database.on_group_row_button_pressed)

        group_name_label = builder.get_object("group_name_label")

        if self.label:
            group_name_label.set_text(self.label)
        else:
            group_name_label.set_markup("<span font-style=\"italic\">" + _("No group title specified") + "</span>")

        self.add(group_event_box)
        self.show_all()

        # Selection Mode Checkboxes
        self.checkbox_box = builder.get_object("group_checkbox_box")
        self.selection_checkbox = builder.get_object("selection_checkbox_group")
        self.selection_checkbox.connect("toggled", self.on_selection_checkbox_toggled)
        if self.unlocked_database.selection_ui.selection_mode_active is True:
            self.checkbox_box.show_all()
        else:
            self.checkbox_box.hide()

        # Edit Button
        self.edit_button = builder.get_object("group_edit_button")
        self.edit_button.connect("clicked", self.unlocked_database.on_group_edit_button_clicked)

    def get_uuid(self):
        return self.group_uuid

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label

    def get_type(self):
        return self.type

    def on_selection_checkbox_toggled(self, _widget):
        if self.selection_checkbox.get_active() is True:
            if self not in self.unlocked_database.selection_ui.groups_selected:
                self.unlocked_database.selection_ui.groups_selected.append(self)
        else:
            if self in self.unlocked_database.selection_ui.groups_selected:
                self.unlocked_database.selection_ui.groups_selected.remove(self)

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
