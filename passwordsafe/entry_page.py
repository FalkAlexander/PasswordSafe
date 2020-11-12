# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations
import logging
import subprocess
from gettext import gettext as _
from typing import Optional
from uuid import UUID
from gi.repository import Gio, GLib, Gtk

import passwordsafe.config_manager
import passwordsafe.passphrase_generator
import passwordsafe.password_generator
from passwordsafe.color_widget import ColorEntryRow
from passwordsafe.history_buffer import HistoryEntryBuffer, HistoryTextBuffer
from passwordsafe.notes_dialog import NotesDialog
from passwordsafe.password_generator_popover import PasswordGeneratorPopover
from passwordsafe.scrolled_page import ScrolledPage


class EntryPage:
    #
    # Global Variables
    #
    unlocked_database = NotImplemented
    _pwd_popover = NotImplemented

    #
    # Init
    #

    def __init__(self, u_d):
        self.unlocked_database = u_d

    #
    # Header Bar
    #

    # Entry creation/editing page headerbar
    def set_entry_page_headerbar(self):
        self.unlocked_database.builder.get_object("linkedbox_right").hide()

        filename_label = self.unlocked_database.builder.get_object("filename_label")
        name = self.unlocked_database.database_manager.get_entry_name(
            self.unlocked_database.current_element)
        filename_label.set_text(name)

        secondary_menupopover_button = self.unlocked_database.builder.get_object("secondary_menupopover_button")
        secondary_menupopover_button.show_all()

        duplicate_menu_entry = self.unlocked_database.builder.get_object("duplicate_menu_entry")
        duplicate_menu_entry.show_all()

        references_menu_entry = self.unlocked_database.builder.get_object("references_menu_entry")
        references_menu_entry.show_all()

        self.unlocked_database.responsive_ui.headerbar_back_button()
        self.unlocked_database.responsive_ui.headerbar_selection_button()
        self.unlocked_database.responsive_ui.action_bar()
        self.unlocked_database.responsive_ui.headerbar_title()

    #
    # Create Property Rows
    #

    def insert_entry_properties_into_listbox(self, properties_list_box, add_all):
        builder = Gtk.Builder()

        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

        cur_entry = self.unlocked_database.current_element
        entry_uuid = cur_entry.uuid
        scrolled_page = self.unlocked_database.get_current_page()
        entry_name = self.unlocked_database.database_manager.get_entry_name(cur_entry)
        if entry_name or add_all:
            if scrolled_page.name_property_row is NotImplemented:
                # Create the name_property_row
                scrolled_page.name_property_row = builder.get_object("name_property_row")
                scrolled_page.name_property_value_entry = builder.get_object("name_property_value_entry")
                scrolled_page.name_property_value_entry.set_buffer(HistoryEntryBuffer([]))

            scrolled_page.name_property_value_entry.set_text(entry_name)
            scrolled_page.name_property_value_entry.connect(
                "changed", self.on_property_value_entry_changed, "name"
            )
            properties_list_box.add(scrolled_page.name_property_row)
            scrolled_page.name_property_value_entry.grab_focus()

        if self.unlocked_database.database_manager.has_entry_username(entry_uuid) is True or add_all is True:
            if scrolled_page.username_property_row is NotImplemented:
                scrolled_page.username_property_row = builder.get_object("username_property_row")
                scrolled_page.username_property_value_entry = builder.get_object("username_property_value_entry")
                scrolled_page.username_property_value_entry.set_buffer(HistoryEntryBuffer([]))
                value = self.unlocked_database.database_manager.get_entry_username(entry_uuid)
                if self.unlocked_database.database_manager.has_entry_username(entry_uuid) is True:
                    scrolled_page.username_property_value_entry.set_text(value)
                else:
                    scrolled_page.username_property_value_entry.set_text("")

                scrolled_page.username_property_value_entry.connect("icon-press", self.unlocked_database.on_copy_secondary_button_clicked)
                scrolled_page.username_property_value_entry.connect("changed", self.on_property_value_entry_changed, "username")
                properties_list_box.add(scrolled_page.username_property_row)
            elif scrolled_page.username_property_row:
                value = self.unlocked_database.database_manager.get_entry_username(entry_uuid)
                if self.unlocked_database.database_manager.has_entry_username(entry_uuid) is True:
                    scrolled_page.username_property_value_entry.set_text(value)
                else:
                    scrolled_page.username_property_value_entry.set_text("")

                scrolled_page.username_property_value_entry.connect("icon-press", self.unlocked_database.on_copy_secondary_button_clicked)
                scrolled_page.username_property_value_entry.connect("changed", self.on_property_value_entry_changed, "username")
                properties_list_box.add(scrolled_page.username_property_row)

        if self.unlocked_database.database_manager.has_entry_password(entry_uuid) is True or add_all is True:
            if scrolled_page.password_property_row is NotImplemented:
                scrolled_page.password_property_row = builder.get_object("password_property_row")
                scrolled_page.password_property_value_entry = builder.get_object("password_property_value_entry")
                scrolled_page.show_password_button = builder.get_object("show_password_button")
                scrolled_page.generate_password_button = builder.get_object("generate_password_button")
                scrolled_page.password_property_value_entry.set_buffer(HistoryEntryBuffer([]))
                value = self.unlocked_database.database_manager.get_entry_password(entry_uuid)

                if self.unlocked_database.database_manager.has_entry_password(entry_uuid) is True:
                    scrolled_page.password_property_value_entry.set_text(value)
                else:
                    scrolled_page.password_property_value_entry.set_text("")

                self._pwd_popover = PasswordGeneratorPopover(
                    self.unlocked_database)
                self._pwd_popover.bind_property(
                    "password", scrolled_page.password_property_value_entry,
                    "text")
                scrolled_page.generate_password_button.set_popover(
                    self._pwd_popover)

                scrolled_page.password_property_value_entry.connect("icon-press", self.unlocked_database.on_copy_secondary_button_clicked)
                scrolled_page.password_property_value_entry.connect("copy-clipboard", self.unlocked_database.on_copy_secondary_button_clicked, None, None)
                self.unlocked_database.bind_accelerator(self.unlocked_database.accelerators, scrolled_page.password_property_value_entry, "<Control><Shift>c", signal="copy-clipboard")
                scrolled_page.password_property_value_entry.connect("changed", self.on_property_value_entry_changed, "password")

                scrolled_page.password_level_bar = builder.get_object("password_level_bar")
                scrolled_page.password_level_bar.add_offset_value("weak", 1.0)
                scrolled_page.password_level_bar.add_offset_value("medium", 3.0)
                scrolled_page.password_level_bar.add_offset_value("strong", 4.0)
                scrolled_page.password_level_bar.add_offset_value("secure", 5.0)

                self.set_password_level_bar(scrolled_page)

                self.change_password_entry_visibility(scrolled_page.password_property_value_entry, scrolled_page.show_password_button)

                properties_list_box.add(scrolled_page.password_property_row)
            elif scrolled_page.password_property_row:
                value = self.unlocked_database.database_manager.get_entry_password(entry_uuid)
                if self.unlocked_database.database_manager.has_entry_password(entry_uuid) is True:
                    scrolled_page.password_property_value_entry.set_text(value)
                else:
                    scrolled_page.password_property_value_entry.set_text("")

                scrolled_page.password_property_value_entry.connect("icon-press", self.unlocked_database.on_copy_secondary_button_clicked)
                scrolled_page.password_property_value_entry.connect("changed", self.on_property_value_entry_changed, "password")
                properties_list_box.add(scrolled_page.password_property_row)

        if self.unlocked_database.database_manager.has_entry_url(entry_uuid) is True or add_all is True:
            if scrolled_page.url_property_row is NotImplemented:
                scrolled_page.url_property_row = builder.get_object("url_property_row")
                scrolled_page.url_property_value_entry = builder.get_object("url_property_value_entry")
                scrolled_page.url_property_value_entry.set_buffer(HistoryEntryBuffer([]))
                value = self.unlocked_database.database_manager.get_entry_url(
                    entry_uuid)
                if self.unlocked_database.database_manager.has_entry_url(entry_uuid) is True:
                    scrolled_page.url_property_value_entry.set_text(value)
                else:
                    scrolled_page.url_property_value_entry.set_text("")

                scrolled_page.url_property_value_entry.connect("icon-press", self.on_link_secondary_button_clicked)
                scrolled_page.url_property_value_entry.connect("changed", self.on_property_value_entry_changed, "url")
                properties_list_box.add(scrolled_page.url_property_row)
            elif scrolled_page.url_property_row:
                value = self.unlocked_database.database_manager.get_entry_url(entry_uuid)
                if self.unlocked_database.database_manager.has_entry_url(entry_uuid) is True:
                    scrolled_page.url_property_value_entry.set_text(value)
                else:
                    scrolled_page.url_property_value_entry.set_text("")

                scrolled_page.url_property_value_entry.connect("icon-press", self.on_link_secondary_button_clicked)
                scrolled_page.url_property_value_entry.connect("changed", self.on_property_value_entry_changed, "url")
                properties_list_box.add(scrolled_page.url_property_row)

        if self.unlocked_database.database_manager.has_entry_notes(entry_uuid) is True or add_all is True:
            if scrolled_page.notes_property_row is NotImplemented:
                scrolled_page.notes_property_row = builder.get_object("notes_property_row")
                scrolled_page.notes_property_value_entry = builder.get_object("notes_property_value_entry")

                builder.get_object("notes_detach_button").connect("clicked", self.on_notes_detach_button_clicked)

                value = self.unlocked_database.database_manager.get_notes(
                    entry_uuid)

                textbuffer = HistoryTextBuffer([])
                if self.unlocked_database.database_manager.has_entry_notes(entry_uuid) is True:
                    textbuffer.set_text(value)
                else:
                    textbuffer.set_text("")
                textbuffer.connect("changed", self.on_property_value_entry_changed, "notes")
                scrolled_page.notes_property_value_entry.set_buffer(textbuffer)
                properties_list_box.add(scrolled_page.notes_property_row)
            elif scrolled_page.notes_property_row:
                value = self.unlocked_database.database_manager.get_notes(
                    entry_uuid)
                textbuffer = scrolled_page.notes_property_value_entry.get_buffer()
                if self.unlocked_database.database_manager.has_entry_notes(entry_uuid) is True:
                    textbuffer.set_text(value)
                    textbuffer.set_modified(False)
                else:
                    textbuffer.set_text("")
                textbuffer.connect("changed", self.on_property_value_entry_changed, "notes")
                properties_list_box.add(scrolled_page.notes_property_row)

        if self.unlocked_database.database_manager.has_entry_color(entry_uuid) is True or add_all is True:
            if scrolled_page.color_property_row is NotImplemented:
                scrolled_page.color_property_row = ColorEntryRow(
                    self.unlocked_database, scrolled_page, entry_uuid)

                properties_list_box.add(scrolled_page.color_property_row)
            elif scrolled_page.color_property_row is not NotImplemented:
                properties_list_box.add(scrolled_page.color_property_row)

        if self.unlocked_database.database_manager.has_entry_icon(entry_uuid) is True or add_all is True:
            if scrolled_page.icon_property_row is NotImplemented:
                scrolled_page.icon_property_row = builder.get_object("icon_property_row")
                for button in builder.get_object("icon_entry_box").get_children():
                    button.get_style_context().add_class("EntryIconButton")

                mail_icon_button = builder.get_object("19")
                profile_icon_button = builder.get_object("9")
                network_profile_button = builder.get_object("1")
                key_button = builder.get_object("0")
                terminal_icon_button = builder.get_object("30")
                setting_icon_button = builder.get_object("34")
                folder_icon_button = builder.get_object("48")
                harddrive_icon_button = builder.get_object("27")
                wifi_icon_button = builder.get_object("12")
                desktop_icon_button = builder.get_object("23")
                mail_icon_button.connect("toggled", self.on_entry_icon_button_toggled)
                profile_icon_button.connect(
                    "toggled", self.on_entry_icon_button_toggled
                )
                network_profile_button.connect(
                    "toggled", self.on_entry_icon_button_toggled
                )
                key_button.connect("toggled", self.on_entry_icon_button_toggled)
                terminal_icon_button.connect(
                    "toggled", self.on_entry_icon_button_toggled
                )
                setting_icon_button.connect(
                    "toggled", self.on_entry_icon_button_toggled
                )
                folder_icon_button.connect("toggled", self.on_entry_icon_button_toggled)
                harddrive_icon_button.connect(
                    "toggled", self.on_entry_icon_button_toggled
                )
                wifi_icon_button.connect("toggled", self.on_entry_icon_button_toggled)
                desktop_icon_button.connect(
                    "toggled", self.on_entry_icon_button_toggled
                )

                icon: Optional[int] = self.unlocked_database.database_manager.get_icon(
                    self.unlocked_database.current_element
                )
                if icon == 0:
                    key_button.set_active(True)
                elif icon == 19:
                    mail_icon_button.set_active(True)
                elif icon == 9:
                    profile_icon_button.set_active(True)
                elif icon == 1:
                    network_profile_button.set_active(True)
                elif icon == 30:
                    terminal_icon_button.set_active(True)
                elif icon == 34:
                    setting_icon_button.set_active(True)
                elif icon == 48:
                    folder_icon_button.set_active(True)
                elif icon == 27:
                    harddrive_icon_button.set_active(True)
                elif icon == 12:
                    wifi_icon_button.set_active(True)
                elif icon == 23:
                    desktop_icon_button.set_active(True)

                properties_list_box.add(scrolled_page.icon_property_row)
            elif scrolled_page.icon_property_row is not NotImplemented:
                properties_list_box.add(scrolled_page.icon_property_row)

        if scrolled_page.attachment_property_row is NotImplemented:
            scrolled_page.attachment_property_row = builder.get_object("attachment_property_row")
            scrolled_page.attachment_list_box = builder.get_object("attachment_list_box")
            for attachment in self.unlocked_database.database_manager.get_entry_attachments_from_entry_uuid(entry_uuid):
                self.add_attachment_row(attachment)

            scrolled_page.attachment_list_box.add(builder.get_object("add_attachment_row"))
            scrolled_page.attachment_list_box.connect("row-activated", self.on_attachment_list_box_activated)
            properties_list_box.add(scrolled_page.attachment_property_row)
        elif scrolled_page.attachment_property_row is not NotImplemented:
            properties_list_box.add(scrolled_page.attachment_property_row)

        if scrolled_page.attributes_property_row is NotImplemented:
            scrolled_page.attributes_property_row = builder.get_object("attributes_property_row")
            scrolled_page.attributes_key_entry = builder.get_object("attributes_key_entry")
            scrolled_page.attributes_value_entry = builder.get_object("attributes_value_entry")
            scrolled_page.attributes_add_button = builder.get_object("attributes_add_button")

            scrolled_page.attributes_add_button.connect("clicked", self.on_attributes_add_button_clicked)
            scrolled_page.attributes_key_entry.connect("activate", self.on_attributes_add_button_clicked)
            scrolled_page.attributes_value_entry.connect("activate", self.on_attributes_add_button_clicked)

            properties_list_box.add(scrolled_page.attributes_property_row)
        elif scrolled_page.attributes_property_row is not NotImplemented:
            properties_list_box.add(scrolled_page.attributes_property_row)

        attributes = self.unlocked_database.database_manager.get_entry_attributes(entry_uuid)
        for key in attributes:
            if key not in ("color_prop_LcljUMJZ9X", "Notes"):
                self.add_attribute_property_row(key, attributes[key])

        if scrolled_page.color_property_row is not NotImplemented and \
           scrolled_page.name_property_row is not NotImplemented and \
           scrolled_page.username_property_row is not NotImplemented and \
           scrolled_page.password_property_row is not NotImplemented and \
           scrolled_page.url_property_row is not NotImplemented and \
           scrolled_page.notes_property_row is not NotImplemented and \
           scrolled_page.attributes_property_row is not NotImplemented:
            scrolled_page.all_properties_revealed = True
        else:
            scrolled_page.show_all_row = builder.get_object("show_all_row")
            scrolled_page.show_all_properties_button = builder.get_object("show_all_properties_button")
            scrolled_page.show_all_properties_button.connect("clicked", self.on_show_all_properties_button_clicked)
            properties_list_box.add(scrolled_page.show_all_row)

    def add_attribute_property_row(self, key, value):
        """Add an attribute to the attributes list view.

        :param str key: property name
        :param str value: property value
        """
        scrolled_page = self.unlocked_database.get_current_page()

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

        index = scrolled_page.attributes_property_row.get_index()

        attribute_property_row = builder.get_object("attribute_property_row")
        attribute_property_name_label = builder.get_object("attribute_property_name_label")
        attribute_key_edit_button = builder.get_object("attribute_key_edit_button")
        attribute_value_entry = builder.get_object("attribute_value_entry")
        attribute_value_entry.set_buffer(HistoryEntryBuffer([]))
        attribute_remove_button = builder.get_object("attribute_remove_button")

        attribute_property_row.set_name(key)
        attribute_property_name_label.set_text(key)
        if value is not None:
            attribute_value_entry.set_text(value)
        attribute_value_entry.connect("changed", self.on_attributes_value_entry_changed)
        attribute_remove_button.connect("clicked", self.on_attribute_remove_button_clicked)
        attribute_key_edit_button.connect("clicked", self.on_attribute_key_edit_button_clicked)

        scrolled_page.properties_list_box.insert(attribute_property_row, index)
        attribute_property_row.show_all()
        scrolled_page.attribute_property_row_list.append(attribute_property_row)

    #
    # Events
    #

    def on_show_all_properties_button_clicked(self, _widget):
        self.unlocked_database.start_database_lock_timer()
        scrolled_page = self.unlocked_database.get_current_page()

        for row in scrolled_page.properties_list_box.get_children():
            scrolled_page.properties_list_box.remove(row)

        self.insert_entry_properties_into_listbox(scrolled_page.properties_list_box, True)

    def on_property_value_entry_changed(self, widget, type_name):
        self.unlocked_database.start_database_lock_timer()
        entry_uuid = self.unlocked_database.current_element.uuid

        scrolled_page = self.unlocked_database.get_current_page()
        scrolled_page.is_dirty = True

        if type_name == "name":
            self.unlocked_database.database_manager.set_entry_name(entry_uuid, widget.get_text())

            pathbar_button = self.unlocked_database.pathbar.get_pathbar_button(entry_uuid)
            pathbar_button.set_label(widget.get_text())

        elif type_name == "username":
            self.unlocked_database.database_manager.set_entry_username(entry_uuid, widget.get_text())
        elif type_name == "password":
            self.unlocked_database.database_manager.set_entry_password(entry_uuid, widget.get_text())
            self.set_password_level_bar(scrolled_page)
        elif type_name == "url":
            self.unlocked_database.database_manager.set_entry_url(entry_uuid, widget.get_text())
        elif type_name == "notes":
            self.unlocked_database.database_manager.set_entry_notes(entry_uuid, widget.get_text(widget.get_start_iter(), widget.get_end_iter(), False))

    def on_notes_detach_button_clicked(self, _button):
        self.unlocked_database.start_database_lock_timer()
        NotesDialog(self.unlocked_database)

    def on_entry_icon_button_toggled(self, button):
        if button.get_active() is False:
            return

        self.unlocked_database.start_database_lock_timer()
        entry_uuid = self.unlocked_database.current_element.uuid
        scrolled_page = self.unlocked_database.get_current_page()

        if str(self.unlocked_database.database_manager.get_icon(entry_uuid)) == button.get_name():
            return

        scrolled_page.is_dirty = True
        self.unlocked_database.database_manager.set_entry_icon(entry_uuid, button.get_name())

    def on_link_secondary_button_clicked(self, widget, _position, _eventbutton):
        self.unlocked_database.start_database_lock_timer()
        Gtk.show_uri_on_window(self.unlocked_database.window, widget.get_text(), Gtk.get_current_event_time())

    def on_show_password_button_toggled(self, _toggle_button, entry):
        self.unlocked_database.start_database_lock_timer()
        if entry.get_visibility() is True:
            entry.set_visibility(False)
        else:
            entry.set_visibility(True)

    #
    # Additional Attributes
    #

    def on_attributes_add_button_clicked(self, _widget):
        entry_uuid = self.unlocked_database.current_element.uuid
        scrolled_page = self.unlocked_database.get_current_page()

        key = scrolled_page.attributes_key_entry.get_text()
        value = scrolled_page.attributes_value_entry.get_text()

        if key == "" or key is None:
            scrolled_page.attributes_key_entry.get_style_context().add_class("error")
            return

        if self.unlocked_database.database_manager.has_entry_attribute(entry_uuid, key) is True:
            scrolled_page.attributes_key_entry.get_style_context().add_class("error")
            self.unlocked_database.show_database_action_revealer(_("Attribute key already exists"))
            return

        scrolled_page.attributes_key_entry.get_style_context().remove_class("error")

        scrolled_page.attributes_key_entry.set_text("")
        scrolled_page.attributes_value_entry.set_text("")

        self.unlocked_database.database_manager.set_entry_attribute(entry_uuid, key, value)
        self.add_attribute_property_row(key, value)
        scrolled_page.is_dirty = True

    def on_attribute_remove_button_clicked(self, button):
        entry_uuid = self.unlocked_database.current_element.uuid
        scrolled_page = self.unlocked_database.get_current_page()

        parent = button.get_parent().get_parent().get_parent()
        key = parent.get_name()

        self.unlocked_database.database_manager.delete_entry_attribute(entry_uuid, key)
        scrolled_page.properties_list_box.remove(parent)

    def on_attributes_value_entry_changed(self, widget):
        entry_uuid = self.unlocked_database.current_element.uuid

        parent = widget.get_parent().get_parent().get_parent()
        key = parent.get_name()

        self.unlocked_database.database_manager.set_entry_attribute(entry_uuid, key, widget.get_text())

    def on_attribute_key_edit_button_clicked(self, button):
        entry_uuid = self.unlocked_database.current_element.uuid

        parent = button.get_parent().get_parent().get_parent()
        key = parent.get_name()

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

        key_entry = builder.get_object("key_entry")
        key_entry.connect("activate", self.on_key_entry_activated, entry_uuid, key, button, parent)
        key_entry.set_text(key)

        attribute_entry_box = button.get_parent()
        attribute_entry_box.remove(button)
        attribute_entry_box.add(key_entry)
        attribute_entry_box.reorder_child(key_entry, 0)
        key_entry.grab_focus()

    def on_key_entry_activated(self, entry, entry_uuid, key, button, parent):
        if entry.get_text() == "" or entry.get_text is None:
            entry.get_style_context().add_class("error")
            return

        if entry.get_text() == key:
            attribute_entry_box = entry.get_parent()
            attribute_entry_box.remove(entry)
            attribute_entry_box.add(button)
            attribute_entry_box.reorder_child(button, 0)
            return

        if self.unlocked_database.database_manager.has_entry_attribute(entry_uuid, entry.get_text()) is True:
            entry.get_style_context().add_class("error")
            self.unlocked_database.show_database_action_revealer(_("Attribute key already exists"))
            return

        self.unlocked_database.database_manager.set_entry_attribute(entry_uuid, entry.get_text(), self.unlocked_database.database_manager.get_entry_attribute_value_from_entry_uuid(entry_uuid, key))
        self.unlocked_database.database_manager.delete_entry_attribute(entry_uuid, key)

        button.get_children()[0].set_text(entry.get_text())
        parent.set_name(entry.get_text())

        attribute_entry_box = entry.get_parent()
        attribute_entry_box.remove(entry)
        attribute_entry_box.add(button)
        attribute_entry_box.reorder_child(button, 0)

    #
    # Attachment Handling
    #

    def on_attachment_list_box_activated(self, _widget, list_box_row):
        if list_box_row.get_name() == "AddAttachmentRow":
            self.on_add_attachment_row_clicked()
        else:
            self.on_attachment_row_clicked(self.unlocked_database.database_manager.get_attachment_from_id(list_box_row.get_name()))

    def on_add_attachment_row_clicked(self):
        self.unlocked_database.start_database_lock_timer()
        select_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for selecting attachment file
            _("Select attachment"), self.unlocked_database.window, Gtk.FileChooserAction.OPEN,
            _("Add"), None)
        select_dialog.set_modal(True)
        select_dialog.set_local_only(False)
        select_dialog.set_select_multiple(True)

        response = select_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            entry_uuid = self.unlocked_database.current_element.uuid
            for uri in select_dialog.get_uris():
                attachment = Gio.File.new_for_uri(uri)
                byte_buffer = attachment.load_bytes()[0].get_data()
                filename = attachment.get_basename()
                self.add_attachment_row(self.unlocked_database.database_manager.add_entry_attachment(entry_uuid, byte_buffer, filename))

    def add_attachment_row(self, attachment):
        entry_uuid = self.unlocked_database.current_element.uuid
        scrolled_page = self.unlocked_database.get_current_page()

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

        attachment_row = builder.get_object("attachment_row")
        attachment_row.set_name(str(attachment.id))
        builder.get_object("attachment_label").set_label(attachment.filename)
        builder.get_object("attachment_download_button").connect("clicked", self.on_attachment_download_button_clicked, attachment)
        builder.get_object("attachment_delete_button").connect("clicked", self.on_attachment_delete_button_clicked, entry_uuid, attachment, attachment_row)

        scrolled_page.attachment_list_box.insert(attachment_row, len(scrolled_page.attachment_list_box) - 1)

    def on_attachment_row_clicked(self, attachment):
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/attachment_warning_dialog.ui")
        warning_dialog = builder.get_object("warning_dialog")
        warning_dialog.set_destroy_with_parent(True)
        warning_dialog.set_modal(True)
        warning_dialog.set_transient_for(self.unlocked_database.window)

        builder.get_object("back_button").connect("clicked", self.on_warning_dialog_back_button_clicked, warning_dialog)
        builder.get_object("proceed_button").connect("clicked", self.on_warning_dialog_proceed_button_clicked, warning_dialog, attachment)

        warning_dialog.present()

    def on_attachment_download_button_clicked(self, _button, attachment):
        save_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for downloading an attachment
            _("Save attachment"), self.unlocked_database.window, Gtk.FileChooserAction.SAVE,
            _("Save"), None)
        save_dialog.set_do_overwrite_confirmation(True)
        save_dialog.set_current_name(attachment.filename)
        save_dialog.set_modal(True)
        save_dialog.set_local_only(False)

        response = save_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            bytes_buffer = self.unlocked_database.database_manager.db.binaries[attachment.id]
            self.save_to_disk(save_dialog.get_filename(), bytes_buffer)

    def on_attachment_delete_button_clicked(self, _button, entry_uuid, attachment, attachment_row):
        self.unlocked_database.database_manager.delete_entry_attachment(entry_uuid, attachment)
        attachment_row.destroy()

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

        entry_uuid = self.unlocked_database.current_element.uuid
        scrolled_page = self.unlocked_database.get_current_page()

        for row in scrolled_page.attachment_list_box.get_children():
            if row.get_name() != "AddAttachmentRow":
                row.destroy()

        for attachment in self.unlocked_database.database_manager.get_entry_attachments_from_entry_uuid(entry_uuid):
            self.add_attachment_row(attachment)

    #
    # Helper
    #

    def save_to_disk(self, filepath, byte_buffer):
        file = Gio.File.new_for_path(filepath)
        stream = Gio.File.replace(
            file, None, False,
            Gio.FileCreateFlags.PRIVATE
            | Gio.FileCreateFlags.REPLACE_DESTINATION, None)
        Gio.OutputStream.write_bytes(stream, GLib.Bytes.new(byte_buffer), None)
        stream.close()

    def open_tmp_file(self, bytes_buffer, filename):
        (file, stream) = Gio.File.new_tmp(filename + ".XXXXXX")
        stream.get_output_stream().write_bytes(GLib.Bytes.new(bytes_buffer))
        stream.close()
        self.unlocked_database.scheduled_tmpfiles_deletion.append(file)
        subprocess.run(["xdg-open", file.get_path()], check=True)

    def on_warning_dialog_back_button_clicked(self, _button, dialog):
        dialog.close()

    def on_warning_dialog_proceed_button_clicked(self, _button, dialog, attachment):
        dialog.close()
        self.open_tmp_file(self.unlocked_database.database_manager.db.binaries[attachment.id], attachment.filename)

    def change_password_entry_visibility(self, entry, toggle_button):
        toggle_button.connect("toggled", self.on_show_password_button_toggled, entry)

        if passwordsafe.config_manager.get_show_password_fields() is False:
            entry.set_visibility(False)
        else:
            toggle_button.toggled()
            entry.set_visibility(True)

    def set_password_level_bar(self, scrolled_page: ScrolledPage) -> None:
        """ Displays the strength of the password in the level bar. """

        password = scrolled_page.password_property_value_entry.get_text()

        # If our password is a just a reference, get the real password
        if password.startswith("{REF:P"):
            try:
                uuid = UUID(self.unlocked_database.reference_to_hex_uuid(
                    scrolled_page.password_property_value_entry.get_text()))
                password = self.unlocked_database.database_manager.get_entry_password(uuid)
            except Exception:
                logging.warning(
                    "Failed to look up password for reference '%s'", password)

        # strength() returns None on error.
        strength = passwordsafe.password_generator.strength(password)
        if strength is not None:
            scrolled_page.password_level_bar.set_value(strength)
