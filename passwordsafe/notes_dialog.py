# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk


class NotesDialog():
    # pylint: disable=too-many-instance-attributes

    dialog = NotImplemented

    unlocked_database = NotImplemented
    builder = NotImplemented
    accelerators = NotImplemented

    search_button = NotImplemented
    search_bar = NotImplemented
    search_entry = NotImplemented

    search_stopped = False

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

        self.unlocked_database.notes_dialog = self.dialog
        self.dialog.connect("delete-event", self.on_dialog_quit)

        scrolled_page = self.unlocked_database.get_current_page()
        scrolled_page.notes_dialog_value_entry = self.builder.get_object("value_entry")
        scrolled_page.notes_dialog_value_entry.get_buffer().connect("changed", self.on_value_entry_changed)

        self.builder.get_object("copy_button").connect("clicked", self.on_copy_button_clicked)

        # Search
        self.search_button = self.builder.get_object("search_button")
        self.search_bar = self.builder.get_object("search_bar")
        self.search_entry = self.builder.get_object("search_entry")

        self.search_button.connect("toggled", self.on_search_button_toggled)
        self.search_entry.connect("search-changed", self.on_search_entry_changed)
        self.search_entry.connect("stop-search", self.on_search_stopped)

        # Tags
        self.tag = scrolled_page.notes_dialog_value_entry.get_buffer().create_tag("found", background="yellow")

        # Accelerators
        self.accelerators = Gtk.AccelGroup()
        self.dialog.add_accel_group(self.accelerators)
        self.add_search_accelerator()

        self.update_value_entry()

    def add_search_accelerator(self):
        key, mod = Gtk.accelerator_parse("<Control>f")
        self.search_button.add_accelerator("clicked", self.accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

    def update_value_entry(self):
        scrolled_page = self.unlocked_database.get_current_page()

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
        scrolled_page = self.unlocked_database.get_current_page()

        scrolled_page.notes_property_value_entry.get_buffer().set_text(
            widget.get_text(widget.get_start_iter(), widget.get_end_iter(), False)
        )

    def on_copy_button_clicked(self, _button):
        scrolled_page = self.unlocked_database.get_current_page()

        self.unlocked_database.send_to_clipboard(
            scrolled_page.notes_dialog_value_entry.get_buffer().get_text(
                scrolled_page.notes_dialog_value_entry.get_buffer().get_start_iter(),
                scrolled_page.notes_dialog_value_entry.get_buffer().get_end_iter(),
                False)
        )

    def on_search_button_toggled(self, _button):
        if self.search_stopped is True:
            return
        self.toggle_search_bar()

    def toggle_search_bar(self):
        if self.search_bar.get_search_mode() is True:
            self.search_bar.set_search_mode(False)
        else:
            self.search_bar.set_search_mode(True)

    def on_search_entry_changed(self, entry):
        scrolled_page = self.unlocked_database.get_current_page()
        notes_buffer = scrolled_page.notes_dialog_value_entry.get_buffer()

        scrolled_page.notes_dialog_value_entry.get_buffer().remove_all_tags(
            scrolled_page.notes_dialog_value_entry.get_buffer().get_start_iter(),
            scrolled_page.notes_dialog_value_entry.get_buffer().get_end_iter()
        )

        start = notes_buffer.get_start_iter()
        if entry.get_text():
            self.do_search(notes_buffer, entry.get_text(), start)

    def on_search_stopped(self, _entry):
        self.search_stopped = True
        self.search_button.set_active(False)
        self.search_stopped = False

    #
    # Tools
    #

    def do_search(self, notes_buffer, keyword, start):
        end = notes_buffer.get_end_iter()
        match = start.forward_search(keyword, Gtk.TextSearchFlags.CASE_INSENSITIVE, end)

        if match is not None:
            match_start, match_end = match
            notes_buffer.apply_tag(self.tag, match_start, match_end)
            self.do_search(notes_buffer, keyword, match_end)

    def on_dialog_quit(self, _window, _event):
        self.unlocked_database.notes_dialog = NotImplemented
        scrolled_page = self.unlocked_database.get_current_page()
        scrolled_page.notes_dialog_value_entry = NotImplemented
