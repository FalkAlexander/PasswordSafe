# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gdk, Gtk


class CustomKeypressHandler:

    def __init__(self, u_d):
        self.unlocked_database = u_d

    #
    # Special Keys (e.g. type-to-search)
    #

    def register_custom_events(self):
        controller = Gtk.EventControllerKey()
        click_controller = Gtk.GestureClick.new()
        click_controller.props.button = 8  # Mouse button 8 is the back button.

        controller.connect("key-pressed", self.on_special_key_pressed)
        click_controller.connect("pressed", self._on_button_pressed)

        self.unlocked_database.window.add_controller(controller)
        self.unlocked_database.window.add_controller(click_controller)

    def on_special_key_pressed(self, controller, keyval, _keycode, state):
        if not self._current_view_accessible():
            return Gdk.EVENT_PROPAGATE

        edit_page = self.unlocked_database.in_edit_page

        if (
            not edit_page
            and state & Gdk.ModifierType.ALT_MASK == 0
            and Gdk.keyval_to_unicode(keyval) != 0
        ):
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

    def _on_button_pressed(
        self, _gesture: Gtk.GestureClick, _n_press: int, _x: float, _y: float
    ) -> None:
        """Go to the parent group with the back button.
        """
        self.unlocked_database.go_back()
