# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gtk, Gdk


class ReferencesDialog():
    __property = "P"

    def __init__(self, unlocked_database):
        self.__unlocked_database = unlocked_database
        self.__database_manager = unlocked_database.database_manager
        self.__builder = Gtk.Builder()
        self.__builder.add_from_resource("/org/gnome/PasswordSafe/references_dialog.ui")

        self.__reference_entry = self.__builder.get_object("reference_entry")
        self.__dialog = self.__builder.get_object("references_dialog")

        self.__setup_signals()
        self.__setup_widgets()

    def present(self) -> None:
        self.__dialog.present()

    def __setup_widgets(self) -> None:
        self.__dialog.set_modal(True)
        self.__dialog.set_transient_for(self.__unlocked_database.window)
        self.__update_reference_entry()

    def __setup_signals(self) -> None:
        self.__reference_entry.connect("icon-press", self.__on_copy_secondary_button_clicked)
        self.__connect_model_buttons_signals()
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self.__on_key_press_event)
        self.__dialog.add_controller(controller)
        self.__database_manager.connect("notify::locked", self.__on_locked)

    def __connect_model_buttons_signals(self):
        self.__builder.get_object("property_label_gesture").connect("pressed", self.__open_codes_popover)
        self.__builder.get_object("identifier_label_gesture").connect("pressed", self.__open_codes_popover)
        self.__builder.get_object("uuid_label_gesture").connect("pressed", self.__open_uuid_popover)
        # Buttons
        self.__builder.get_object("title_button").connect("clicked", self.__on_property_model_button_clicked)
        self.__builder.get_object("username_button").connect("clicked", self.__on_property_model_button_clicked)
        self.__builder.get_object("password_button").connect("clicked", self.__on_property_model_button_clicked)
        self.__builder.get_object("url_button").connect("clicked", self.__on_property_model_button_clicked)
        self.__builder.get_object("notes_button").connect("clicked", self.__on_property_model_button_clicked)

        uuid_popover = self.__builder.get_object("uuid_popover")
        uuid_popover.set_parent(self.__builder.get_object("uuid_label"))

        codes_popover = self.__builder.get_object("codes_popover")
        codes_popover.set_parent(self.__builder.get_object("property_label"))

    def __update_reference_entry(self):
        """Update the reference entry and selected label text."""
        uuid = self.__unlocked_database.current_element.uuid
        encoded_uuid = uuid.hex.upper()

        self.__builder.get_object("property_popover_button").set_label(self.__property)

        self.__reference_entry.set_text("{REF:" + self.__property + "@I:" + encoded_uuid + "}")

    def __open_codes_popover(self, gesture, _n_points, _x, _y, data=None):
        codes_popover = self.__builder.get_object("codes_popover")
        codes_popover.popup()

    def __open_uuid_popover(self, gesture, _n_points, _x, _y, data=None):
        uuid_popover = self.__builder.get_object("uuid_popover")
        uuid_popover.popup()

    def __on_key_press_event(self, _controller, keyval, _keycode, _state, _gdata=None):
        self.__unlocked_database.start_database_lock_timer()
        if keyval == Gdk.KEY_Escape:
            self.__dialog.close()
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def __on_copy_secondary_button_clicked(self, widget, _position, _eventbutton):
        self.__unlocked_database.start_database_lock_timer()
        self.__unlocked_database.clipboard.set(widget.get_text())

    def __on_property_model_button_clicked(self, widget):
        self.__unlocked_database.start_database_lock_timer()
        self.__property = widget.get_name()
        self.__update_reference_entry()

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.__dialog.close()
