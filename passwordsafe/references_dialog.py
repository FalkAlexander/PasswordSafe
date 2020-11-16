# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gtk, Gdk, Handy


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
        self.__dialog.connect("key-press-event", self.__on_key_press_event)
        self.__database_manager.connect("notify::locked", self.__on_locked)

    def __connect_model_buttons_signals(self):
        self.__builder.get_object("property_label").connect("button-press-event", self.__open_codes_popover)
        self.__builder.get_object("identifier_label").connect("button-press-event", self.__open_codes_popover)
        self.__builder.get_object("uuid_label").connect("button-press-event", self.__open_uuid_popover)
        # Buttons
        self.__builder.get_object("title_button").connect("clicked", self.__on_property_model_button_clicked)
        self.__builder.get_object("username_button").connect("clicked", self.__on_property_model_button_clicked)
        self.__builder.get_object("password_button").connect("clicked", self.__on_property_model_button_clicked)
        self.__builder.get_object("url_button").connect("clicked", self.__on_property_model_button_clicked)
        self.__builder.get_object("notes_button").connect("clicked", self.__on_property_model_button_clicked)

    def __update_reference_entry(self):
        """Update the reference entry and selected label text."""
        uuid = self.__unlocked_database.current_element.uuid
        encoded_uuid = uuid.hex.upper()

        self.__builder.get_object("selected_property_label").set_text(self.__property)

        self.__reference_entry.set_text("{REF:" + self.__property + "@I:" + encoded_uuid + "}")

    def __open_codes_popover(self, widget, _label):
        codes_popover = self.__builder.get_object("codes_popover")
        codes_popover.set_relative_to(widget)
        codes_popover.popup()

    def __open_uuid_popover(self, widget, _label):
        uuid_popover = self.__builder.get_object("uuid_popover")
        uuid_popover.set_relative_to(widget)
        uuid_popover.popup()

    def __on_key_press_event(self, _window: Handy.Window, event: Gtk.Event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.__dialog.close()
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def __on_copy_secondary_button_clicked(self, widget, _position, _eventbutton):
        self.__unlocked_database.clipboard.set_text(widget.get_text(), -1)

    def __on_property_model_button_clicked(self, widget):
        self.__property = widget.get_name()
        self.__update_reference_entry()

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.__dialog.close()
