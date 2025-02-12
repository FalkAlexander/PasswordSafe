# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk, GtkSource


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/notes_dialog.ui")
class NotesDialog(Adw.Dialog):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "NotesDialog"

    _search_bar = Gtk.Template.Child()
    _search_button = Gtk.Template.Child()
    _toast_overlay = Gtk.Template.Child()
    _value_entry = Gtk.Template.Child()

    clipboard_timer_handler: None | int = None

    def __init__(self, unlocked_database, safe_entry):
        super().__init__()

        self.__unlocked_database = unlocked_database
        self.__safe_entry = safe_entry
        self.__search_stopped = False
        self.__signal_handle = 0

        self.__notes_buffer = self._value_entry.get_buffer()

        self.__tag = self.__notes_buffer.create_tag(None)

        manager = Adw.StyleManager.get_default()

        self.__setup_signals()

        self.__update_tag()
        self.__update_style_scheme(manager)

    def __setup_signals(self):
        manager = Adw.StyleManager.get_default()

        handle = self.__unlocked_database.database_manager.connect(
            "notify::locked",
            self.__on_locked,
        )
        self.__signal_handle = handle
        # Bind text to the corresponding safe entry.
        self.__safe_entry.bind_property(
            "notes",
            self.__notes_buffer,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        self.__notes_buffer.connect(
            "notify::style-scheme", self.__on_style_scheme_notify
        )
        manager.connect("notify::dark", self.__on_dark_notify)

    def __on_style_scheme_notify(self, _buffer, _pspec):
        self.__update_tag()

    def __on_dark_notify(self, manager, _pspec):
        self.__update_style_scheme(manager)

    def __update_style_scheme(self, manager):
        if manager.props.dark:
            scheme_name = "Adwaita-dark"
        else:
            scheme_name = "Adwaita"

        scheme_manager = GtkSource.StyleSchemeManager.get_default()
        scheme = scheme_manager.get_scheme(scheme_name)
        self.__notes_buffer.set_style_scheme(scheme)

    def __update_tag(self):
        table = self.__notes_buffer.get_tag_table()

        if current_tag := self.__tag:
            table.remove(current_tag)

        self.__tag = self.__notes_buffer.create_tag(None)

        if scheme := self.__notes_buffer.get_style_scheme():  # noqa: SIM102
            if style := scheme.get_style("search-match"):
                style.apply(self.__tag)

                if rgba := self.__tag.props.background_rgba:
                    rgba.alpha = 1.0
                    current_tag.props.background_rgba = rgba

        self.__tag.set_priority(table.get_size() - 1)

    #
    # Events
    #

    @Gtk.Template.Callback()
    def _on_copy_button_clicked(self, _button):
        notes_buffer = self.__notes_buffer
        bounds = notes_buffer.get_selection_bounds()
        if bounds:
            message = _("Selection copied")
            start, end = bounds[0], bounds[1]
        else:
            message = ""
            start = notes_buffer.get_start_iter()
            end = notes_buffer.get_end_iter()

        self.__unlocked_database.send_to_clipboard(
            notes_buffer.get_text(start, end, False),
            message=message,
            toast_overlay=self._toast_overlay,
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
            notes_buffer.get_start_iter(),
            notes_buffer.get_end_iter(),
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

    def do_closed(self) -> None:
        if handle := self.__signal_handle:
            self.__unlocked_database.database_manager.disconnect(handle)
            self.__signal_handle = 0
