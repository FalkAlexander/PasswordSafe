# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _
from logging import warning

from gi.repository import Gdk, Gio, GLib, GObject, Gtk

from passwordsafe.attachment_warning_dialog import AttachmentWarningDialog
from passwordsafe.color_widget import ColorEntryRow
from passwordsafe.password_entry_row import PasswordEntryRow
from passwordsafe.safe_element import ICONS
from passwordsafe.widgets.entry_page_icon import EntryPageIcon
from passwordsafe.widgets.progress_icon import ProgressIcon  # noqa: F401, pylint: disable=unused-import
from passwordsafe.widgets.notes_dialog import NotesDialog
from passwordsafe.widgets.expiration_date_row import ExpirationDateRow  # noqa: F401, pylint: disable=unused-import

if typing.TYPE_CHECKING:
    from passwordsafe.safe_element import SafeEntry
    from pykeepass.attachment import Attachment


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/entry_page.ui")
class EntryPage(Gtk.ScrolledWindow):
    # pylint: disable=too-many-public-methods

    __gtype_name__ = "EntryPage"

    name_property_value_entry = Gtk.Template.Child()

    username_property_value_entry = Gtk.Template.Child()

    password_property_bin = Gtk.Template.Child()

    otp_token_box = Gtk.Template.Child()
    otp_token_row = Gtk.Template.Child()
    otp_progress_icon = Gtk.Template.Child()

    url_property_box = Gtk.Template.Child()
    url_property_value_entry = Gtk.Template.Child()

    otp_error_revealer = Gtk.Template.Child()
    otp_property_box = Gtk.Template.Child()
    otp_property_value_entry = Gtk.Template.Child()

    notes_property_box = Gtk.Template.Child()
    notes_property_value_entry = Gtk.Template.Child()

    color_property_bin = Gtk.Template.Child()

    icon_entry_box = Gtk.Template.Child()

    attachment_property_box = Gtk.Template.Child()
    attachment_list_box = Gtk.Template.Child()

    attributes_key_entry = Gtk.Template.Child()
    attribute_list_box = Gtk.Template.Child()
    attributes_property_box = Gtk.Template.Child()
    attributes_value_entry = Gtk.Template.Child()

    expiration_date_property_box = Gtk.Template.Child()
    expiration_date_row = Gtk.Template.Child()

    show_all_row = Gtk.Template.Child()

    attribute_property_row_list: list[Gtk.ListBoxRow] = []
    otp_timer_handler: int | None = None

    def __init__(self, u_d, add_all):
        super().__init__()

        self.unlocked_database = u_d
        self.toggeable_widget_list = [
            self.url_property_box,
            self.otp_property_box,
            self.notes_property_box,
            self.attachment_property_box,
            self.attributes_property_box,
            self.expiration_date_property_box,
        ]

        self.insert_entry_properties_into_listbox(add_all)

        safe_entry: SafeEntry = self.unlocked_database.current_element
        safe_entry.connect("updated", self._on_safe_entry_updated)

        # Setup actions
        copy_user_action = Gio.SimpleAction.new("entry.copy_user", None)
        copy_user_action.connect("activate", self._on_copy_action)
        self.unlocked_database.window.add_action(copy_user_action)

        copy_password_action = Gio.SimpleAction.new("entry.copy_password", None)
        copy_password_action.connect("activate", self._on_copy_action)
        self.unlocked_database.window.add_action(copy_password_action)

    def do_unroot(self) -> None:  # pylint: disable=arguments-differ
        if self.otp_timer_handler is not None:
            GLib.source_remove(self.otp_timer_handler)
            self.otp_timer_handler = None

        Gtk.Widget.do_unroot(self)

    def insert_entry_properties_into_listbox(self, add_all):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        safe_entry: SafeEntry = self.unlocked_database.current_element

        # Create the name_property_row
        safe_entry.bind_property(
            "name",
            self.name_property_value_entry,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        self.name_property_value_entry.props.enable_undo = True

        # Username
        safe_entry.bind_property(
            "username",
            self.username_property_value_entry,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        value = safe_entry.username != ""
        self.username_property_value_entry.props.enable_undo = True

        # Password
        self.password_entry_row = PasswordEntryRow(self.unlocked_database)
        self.password_property_bin.set_child(self.password_entry_row)

        # OTP (token)
        safe_entry.connect("notify::otp", self.otp_update)
        if safe_entry.otp_token():
            self.otp_update(safe_entry, None)
            self.show_row(self.otp_token_box, True, add_all)

        # Url
        safe_entry.bind_property(
            "url",
            self.url_property_value_entry,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        self.show_row(self.url_property_box, safe_entry.url, add_all)
        self.url_property_value_entry.props.enable_undo = True

        # OTP (secret)
        safe_entry.bind_property(
            "otp",
            self.otp_property_value_entry,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        self.show_row(self.otp_property_box, False, add_all)

        # Notes
        self.notes_property_value_entry.add_css_class("codeview")

        textbuffer = self.notes_property_value_entry.get_buffer()
        safe_entry.bind_property(
            "notes",
            textbuffer,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        self.notes_property_value_entry.set_buffer(textbuffer)
        self.show_row(self.notes_property_box, safe_entry.notes, add_all)

        # Color
        self.color_property_bin.set_child(
            ColorEntryRow(self.unlocked_database, safe_entry)
        )

        # Icons
        entry_icon = safe_entry.props.icon
        for icon_nr, icon in ICONS.items():
            if not icon.visible:
                continue

            btn = EntryPageIcon(icon.name, icon_nr)
            self.icon_entry_box.insert(btn, -1)

            if entry_icon == icon:
                self.icon_entry_box.select_child(btn)

        self.icon_entry_box.connect(
            "selected-children-changed", self.on_entry_icon_button_toggled
        )

        # Attachments
        for attachment in safe_entry.attachments:
            self.add_attachment_row(attachment)

        self.show_row(self.attachment_property_box, safe_entry.attachments, add_all)

        # Attributes
        self.show_row(self.attributes_property_box, safe_entry.attributes, add_all)

        for key, value in safe_entry.attributes.items():
            self.add_attribute_property_row(key, value)

        # Expiration Date
        self.expiration_date_row.props.safe_entry = safe_entry
        self.show_row(self.expiration_date_property_box, safe_entry.expires, add_all)

        # Show more row
        for widget in self.toggeable_widget_list:
            if not widget.get_visible():
                self.show_all_row.set_visible(True)
                break

    def add_attribute_property_row(self, key, value):
        """Add an attribute to the attributes list view.

        :param str key: property name
        :param str value: property value
        """
        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/PasswordSafe/attribute_entry_row.ui"
        )

        attribute_row = builder.get_object("attribute_row")
        attribute_key_edit_button = builder.get_object("attribute_key_edit_button")
        attribute_value_entry = builder.get_object("attribute_value_entry")
        attribute_remove_button = builder.get_object("attribute_remove_button")

        attribute_key_edit_button.set_label(key)
        if value is not None:
            attribute_value_entry.set_text(value)
        attribute_remove_button.connect(
            "clicked", self.on_attribute_remove_button_clicked, key
        )
        attribute_key_edit_button.connect(
            "clicked", self.on_attribute_key_edit_button_clicked
        )
        attribute_value_entry.connect(
            "changed", self.on_attributes_value_entry_changed, key
        )

        self.attribute_list_box.append(attribute_row)
        self.attribute_property_row_list.append(attribute_row)

    #
    # Events
    #

    def _on_copy_action(self, action, _data=None):
        if action.props.name == "entry.copy_user":
            username = self.username_property_value_entry.get_text()
            self.unlocked_database.send_to_clipboard(
                username,
                _("Username copied to clipboard"),
            )
        elif action.props.name == "entry.copy_password":
            self.password_entry_row.copy_password()

    @Gtk.Template.Callback()
    def on_show_all_properties_button_clicked(self, _widget):
        self.unlocked_database.start_database_lock_timer()

        for widget in self.toggeable_widget_list:
            widget.set_visible(True)

        self.show_all_row.set_visible(False)

    @Gtk.Template.Callback()
    def on_notes_detach_button_clicked(self, _button):
        self.unlocked_database.start_database_lock_timer()
        safe_entry = self.unlocked_database.current_element
        NotesDialog(self.unlocked_database, safe_entry).present()

    def on_entry_icon_button_toggled(self, flowbox):
        if not flowbox.get_selected_children():
            return

        selected_row = flowbox.get_selected_children()[0]
        icon = selected_row.get_name()

        safe_entry = self.unlocked_database.current_element
        safe_entry.props.icon = icon

    @Gtk.Template.Callback()
    def on_link_secondary_button_clicked(self, widget, _position, _data=None):
        self.unlocked_database.start_database_lock_timer()
        Gtk.show_uri(self.unlocked_database.window, widget.get_text(), Gdk.CURRENT_TIME)

    @Gtk.Template.Callback()
    def on_otp_copy_button_clicked(self, _button):
        safe_entry: SafeEntry = self.unlocked_database.current_element
        otp_token = safe_entry.otp_token() or ""
        self.unlocked_database.send_to_clipboard(
            otp_token,
            _("One-time password copied to clipboard"),
        )

    #
    # Additional Attributes
    #

    @Gtk.Template.Callback()
    def on_attributes_add_button_clicked(self, _widget):
        safe_entry: SafeEntry = self.unlocked_database.current_element

        key = self.attributes_key_entry.get_text()
        value = self.attributes_value_entry.get_text()

        if key == "" or key is None:
            self.attributes_key_entry.add_css_class("error")
            return

        if safe_entry.has_attribute(key):
            self.attributes_key_entry.add_css_class("error")
            self.unlocked_database.window.send_notification(
                _("Attribute key already exists")
            )
            return

        self.attributes_key_entry.remove_css_class("error")

        self.attributes_key_entry.set_text("")
        self.attributes_value_entry.set_text("")

        safe_entry.set_attribute(key, value)
        self.add_attribute_property_row(key, value)

    def on_attribute_remove_button_clicked(self, button, key):
        safe_entry: SafeEntry = self.unlocked_database.current_element

        attribute_row = button.get_parent().get_parent()
        safe_entry.delete_attribute(key)
        self.attribute_list_box.remove(attribute_row)

    def on_attributes_value_entry_changed(self, widget, key):
        safe_entry = self.unlocked_database.current_element
        safe_entry.set_attribute(key, widget.get_text())

    def on_attribute_key_edit_button_clicked(self, button):
        safe_entry: SafeEntry = self.unlocked_database.current_element
        parent = button.get_parent()

        parent = button.get_parent().get_parent().get_parent()
        key = button.get_label()

        key_entry = Gtk.Entry()
        key_entry.set_visible(True)

        key_entry.connect(
            "activate", self.on_key_entry_activated, safe_entry, key, button, parent
        )
        key_entry.set_text(key)

        attribute_entry_box = button.get_parent()
        attribute_entry_box.remove(button)
        attribute_entry_box.append(key_entry)
        key_entry.grab_focus()

    def on_key_entry_activated(
        self,
        widget: Gtk.Entry,
        safe_entry: SafeEntry,
        key: str,
        button: Gtk.Button,
        parent: Gtk.Box,
    ) -> None:
        # pylint: disable=too-many-arguments
        new_key: str = widget.props.text
        if not new_key:
            widget.add_css_class("error")
            return

        if new_key == key:
            attribute_entry_box = widget.get_parent()
            attribute_entry_box.remove(widget)
            attribute_entry_box.append(button)
            return

        if safe_entry.has_attribute(new_key):
            widget.add_css_class("error")
            self.unlocked_database.window.send_notification(
                _("Attribute key already exists")
            )
            return

        safe_entry.set_attribute(new_key, safe_entry.props.attributes[key])
        safe_entry.delete_attribute(key)

        button.set_label(new_key)
        parent.set_name(new_key)

        attribute_entry_box = widget.get_parent()
        attribute_entry_box.remove(widget)
        attribute_entry_box.append(button)

    #
    # Attachment Handling
    #

    @Gtk.Template.Callback()
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
            _("Select attachment"),
            self.unlocked_database.window,
            Gtk.FileChooserAction.OPEN,
            _("_Add"),
            None,
        )
        select_dialog.set_modal(True)
        select_dialog.set_select_multiple(True)

        select_dialog.connect(
            "response", self._on_select_filechooser_response, select_dialog
        )
        select_dialog.show()

    def _on_select_filechooser_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType, _dialog: Gtk.Dialog
    ) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            safe_entry: SafeEntry = self.unlocked_database.current_element
            for attachment in dialog.get_files():
                try:
                    byte_buffer = attachment.load_bytes()[0].get_data()
                    filename = attachment.get_basename()
                    new_attachment = safe_entry.add_attachment(byte_buffer, filename)
                    self.add_attachment_row(new_attachment)
                except GLib.Error as err:
                    warning(
                        "Could not create new keyfile %s: %s",
                        filename,
                        err.message,
                    )

    def add_attachment_row(self, attachment):
        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/PasswordSafe/attachment_entry_row.ui"
        )

        attachment_row = builder.get_object("attachment_row")
        attachment_row.set_name(str(attachment.id))
        attachment_row.set_title(attachment.filename)
        builder.get_object("attachment_download_button").connect(
            "clicked", self.on_attachment_download_button_clicked, attachment
        )
        builder.get_object("attachment_delete_button").connect(
            "clicked",
            self.on_attachment_delete_button_clicked,
            attachment,
            attachment_row,
        )

        self.attachment_list_box.prepend(attachment_row)

    def on_attachment_row_clicked(self, attachment):
        AttachmentWarningDialog(self, attachment).present()

    def on_attachment_download_button_clicked(self, _button, attachment):
        save_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for downloading an attachment
            _("Save attachment"),
            self.unlocked_database.window,
            Gtk.FileChooserAction.SAVE,
            _("_Save"),
            None,
        )
        save_dialog.set_current_name(attachment.filename)
        save_dialog.set_modal(True)

        save_dialog.connect(
            "response", self._on_save_filechooser_response, attachment, save_dialog
        )
        save_dialog.show()

    def _on_save_filechooser_response(
        self,
        dialog: Gtk.Dialog,
        response: Gtk.ResponseType,
        attachment: Attachment,
        _dialog: Gtk.Dialog,
    ) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            safe_entry: SafeEntry = self.unlocked_database.current_element
            bytes_buffer = safe_entry.get_attachment_content(attachment)
            stream = Gio.File.replace(
                dialog.get_file(),
                None,
                False,
                Gio.FileCreateFlags.PRIVATE | Gio.FileCreateFlags.REPLACE_DESTINATION,
                None,
            )
            Gio.OutputStream.write_bytes(stream, GLib.Bytes.new(bytes_buffer), None)
            stream.close()

    def on_attachment_delete_button_clicked(
        self, _button, attachment_to_delete, attachment_row
    ):
        safe_entry: SafeEntry = self.unlocked_database.current_element
        safe_entry.delete_attachment(attachment_to_delete)

        self.attachment_list_box.remove(attachment_row)

    @Gtk.Template.Callback()
    def _on_copy_secondary_button_clicked(self, widget, _icon_pos, _data=None):
        self.unlocked_database.send_to_clipboard(
            widget.get_text(),
            _("Username copied to clipboard"),
        )

    def show_row(self, row: Gtk.ListBoxRow, non_empty: bool, add_all: bool) -> None:
        if non_empty or add_all:
            row.set_visible(True)
        else:
            row.set_visible(False)

    def _on_safe_entry_updated(self, _safe_entry: SafeEntry) -> None:
        self.unlocked_database.start_database_lock_timer()

    def otp_update(self, safe_entry, _value):
        otp_token = safe_entry.otp_token()

        if self.otp_timer_handler is not None:
            GLib.source_remove(self.otp_timer_handler)
            self.otp_timer_handler = None

        if otp_token:
            remaining_time = safe_entry.otp_lifespan() / safe_entry.otp_interval()
            self.otp_progress_icon.props.progress = remaining_time
            self.otp_token_box.props.visible = True
            self.otp_token_row.props.title = otp_token
            self.otp_timer_handler = GObject.timeout_add(
                100, self.otp_update, safe_entry, None
            )
        else:
            self.otp_token_box.props.visible = False

        reveal_error = not otp_token and safe_entry.props.otp
        self.otp_error_revealer.props.reveal_child = reveal_error

        return GLib.SOURCE_CONTINUE
