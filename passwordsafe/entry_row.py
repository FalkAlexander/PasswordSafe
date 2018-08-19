from gi.repository import Gtk, Gdk
import gi
import passwordsafe.icon
gi.require_version('Gtk', '3.0')


class EntryRow(Gtk.ListBoxRow):
    unlocked_database = NotImplemented
    database_manager = NotImplemented
    entry_uuid = NotImplemented
    icon = NotImplemented
    label = NotImplemented
    password = NotImplemented
    changed = False
    selection_checkbox = NotImplemented
    color = NotImplemented
    type = "EntryRow"

    targets = NotImplemented

    def __init__(self, unlocked_database, dbm, entry):
        print("e1")
        Gtk.ListBoxRow.__init__(self)
        print("e2")
        self.set_name("EntryRow")
        print("e3")

        self.unlocked_database = unlocked_database
        print("e4")
        self.database_manager = dbm
        print("e5")

        self.entry_uuid = dbm.get_entry_uuid_from_entry_object(entry)
        print("e6")
        self.icon = dbm.get_entry_icon_from_entry_object(entry)
        print("e7")
        self.label = dbm.get_entry_name_from_entry_object(entry)
        print("e8")
        self.password = dbm.get_entry_password_from_entry_object(entry)
        print("e9")
        self.color = dbm.get_entry_color_from_entry_uuid(self.entry_uuid)
        print("e10")

        self.assemble_entry_row()
        print("e11")

    def assemble_entry_row(self):
        print("e12")
        builder = Gtk.Builder()
        print("e13")
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_database.ui")
        print("e14")
        entry_event_box = builder.get_object("entry_event_box")
        print("e15")
        entry_event_box.connect("button-press-event", self.unlocked_database.on_entry_row_button_pressed)
        print("e16")

        entry_icon = builder.get_object("entry_icon")
        print("e17")
        entry_name_label = builder.get_object("entry_name_label")
        print("e18")
        entry_subtitle_label = builder.get_object("entry_subtitle_label")
        print("e19")
        entry_password_input = builder.get_object("entry_password_input")
        print("e20")
        entry_color_button = builder.get_object("entry_color_button")
        print("e21")

        if self.unlocked_database.selection_mode is True:
            print("e22")
            entry_checkbox_box = builder.get_object("entry_checkbox_box")
            print("e23")
            self.selection_checkbox = builder.get_object("selection_checkbox")
            print("e24")
            self.selection_checkbox.connect("toggled", self.on_selection_checkbox_toggled)
            print("e25")
            entry_checkbox_box.add(self.selection_checkbox)
            print("e26")

        # Icon
        print("e27")
        entry_icon.set_from_icon_name(passwordsafe.icon.get_icon(self.icon), 20)
        print("e28")

        # Title/Name
        print("e29")
        if self.database_manager.has_entry_name(self.entry_uuid) is True and self.label is not "":
            print("e30")
            entry_name_label.set_text(self.label)
            print("e31")
        else:
            print("e32")
            entry_name_label.set_markup("<span font-style=\"italic\">" + "Title not specified" + "</span>")
            print("e33")

        # Subtitle
        print("e34")
        subtitle = self.database_manager.get_entry_username_from_entry_uuid(self.entry_uuid)
        print("e35")
        if (self.database_manager.has_entry_username(self.entry_uuid) is True and subtitle is not ""):
            print("e36")
            entry_subtitle_label.set_text(
                self.database_manager.get_entry_username_from_entry_uuid(
                    self.entry_uuid))
            print("e37")
        else:
            print("e38")
            entry_subtitle_label.set_markup("<span font-style=\"italic\">" + "No username specified" + "</span>")
            print("e39")

        # Password
        print("e40")
        if self.database_manager.has_entry_password(self.entry_uuid) is True and self.password is not "":
            print("e41")
            entry_password_input.set_text(self.password)
            print("e42")
        else:
            print("e43")
            entry_password_input.set_text("")
            print("e44")

        print("e45")
        entry_password_input.connect("icon-press", self.unlocked_database.on_copy_secondary_button_clicked)
        print("e46")

        # Color Button
        print("e47")
        entry_color_button.set_name(self.color + "List")
        print("e48")
        if self.color != "NoneColorButton":
            print("e49")
            image = entry_color_button.get_children()[0]
            print("e50")
            image.set_name("BrightIcon")
            print("e51")
        else:
            print("e52")
            image = entry_color_button.get_children()[0]
            print("e53")
            image.set_name("DarkIcon")
            print("e54")

        print("e55")
        self.add(entry_event_box)
        print("e56")
        self.show_all()
        print("e57")

    def get_entry_uuid(self):
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

    def set_changed(self, bool):
        self.changed = bool

    def get_changed(self):
        return self.changed

    def on_selection_checkbox_toggled(self, widget):
        if self.selection_checkbox.get_active() is True:
            if self not in self.unlocked_database.entries_selected:
                self.unlocked_database.entries_selected.append(self)
        else:
            if self in self.unlocked_database.entries_selected:
                self.unlocked_database.entries_selected.remove(self)

        if len(self.unlocked_database.entries_selected) > 0 or len(self.unlocked_database.groups_selected) > 0:
            self.unlocked_database.builder.get_object("selection_cut_button").set_sensitive(True)
            self.unlocked_database.builder.get_object("selection_delete_button").set_sensitive(True)
        else:
            self.unlocked_database.builder.get_object("selection_cut_button").set_sensitive(False)
            self.unlocked_database.builder.get_object("selection_delete_button").set_sensitive(False)

    def update_color(self, color):
        self.color = color

    def get_color(self):
        return self.color
