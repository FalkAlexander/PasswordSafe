# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _
from gi.repository import Gio, GLib, GObject, Gtk

from passwordsafe.attachment_warning_dialog import AttachmentWarningDialog
from passwordsafe.color_widget import Color, ColorEntryRow
from passwordsafe.history_buffer import HistoryEntryBuffer, HistoryTextBuffer
from passwordsafe.notes_dialog import NotesDialog
from passwordsafe.password_entry_row import PasswordEntryRow

if typing.TYPE_CHECKING:
    from passwordsafe.safe_entry import SafeEntry


class EntryPage:
    # pylint: disable=too-many-public-methods
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
    # Create Property Rows
    #

    def insert_entry_properties_into_listbox(self, properties_list_box, add_all):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        builder = Gtk.Builder()

        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

        safe_entry: SafeEntry = self.unlocked_database.current_element
        scrolled_page = self.unlocked_database.get_current_page()
        entry_name = safe_entry.props.name
        if entry_name or add_all:
            if scrolled_page.name_property_row is NotImplemented:
                # Create the name_property_row
                scrolled_page.name_property_row = builder.get_object("name_property_row")
                scrolled_page.name_property_value_entry = builder.get_object("name_property_value_entry")
                scrolled_page.name_property_value_entry.set_buffer(HistoryEntryBuffer([]))

            safe_entry.bind_property(
                "name", scrolled_page.name_property_value_entry, "text",
                GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL
            )
            properties_list_box.add(scrolled_page.name_property_row)
            scrolled_page.name_property_value_entry.grab_focus()

        if safe_entry.props.username or add_all:
            if scrolled_page.username_property_row is NotImplemented:
                scrolled_page.username_property_row = builder.get_object("username_property_row")
                scrolled_page.username_property_value_entry = builder.get_object("username_property_value_entry")
                scrolled_page.username_property_value_entry.set_buffer(HistoryEntryBuffer([]))
                safe_entry.bind_property(
                    "username", scrolled_page.username_property_value_entry, "text",
                    GObject.BindingFlags.SYNC_CREATE
                    | GObject.BindingFlags.BIDIRECTIONAL)
                self.unlocked_database.bind_accelerator(
                    scrolled_page.username_property_value_entry,
                    "<Control><Shift>b",
                    signal="copy-clipboard")
                scrolled_page.username_property_value_entry.connect("copy-clipboard", self._on_copy_secondary_button_clicked)

                scrolled_page.username_property_value_entry.connect(
                    "icon-press", self._on_copy_secondary_button_clicked)
                properties_list_box.add(scrolled_page.username_property_row)
            elif scrolled_page.username_property_row:
                safe_entry.bind_property(
                    "username", scrolled_page.username_property_value_entry, "text",
                    GObject.BindingFlags.SYNC_CREATE
                    | GObject.BindingFlags.BIDIRECTIONAL)

                scrolled_page.username_property_value_entry.connect(
                    "icon-press", self._on_copy_secondary_button_clicked)

                self.unlocked_database.bind_accelerator(
                    scrolled_page.username_property_value_entry,
                    "<Control><Shift>b",
                    signal="copy-clipboard")
                scrolled_page.username_property_value_entry.connect("copy-clipboard", self._on_copy_secondary_button_clicked)
                properties_list_box.add(scrolled_page.username_property_row)

        if safe_entry.props.password or add_all:
            if scrolled_page.password_property_row is NotImplemented:
                scrolled_page.password_property_row = PasswordEntryRow(
                    self.unlocked_database)
                properties_list_box.add(scrolled_page.password_property_row)
            elif scrolled_page.password_property_row:
                properties_list_box.add(scrolled_page.password_property_row)

        if safe_entry.props.url or add_all:
            if scrolled_page.url_property_row is NotImplemented:
                scrolled_page.url_property_row = builder.get_object("url_property_row")
                scrolled_page.url_property_value_entry = builder.get_object("url_property_value_entry")
                scrolled_page.url_property_value_entry.set_buffer(HistoryEntryBuffer([]))
                safe_entry.bind_property(
                    "url", scrolled_page.url_property_value_entry, "text",
                    GObject.BindingFlags.SYNC_CREATE
                    | GObject.BindingFlags.BIDIRECTIONAL)
                scrolled_page.url_property_value_entry.connect("icon-press", self.on_link_secondary_button_clicked)
                properties_list_box.add(scrolled_page.url_property_row)
            elif scrolled_page.url_property_row:
                safe_entry.bind_property(
                    "url", scrolled_page.url_property_value_entry, "text",
                    GObject.BindingFlags.SYNC_CREATE
                    | GObject.BindingFlags.BIDIRECTIONAL)

                scrolled_page.url_property_value_entry.connect("icon-press", self.on_link_secondary_button_clicked)
                properties_list_box.add(scrolled_page.url_property_row)

        if safe_entry.props.notes or add_all:
            if scrolled_page.notes_property_row is NotImplemented:
                scrolled_page.notes_property_row = builder.get_object("notes_property_row")
                scrolled_page.notes_property_value_entry = builder.get_object("notes_property_value_entry")
                scrolled_page.notes_property_value_entry.get_style_context().add_class("codeview")

                builder.get_object("notes_detach_button").connect("clicked", self.on_notes_detach_button_clicked)

                textbuffer = HistoryTextBuffer([])
                safe_entry.bind_property(
                    "notes", textbuffer, "text",
                    GObject.BindingFlags.SYNC_CREATE
                    | GObject.BindingFlags.BIDIRECTIONAL)
                scrolled_page.notes_property_value_entry.set_buffer(textbuffer)
                properties_list_box.add(scrolled_page.notes_property_row)
            elif scrolled_page.notes_property_row:
                notes = safe_entry.props.notes
                textbuffer = scrolled_page.notes_property_value_entry.get_buffer()
                if not notes:
                    textbuffer.props.modified = False

                safe_entry.bind_property(
                    "notes", textbuffer, "text",
                    GObject.BindingFlags.SYNC_CREATE
                    | GObject.BindingFlags.BIDIRECTIONAL)
                properties_list_box.add(scrolled_page.notes_property_row)

        if safe_entry.props.color != Color.NONE.value or add_all:
            if scrolled_page.color_property_row is NotImplemented:
                scrolled_page.color_property_row = ColorEntryRow(
                    self.unlocked_database, safe_entry)

                properties_list_box.add(scrolled_page.color_property_row)
            elif scrolled_page.color_property_row is not NotImplemented:
                properties_list_box.add(scrolled_page.color_property_row)

        if safe_entry.props.icon or add_all:
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

                icon: str = safe_entry.props.icon
                if icon == "0":
                    key_button.set_active(True)
                elif icon == "19":
                    mail_icon_button.set_active(True)
                elif icon == "9":
                    profile_icon_button.set_active(True)
                elif icon == "1":
                    network_profile_button.set_active(True)
                elif icon == "30":
                    terminal_icon_button.set_active(True)
                elif icon == "34":
                    setting_icon_button.set_active(True)
                elif icon == "48":
                    folder_icon_button.set_active(True)
                elif icon == "27":
                    harddrive_icon_button.set_active(True)
                elif icon == "12":
                    wifi_icon_button.set_active(True)
                elif icon == "23":
                    desktop_icon_button.set_active(True)

                properties_list_box.add(scrolled_page.icon_property_row)
            elif scrolled_page.icon_property_row is not NotImplemented:
                properties_list_box.add(scrolled_page.icon_property_row)

        if scrolled_page.attachment_property_row is NotImplemented:
            scrolled_page.attachment_property_row = builder.get_object("attachment_property_row")
            scrolled_page.attachment_list_box = builder.get_object("attachment_list_box")
            for attachment in safe_entry.attachments:
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

        for key, value in safe_entry.attributes.items():
            self.add_attribute_property_row(key, value)

        # pylint: disable=too-many-boolean-expressions
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
        safe_entry = self.unlocked_database.current_element

        scrolled_page = self.unlocked_database.get_current_page()
        scrolled_page.is_dirty = True

        if type_name == "name":
            safe_entry.props.name = widget.props.text

        elif type_name == "username":
            safe_entry.props.username = widget.props.text
        elif type_name == "url":
            safe_entry.props.url = widget.props.text
        elif type_name == "notes":
            safe_entry.props.notes = widget.props.text

    def on_notes_detach_button_clicked(self, _button):
        self.unlocked_database.start_database_lock_timer()
        NotesDialog(self.unlocked_database).present()

    def on_entry_icon_button_toggled(self, button):
        if button.get_active() is False:
            return

        self.unlocked_database.start_database_lock_timer()
        safe_entry = self.unlocked_database.current_element
        new_icon: str = button.get_name()
        safe_entry.props.icon = new_icon

        scrolled_page = self.unlocked_database.get_current_page()
        scrolled_page.is_dirty = True

    def on_link_secondary_button_clicked(self, widget, _position, _eventbutton):
        self.unlocked_database.start_database_lock_timer()
        Gtk.show_uri_on_window(self.unlocked_database.window, widget.get_text(), Gtk.get_current_event_time())

    #
    # Additional Attributes
    #

    def on_attributes_add_button_clicked(self, _widget):
        safe_entry: SafeEntry = self.unlocked_database.current_element
        scrolled_page = self.unlocked_database.get_current_page()

        key = scrolled_page.attributes_key_entry.get_text()
        value = scrolled_page.attributes_value_entry.get_text()

        if key == "" or key is None:
            scrolled_page.attributes_key_entry.get_style_context().add_class("error")
            return

        if safe_entry.has_attribute(key):
            scrolled_page.attributes_key_entry.get_style_context().add_class("error")
            self.unlocked_database.show_database_action_revealer(_("Attribute key already exists"))
            return

        scrolled_page.attributes_key_entry.get_style_context().remove_class("error")

        scrolled_page.attributes_key_entry.set_text("")
        scrolled_page.attributes_value_entry.set_text("")

        safe_entry.set_attribute(key, value)
        self.add_attribute_property_row(key, value)

    def on_attribute_remove_button_clicked(self, button):
        safe_entry: SafeEntry = self.unlocked_database.current_element
        scrolled_page = self.unlocked_database.get_current_page()

        parent = button.get_parent().get_parent().get_parent()
        key = parent.get_name()

        safe_entry.delete_attribute(key)
        scrolled_page.properties_list_box.remove(parent)

    def on_attributes_value_entry_changed(self, widget):
        safe_entry = self.unlocked_database.current_element

        parent = widget.get_parent().get_parent().get_parent()
        key = parent.get_name()
        safe_entry.set_attribute(key, widget.get_text())

    def on_attribute_key_edit_button_clicked(self, button):
        safe_entry: SafeEntry = self.unlocked_database.current_element

        parent = button.get_parent().get_parent().get_parent()
        key = parent.get_name()

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

        key_entry = builder.get_object("key_entry")
        key_entry.connect(
            "activate", self.on_key_entry_activated, safe_entry, key, button, parent)
        key_entry.set_text(key)

        attribute_entry_box = button.get_parent()
        attribute_entry_box.remove(button)
        attribute_entry_box.add(key_entry)
        attribute_entry_box.reorder_child(key_entry, 0)
        key_entry.grab_focus()

    def on_key_entry_activated(
            self, widget: Gtk.Entry, safe_entry: SafeEntry, key: str,
            button: Gtk.Button, parent: Gtk.Box) -> None:
        # pylint: disable=too-many-arguments
        new_key: str = widget.props.text
        if not new_key:
            widget.get_style_context().add_class("error")
            return

        if new_key == key:
            attribute_entry_box = widget.get_parent()
            attribute_entry_box.remove(widget)
            attribute_entry_box.add(button)
            attribute_entry_box.reorder_child(button, 0)
            return

        if safe_entry.has_attribute(new_key):
            widget.get_style_context().add_class("error")
            self.unlocked_database.show_database_action_revealer(_("Attribute key already exists"))
            return

        safe_entry.set_attribute(new_key, safe_entry.props.attributes[key])
        safe_entry.delete_attribute(key)

        button.get_children()[0].set_text(new_key)
        parent.set_name(new_key)

        attribute_entry_box = widget.get_parent()
        attribute_entry_box.remove(widget)
        attribute_entry_box.add(button)
        attribute_entry_box.reorder_child(button, 0)

    #
    # Attachment Handling
    #

    def on_attachment_list_box_activated(self, _widget, list_box_row):
        if list_box_row.get_name() == "AddAttachmentRow":
            self.on_add_attachment_row_clicked()
        else:
            safe_entry: SafeEntry = self.unlocked_database.current_element
            attachment = safe_entry.get_attachment(list_box_row.get_name())
            self.on_attachment_row_clicked(attachment)

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
            safe_entry: SafeEntry = self.unlocked_database.current_element
            for uri in select_dialog.get_uris():
                attachment = Gio.File.new_for_uri(uri)
                byte_buffer = attachment.load_bytes()[0].get_data()
                filename = attachment.get_basename()
                new_attachment = safe_entry.add_attachment(byte_buffer, filename)
                self.add_attachment_row(new_attachment)

    def add_attachment_row(self, attachment):
        scrolled_page = self.unlocked_database.get_current_page()

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")

        attachment_row = builder.get_object("attachment_row")
        attachment_row.set_name(str(attachment.id))
        builder.get_object("attachment_label").set_label(attachment.filename)
        builder.get_object("attachment_download_button").connect(
            "clicked", self.on_attachment_download_button_clicked, attachment
        )
        builder.get_object("attachment_delete_button").connect(
            "clicked",
            self.on_attachment_delete_button_clicked,
            attachment,
            attachment_row,
        )

        scrolled_page.attachment_list_box.insert(attachment_row, len(scrolled_page.attachment_list_box) - 1)

    def on_attachment_row_clicked(self, attachment):
        AttachmentWarningDialog(self, attachment).present()

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
            safe_entry: SafeEntry = self.unlocked_database.current_element
            bytes_buffer = safe_entry.get_attachment_content(attachment)
            self.save_to_disk(save_dialog.get_filename(), bytes_buffer)

    def on_attachment_delete_button_clicked(
            self, _button, attachment_to_delete, attachment_row):
        safe_entry: SafeEntry = self.unlocked_database.current_element
        safe_entry.delete_attachment(attachment_to_delete)
        attachment_row.destroy()

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/entry_page.ui")
        scrolled_page = self.unlocked_database.get_current_page()

        for row in scrolled_page.attachment_list_box.get_children():
            if row.get_name() != "AddAttachmentRow":
                row.destroy()

        for attachment in safe_entry.props.attachments:
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

    def _on_copy_secondary_button_clicked(
            self, widget, _position=None, _eventbutton=None):
        self.unlocked_database.send_to_clipboard(widget.get_text())
