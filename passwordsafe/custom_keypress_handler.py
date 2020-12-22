# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing

from gi.repository import Gdk, Gtk

import passwordsafe.pathbar_button

if typing.TYPE_CHECKING:
    from passwordsafe.main_window import MainWindow


class CustomKeypressHandler:
    #
    # Global Variables
    #

    unlocked_database = NotImplemented

    #
    # Init
    #

    def __init__(self, u_d):
        self.unlocked_database = u_d

    #
    # Special Keys (e.g. type-to-search)
    #

    def register_custom_events(self):
        self.unlocked_database.window.connect("key-press-event", self.on_special_key_pressed)
        self.unlocked_database.window.connect("button-release-event", self._on_button_released)

    def on_special_key_pressed(self, window: MainWindow, eventkey: Gdk.EventKey) -> bool:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        if not self._current_view_accessible():
            return Gdk.EVENT_PROPAGATE

        scrolled_page = self.unlocked_database.get_current_page()

        # Handle undo and redo on entries.
        if (
                scrolled_page.edit_page
                and eventkey.state & Gdk.ModifierType.CONTROL_MASK == Gdk.ModifierType.CONTROL_MASK
        ):
            keyval_name = Gdk.keyval_name(eventkey.keyval)
            if isinstance(window.get_focus(), Gtk.TextView):
                textbuffer = window.get_focus().get_buffer()
                if isinstance(textbuffer, passwordsafe.history_buffer.HistoryTextBuffer):
                    if keyval_name == 'y':
                        textbuffer.logic.do_redo()
                        return Gdk.EVENT_PROPAGATE
                    if keyval_name == "z":
                        textbuffer.logic.do_undo()
                        return Gdk.EVENT_PROPAGATE
            if isinstance(window.get_focus(), Gtk.Entry):
                textbuffer = window.get_focus().get_buffer()
                if isinstance(textbuffer, passwordsafe.history_buffer.HistoryEntryBuffer):
                    if keyval_name == 'y':
                        textbuffer.logic.do_redo()
                        return Gdk.EVENT_PROPAGATE
                    if keyval_name == "z":
                        textbuffer.logic.do_undo()
                        return Gdk.EVENT_PROPAGATE
        elif (not scrolled_page.edit_page
              # MOD1 usually corresponds to Alt
              and eventkey.state & Gdk.ModifierType.MOD1_MASK == 0
              and eventkey.string.isalnum()):
            self.unlocked_database.props.search_active = True

        return Gdk.EVENT_PROPAGATE

    def _current_view_accessible(self):
        """Check that the current view is accessible:
         * selection mode is not active
         * search mode is not active
         * current database is not locked
        """
        db_view = self.unlocked_database
        if (not db_view.window.tab_visible(db_view.parent_widget)
                or db_view.props.database_locked
                or db_view.props.selection_mode
                or db_view.search_active):
            return False

        return True

    def _on_button_released(
            self, _window: MainWindow, event: Gtk.Event) -> bool:
        """Go to the parent group with the back button.

        :param Gtk.Widget window: the main window
        :param Gtk.Event event: the event
        """
        # Mouse button 8 is the back button.
        if event.button == 8:
            self.unlocked_database.go_back()
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE
