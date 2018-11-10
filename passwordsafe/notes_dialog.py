from gi.repository import Gtk


class NotesDialog():
    dialog = NotImplemented

    unlocked_database = NotImplemented
    builder = NotImplemented

    value_entry = NotImplemented

    def __init__(self, unlocked_database):
        self.unlocked_database = unlocked_database
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/notes_dialog.ui")

        self.assemble_dialog()

    def assemble_dialog(self):
        self.dialog = self.builder.get_object("notes_detached_dialog")

        # Dialog
        self.dialog.set_modal(True)
        self.dialog.set_transient_for(self.unlocked_database.window)
        self.dialog.present()

        self.unlocked_database.references_dialog = self.dialog

        self.value_entry = self.builder.get_object("value_entry")
        self.value_entry.get_buffer().connect("changed", self.on_value_entry_changed)
        self.builder.get_object("copy_button").connect("clicked", self.on_copy_button_clicked)
        self.builder.get_object("close_button").connect("clicked", self.on_close_button_clicked)

        self.update_value_entry()

    def update_value_entry(self):
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_entry_uuid_from_entry_object(self.unlocked_database.current_group))

        buffer_text = scrolled_page.notes_property_value_entry.get_buffer().get_text(
            scrolled_page.notes_property_value_entry.get_buffer().get_start_iter(),
            scrolled_page.notes_property_value_entry.get_buffer().get_end_iter(),
            False)
        self.value_entry.get_buffer().set_text(buffer_text)

    #
    # Events
    #
    def on_value_entry_changed(self, widget):
        self.unlocked_database.start_database_lock_timer()
        entry_uuid = self.unlocked_database.database_manager.get_entry_uuid_from_entry_object(self.unlocked_database.current_group)
        self.unlocked_database.database_manager.set_entry_notes(entry_uuid, widget.get_text(widget.get_start_iter(), widget.get_end_iter(), False))

    def on_copy_button_clicked(self, button):
        self.unlocked_database.send_to_clipboard(
            self.value_entry.get_buffer().get_text(
                self.value_entry.get_buffer().get_start_iter(),
                self.value_entry.get_buffer().get_end_iter(),
                False)
            )

    def on_close_button_clicked(self, button):
        self.dialog.destroy()

