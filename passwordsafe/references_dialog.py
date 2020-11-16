# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gtk, Gdk, Handy


class ReferencesDialog():
    dialog = NotImplemented

    unlocked_database = NotImplemented
    database_manager = NotImplemented
    builder = NotImplemented

    reference_entry = NotImplemented
    property = "P"

    def __init__(self, unlocked_database):
        self.unlocked_database = unlocked_database
        self.database_manager = unlocked_database.database_manager
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/references_dialog.ui")

        self.reference_entry = self.builder.get_object("reference_entry")
        self.dialog = self.builder.get_object("references_dialog")

        self.__setup_signals()
        self.__setup_widgets()

    def present(self) -> None:
        self.dialog.present()

    def __setup_widgets(self) -> None:
        self.dialog.set_modal(True)
        self.dialog.set_transient_for(self.unlocked_database.window)
        self.__update_reference_entry()

    def __setup_signals(self) -> None:
        self.dialog.connect("delete-event", self.__on_dialog_quit)
        self.reference_entry.connect("icon-press", self.__on_copy_secondary_button_clicked)
        self.__connect_model_buttons_signals()
        self.dialog.connect("key-press-event", self.__on_key_press_event)
        self.database_manager.connect("notify::locked", self.__on_locked)

    def __connect_model_buttons_signals(self):
        self.builder.get_object("property_label").connect("button-press-event", self.__open_codes_popover)
        self.builder.get_object("identifier_label").connect("button-press-event", self.__open_codes_popover)
        self.builder.get_object("uuid_label").connect("button-press-event", self.__open_uuid_popover)
        # Buttons
        self.builder.get_object("title_button").connect("clicked", self.__on_property_model_button_clicked)
        self.builder.get_object("username_button").connect("clicked", self.__on_property_model_button_clicked)
        self.builder.get_object("password_button").connect("clicked", self.__on_property_model_button_clicked)
        self.builder.get_object("url_button").connect("clicked", self.__on_property_model_button_clicked)
        self.builder.get_object("notes_button").connect("clicked", self.__on_property_model_button_clicked)

    def __update_reference_entry(self):
        """Update the reference entry and selected label text."""
        uuid = self.unlocked_database.current_element.uuid
        encoded_uuid = uuid.hex.upper()

        self.builder.get_object("selected_property_label").set_text(self.property)

        self.reference_entry.set_text("{REF:" + self.property + "@I:" + encoded_uuid + "}")

    def __open_codes_popover(self, widget, _label):
        codes_popover = self.builder.get_object("codes_popover")
        codes_popover.set_relative_to(widget)
        codes_popover.popup()

    def __open_uuid_popover(self, widget, _label):
        uuid_popover = self.builder.get_object("uuid_popover")
        uuid_popover.set_relative_to(widget)
        uuid_popover.popup()

    def __on_dialog_quit(self, _window, _event):
        self.unlocked_database.references_dialog = NotImplemented

    def __on_key_press_event(self, _window: Handy.Window, event: Gtk.Event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.dialog.close()
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def __on_copy_secondary_button_clicked(self, widget, _position, _eventbutton):
        self.unlocked_database.clipboard.set_text(widget.get_text(), -1)

    def __on_property_model_button_clicked(self, widget):
        self.property = widget.get_name()
        self.__update_reference_entry()

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.__dialog.close()
