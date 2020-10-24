from gettext import gettext as _
from gi.repository import Gtk
from uuid import UUID

from passwordsafe.color_widget import Color
import passwordsafe.config_manager
import passwordsafe.icon


class EntryRow(Gtk.ListBoxRow):
    unlocked_database = NotImplemented
    database_manager = NotImplemented
    entry_uuid = NotImplemented
    icon = NotImplemented
    label = NotImplemented
    password = NotImplemented
    changed = False
    selection_checkbox = NotImplemented
    checkbox_box = NotImplemented
    color = NotImplemented
    type = "EntryRow"

    targets = NotImplemented

    def __init__(self, unlocked_database, dbm, entry):
        Gtk.ListBoxRow.__init__(self)
        self.set_name("EntryRow")

        self.unlocked_database = unlocked_database
        self.database_manager = dbm

        self.entry_uuid = dbm.get_entry_uuid_from_entry_object(entry)
        self.icon = dbm.get_entry_icon_from_entry_object(entry)
        self.label = dbm.get_entry_name_from_entry_object(entry)
        self.password = dbm.get_entry_password_from_entry_object(entry)
        self.color = dbm.get_entry_color_from_entry_uuid(self.entry_uuid)

        self.assemble_entry_row()

    def assemble_entry_row(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_database.ui")
        entry_event_box = builder.get_object("entry_event_box")
        entry_event_box.connect("button-press-event", self.unlocked_database.on_entry_row_button_pressed)

        entry_icon = builder.get_object("entry_icon")
        entry_name_label = builder.get_object("entry_name_label")
        entry_subtitle_label = builder.get_object("entry_subtitle_label")
        entry_copy_button = builder.get_object("entry_copy_button")
        entry_color_button = builder.get_object("entry_color_button")

        # Icon
        if self.icon is not None:
            if int(self.icon) >= 0 and int(self.icon) <= 68 and self.icon:
                entry_icon.set_from_icon_name(passwordsafe.icon.get_icon(self.icon), 20)
            else:
                entry_icon.set_from_icon_name(passwordsafe.icon.get_icon("0"), 20)
        else:
            entry_icon.set_from_icon_name(passwordsafe.icon.get_icon("0"), 20)

        # Title/Name
        if self.database_manager.has_entry_name(self.entry_uuid) and self.label:
            entry_name_label.set_text(self.label)
        else:
            entry_name_label.set_markup("<span font-style=\"italic\">" + _("Title not specified") + "</span>")

        # Subtitle
        subtitle = self.database_manager.get_entry_username_from_entry_uuid(self.entry_uuid)
        if (self.database_manager.has_entry_username(self.entry_uuid) and subtitle):
            username = self.database_manager.get_entry_username_from_entry_uuid(self.entry_uuid)
            if username.startswith("{REF:U"):
                uuid = UUID(
                    self.unlocked_database.reference_to_hex_uuid(username))
                username = self.database_manager.get_entry_username_from_entry_uuid(uuid)
                entry_subtitle_label.set_text(username)
            else:
                entry_subtitle_label.set_text(username)
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
        self.show_all()

        # Selection Mode Checkboxes
        self.checkbox_box = builder.get_object("entry_checkbox_box")
        self.selection_checkbox = builder.get_object("selection_checkbox_entry")
        self.selection_checkbox.connect("toggled", self.on_selection_checkbox_toggled)
        if self.unlocked_database.selection_ui.selection_mode_active is True:
            self.checkbox_box.show_all()
        else:
            self.checkbox_box.hide()

    def get_uuid(self):
        return self.entry_uuid

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label

    def update_password(self):
        self.password = self.database_manager.get_entry_password(
            self.entry_uuid)

    def get_type(self):
        return self.type

    def set_changed(self, boolean):
        self.changed = boolean

    def get_changed(self):
        return self.changed

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
        self.unlocked_database.send_to_clipboard(self.database_manager.get_entry_password_from_entry_uuid(self.entry_uuid))

    def update_color(self, color):
        self.color = color

    def get_color(self):
        return self.color
