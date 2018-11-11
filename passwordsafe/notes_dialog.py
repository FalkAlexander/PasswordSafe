from gi.repository import Gtk


class NotesDialog():
    dialog = NotImplemented

    unlocked_database = NotImplemented
    builder = NotImplemented

    search_button = NotImplemented
    search_bar = NotImplemented
    search_entry = NotImplemented

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
        self.dialog.connect("delete-event", self.on_dialog_quit)

        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_entry_uuid_from_entry_object(self.unlocked_database.current_group))
        scrolled_page.notes_dialog_value_entry = self.builder.get_object("value_entry")
        scrolled_page.notes_dialog_value_entry.get_buffer().connect("changed", self.on_value_entry_changed)

        self.builder.get_object("copy_button").connect("clicked", self.on_copy_button_clicked)
        self.builder.get_object("close_button").connect("clicked", self.on_close_button_clicked)

        # Search
        self.search_button = self.builder.get_object("search_button")
        self.search_bar = self.builder.get_object("search_bar")
        self.search_entry = self.builder.get_object("search_entry")

        self.search_button.connect("toggled", self.on_search_button_toggled)

        self.update_value_entry()

    def update_value_entry(self):
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_entry_uuid_from_entry_object(self.unlocked_database.current_group))

        buffer_text = scrolled_page.notes_property_value_entry.get_buffer().get_text(
            scrolled_page.notes_property_value_entry.get_buffer().get_start_iter(),
            scrolled_page.notes_property_value_entry.get_buffer().get_end_iter(),
            False)
        scrolled_page.notes_dialog_value_entry.get_buffer().set_text(buffer_text)

    #
    # Events
    #

    def on_value_entry_changed(self, widget):
        self.unlocked_database.start_database_lock_timer()
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_entry_uuid_from_entry_object(self.unlocked_database.current_group))

        scrolled_page.notes_property_value_entry.get_buffer().set_text(
            widget.get_text(widget.get_start_iter(), widget.get_end_iter(), False)
        )

    def on_copy_button_clicked(self, button):
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_entry_uuid_from_entry_object(self.unlocked_database.current_group))

        self.unlocked_database.send_to_clipboard(
            scrolled_page.notes_dialog_value_entry.get_buffer().get_text(
                scrolled_page.notes_dialog_value_entry.get_buffer().get_start_iter(),
                scrolled_page.notes_dialog_value_entry.get_buffer().get_end_iter(),
                False)
            )

    def on_close_button_clicked(self, button):
        self.dialog.destroy()

    def on_search_button_toggled(self, button):
        self.toggle_search_bar()

    def toggle_search_bar(self):
        if self.search_bar.get_search_mode() is True:
            self.search_bar.set_search_mode(False)
            self.search_button.set_active(False)
        else:
            self.search_bar.set_search_mode(True)
            self.search_button.set_active(True)

    #
    # Tools
    #

    def on_dialog_quit(self, window, event):
        self.unlocked_database.notes_dialog = NotImplemented
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_entry_uuid_from_entry_object(self.unlocked_database.current_group))
        scrolled_page.notes_dialog_value_entry = NotImplemented

