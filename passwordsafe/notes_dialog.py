# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Adw, GObject, Gtk


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/notes_dialog.ui")
class NotesDialog(Adw.Window):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "NotesDialog"

    _search_bar = Gtk.Template.Child()
    _search_button = Gtk.Template.Child()
    _value_entry = Gtk.Template.Child()

    def __init__(self, unlocked_database, safe_entry):
        super().__init__()

        self.__unlocked_database = unlocked_database
        self.__safe_entry = safe_entry
        self.__search_stopped = False

        self.__notes_buffer = self._value_entry.get_buffer()
        # TODO Revisit the choice of color used as it might look bad
        # other themes.
        self.__tag = self.__notes_buffer.create_tag("found", background="yellow")

        self.__setup_widgets()
        self.__setup_signals()

    def __setup_signals(self):
        self.__unlocked_database.database_manager.connect(
            "notify::locked", self.__on_locked
        )
        # Bind text to the corresponding safe entry.
        self.__safe_entry.bind_property(
            "notes",
            self.__notes_buffer,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

    def __setup_widgets(self):
        self.set_modal(True)
        self.set_transient_for(self.__unlocked_database.window)

    #
    # Events
    #

    @Gtk.Template.Callback()
    def _on_copy_button_clicked(self, _button):
        notes_buffer = self.__notes_buffer

        self.__unlocked_database.send_to_clipboard(
            notes_buffer.get_text(
                notes_buffer.get_start_iter(), notes_buffer.get_end_iter(), False
            )
        )

    @Gtk.Template.Callback()
    def _on_search_button_toggled(self, _button):
        self.__unlocked_database.start_database_lock_timer()

        if self.__search_stopped is True:
            return
        self.__toggle_search_bar()

    def __toggle_search_bar(self):
        if self._search_bar.get_search_mode() is True:
            self._search_bar.set_search_mode(False)
        else:
            self._search_bar.set_search_mode(True)

    @Gtk.Template.Callback()
    def _on_search_entry_changed(self, entry):
        self.__unlocked_database.start_database_lock_timer()

        notes_buffer = self.__notes_buffer

        notes_buffer.remove_all_tags(
            notes_buffer.get_start_iter(), notes_buffer.get_end_iter()
        )

        start = notes_buffer.get_start_iter()
        if entry.get_text():
            self.__do_search(notes_buffer, entry.get_text(), start)

    @Gtk.Template.Callback()
    def _on_search_stopped(self, _entry):
        self.__search_stopped = True
        self._search_button.set_active(False)
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

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.close()
