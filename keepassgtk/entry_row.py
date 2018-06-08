from gi.repository import Gtk, Gdk
import gi
import keepassgtk.icon
gi.require_version('Gtk', '3.0')


class EntryRow(Gtk.ListBoxRow):
    unlocked_database = NotImplemented
    database_manager = NotImplemented
    entry_uuid = NotImplemented
    icon = NotImplemented
    label = NotImplemented
    password = NotImplemented
    changed = False
    type = "EntryRow"

    def __init__(self, unlocked_database, dbm, entry):
        Gtk.ListBoxRow.__init__(self)
        self.set_name("EntryRow")

        self.unlocked_database = unlocked_database
        self.database_manager = dbm

        self.entry_uuid = dbm.get_entry_uuid_from_entry_object(entry)
        self.icon = dbm.get_entry_icon_from_entry_object(entry)
        self.label = dbm.get_entry_name_from_entry_object(entry)
        self.password = dbm.get_entry_password_from_entry_object(entry)

        self.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.MOVE)
        self.connect("drag-begin", self.on_drag_begin)

        self.assemble_entry_row()

    def on_drag_begin(self, source, drag_context):
        print("drag begin")

    def assemble_entry_row(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/run/terminal/KeepassGtk/unlocked_database.ui")
        entry_event_box = builder.get_object("entry_event_box")
        entry_event_box.connect("button-press-event", self.unlocked_database.on_entry_row_button_pressed)

        entry_icon = builder.get_object("entry_icon")
        entry_name_label = builder.get_object("entry_name_label")
        entry_subtitle_label = builder.get_object("entry_subtitle_label")
        entry_password_input = builder.get_object("entry_password_input")

        # Icon
        entry_icon.set_from_icon_name(keepassgtk.icon.get_icon(self.icon), 20)

        # Title/Name
        if self.database_manager.has_entry_name(self.entry_uuid) is True and self.label is not "":
            entry_name_label.set_text(self.label)
        else:
            entry_name_label.set_markup("<span font-style=\"italic\">" + "Title not specified" + "</span>")

        # Subtitle
        subtitle = self.database_manager.get_entry_username_from_entry_uuid(self.entry_uuid)
        if (self.database_manager.has_entry_username(self.entry_uuid) is True and subtitle is not ""):
            entry_subtitle_label.set_text(
                self.database_manager.get_entry_username_from_entry_uuid(
                    self.entry_uuid))
        else:
            entry_subtitle_label.set_markup("<span font-style=\"italic\">" + "No username specified" + "</span>")

        # Password
        if self.database_manager.has_entry_password(self.entry_uuid) is True and self.password is not "":
            entry_password_input.set_text(self.password)
        else:
            entry_password_input.set_text("")

        entry_password_input.connect("icon-press", self.unlocked_database.on_copy_secondary_button_clicked)

        self.add(entry_event_box)
        self.show_all()

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
