# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gtk, Gdk, Handy


class NotesDialog:
    def __init__(self, unlocked_database):
        self.__builder = Gtk.Builder()
        self.__builder.add_from_resource("/org/gnome/PasswordSafe/notes_dialog.ui")

        self.__unlocked_database = unlocked_database
        self.__dialog = self.__builder.get_object("notes_detached_dialog")
        self.__scrolled_page = self.__unlocked_database.get_current_page()
        self.__accelerators = Gtk.AccelGroup()
        self.__search_stopped = False

        self.__notes_buffer = self.__builder.get_object("value_entry").get_buffer()
        self.__tag = self.__notes_buffer.create_tag("found", background="yellow")

        self.__setup_widgets()
        self.__setup_signals()
        self.__setup_accelerators()

    def present(self):
        self.__dialog.present()

    def __setup_signals(self):
        self.__unlocked_database.database_manager.connect("notify::locked", self.__on_locked)
        self.__builder.get_object("copy_button").connect("clicked", self.__on_copy_button_clicked)

        # Search
        self.__search_button = self.__builder.get_object("search_button")
        self.__search_bar = self.__builder.get_object("search_bar")
        self.__search_entry = self.__builder.get_object("search_entry")

        self.__search_button.connect("toggled", self.__on_search_button_toggled)
        self.__search_entry.connect("search-changed", self.__on_search_entry_changed)
        self.__search_entry.connect("stop-search", self.__on_search_stopped)

        self.__notes_buffer.connect("changed", self.__on_value_entry_changed)

    def __setup_widgets(self):
        # Dialog
        self.__dialog.set_modal(True)
        self.__dialog.set_transient_for(self.__unlocked_database.window)
        self.__dialog.connect("key-press-event", self.__on_key_press_event)

        self.__update_value_entry()

    def __setup_accelerators(self):
        self.__dialog.add_accel_group(self.__accelerators)
        self.__add_search_accelerator()
        # TODO Add accelerator for save on "<primary>s"

    def __add_search_accelerator(self):
        key, mod = Gtk.accelerator_parse("<primary>f")
        self.__search_button.add_accelerator(
            "clicked", self.__accelerators, key, mod, Gtk.AccelFlags.VISIBLE
        )

    def __update_value_entry(self):
        scrolled_page = self.__scrolled_page
        scrolled_page_buffer = scrolled_page.notes_property_value_entry.get_buffer()

        buffer_text = scrolled_page_buffer.get_text(
            scrolled_page_buffer.get_start_iter(),
            scrolled_page_buffer.get_end_iter(),
            False,
        )
        self.__notes_buffer.set_text(buffer_text)

    #
    # Events
    #

    def __on_value_entry_changed(self, widget):
        self.__unlocked_database.start_database_lock_timer()
        scrolled_page = self.__scrolled_page
        scrolled_page_buffer = scrolled_page.notes_property_value_entry.get_buffer()

        scrolled_page_buffer.set_text(
            widget.get_text(widget.get_start_iter(), widget.get_end_iter(), False)
        )

    def __on_copy_button_clicked(self, _button):
        notes_buffer = self.__notes_buffer

        self.__unlocked_database.send_to_clipboard(
            notes_buffer.get_text(
                notes_buffer.get_start_iter(), notes_buffer.get_end_iter(), False
            )
        )

    def __on_search_button_toggled(self, _button):
        if self.__search_stopped is True:
            return
        self.__toggle_search_bar()

    def __toggle_search_bar(self):
        if self.__search_bar.get_search_mode() is True:
            self.__search_bar.set_search_mode(False)
        else:
            self.__search_bar.set_search_mode(True)

    def __on_search_entry_changed(self, entry):
        notes_buffer = self.__notes_buffer

        notes_buffer.remove_all_tags(
            notes_buffer.get_start_iter(), notes_buffer.get_end_iter()
        )

        start = notes_buffer.get_start_iter()
        if entry.get_text():
            self.__do_search(notes_buffer, entry.get_text(), start)

    def __on_search_stopped(self, _entry):
        self.__search_stopped = True
        self.__search_button.set_active(False)
        self.__search_stopped = False

    #
    # Tools
    #

    def __do_search(self, notes_buffer, keyword, start):
        end = notes_buffer.get_end_iter()
        match = start.forward_search(keyword, Gtk.TextSearchFlags.CASE_INSENSITIVE, end)

        if match is not None:
            match_start, match_end = match
            notes_buffer.apply_tag(self.__tag, match_start, match_end)
            self.__do_search(notes_buffer, keyword, match_end)

    def __on_key_press_event(self, _window: Handy.Window, event: Gtk.Event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            if not self.__search_bar.get_search_mode():
                self.__dialog.close()
                return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.__dialog.close()
