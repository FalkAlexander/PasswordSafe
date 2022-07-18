# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from gettext import gettext as _

import validators
from gi.repository import Gdk, GLib, GObject, Gtk

from gsecrets.attachment_warning_dialog import AttachmentWarningDialog
from gsecrets.color_widget import ColorEntryRow
from gsecrets.password_entry_row import PasswordEntryRow
from gsecrets.pathbar import Pathbar
from gsecrets.safe_element import ICONS
from gsecrets.widgets.add_attribute_dialog import AddAttributeDialog
from gsecrets.widgets.attachment_entry_row import AttachmentEntryRow
from gsecrets.widgets.attribute_entry_row import AttributeEntryRow
from gsecrets.widgets.entry_page_icon import EntryPageIcon
from gsecrets.widgets.notes_dialog import NotesDialog

if typing.TYPE_CHECKING:
    from gsecrets.safe_element import SafeEntry


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/entry_page.ui")
class EntryPage(Gtk.Box):
    # pylint: disable=too-many-public-methods

    __gtype_name__ = "EntryPage"

    _pathbar_bin = Gtk.Template.Child()

    title_entry_row = Gtk.Template.Child()
    username_entry_row = Gtk.Template.Child()

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

    attribute_list_box = Gtk.Template.Child()
    attributes_property_box = Gtk.Template.Child()

    expiration_date_property_box = Gtk.Template.Child()
    expiration_date_row = Gtk.Template.Child()

    show_all_button = Gtk.Template.Child()

    otp_timer_handler: int | None = None

    def __init__(self, u_d, add_all):
        # Setup actions, must be done before initializing the template.
        self.install_action("entry.copy_password", None, self._on_copy_action)
        self.install_action("entry.copy_user", None, self._on_copy_action)
        self.install_action("entry.copy_otp", None, self._on_copy_action)
        self.install_action("entry.copy_url", None, self._on_copy_action)
        self.install_action(
            "entry.add_attribute", None, self._on_attributes_add_button_activated
        )

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

        self._pathbar_bin.set_child(Pathbar(u_d))

        u_d.pathbar.bind_property(
            "visible",
            self._pathbar_bin,
            "visible",
            GObject.BindingFlags.SYNC_CREATE,
        )

        self.insert_entry_properties_into_listbox(add_all)

        safe_entry: SafeEntry = self.unlocked_database.current_element
        safe_entry.updated.connect(self._on_safe_entry_updated)

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
            self.title_entry_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        # Username
        safe_entry.bind_property(
            "username",
            self.username_entry_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        value = safe_entry.username != ""

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
                self.show_all_button.set_visible(True)
                break

    def add_attribute_property_row(self, key, value):
        """Add an attribute to the attributes list view.

        :param str key: property name
        :param str value: property value
        """
        safe_entry = self.unlocked_database.current_element
        attribute_row = AttributeEntryRow(
            safe_entry, key, value, self.attribute_list_box
        )

        self.attribute_list_box.prepend(attribute_row)

    #
    # Events
    #

    def _on_copy_action(self, _widget, action_name, _parameter):
        if self.unlocked_database.props.database_locked:
            return

        if action_name == "entry.copy_user":
            username = self.username_entry_row.props.text
            self.unlocked_database.send_to_clipboard(
                username,
                _("Username copied"),
            )
        elif action_name == "entry.copy_password":
            self.password_entry_row.copy_password()
        elif action_name == "entry.copy_url":
            url = self.url_property_value_entry.get_text()
            self.unlocked_database.send_to_clipboard(
                url,
                _("Address copied"),
            )
        elif action_name == "entry.copy_otp":
            safe_entry: SafeEntry = self.unlocked_database.current_element
            otp_token = safe_entry.otp_token() or ""
            if otp_token == "":
                return

            self.unlocked_database.send_to_clipboard(
                otp_token,
                _("One-time password copied"),
            )

    @Gtk.Template.Callback()
    def on_show_all_properties_button_clicked(self, _widget):
        self.unlocked_database.start_database_lock_timer()

        for widget in self.toggeable_widget_list:
            widget.set_visible(True)

        self.show_all_button.set_visible(False)

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
    def on_visit_url_button_clicked(self, _button):
        self.unlocked_database.start_database_lock_timer()
        url = self.url_property_value_entry.get_text()
        window = self.unlocked_database.window
        if validators.url(url):
            Gtk.show_uri(window, url, Gdk.CURRENT_TIME)
        else:
            url = "https://" + url
            if validators.url(url):
                Gtk.show_uri(window, url, Gdk.CURRENT_TIME)
            else:
                window.send_notification(_("The address is not valid"))

    @Gtk.Template.Callback()
    def on_otp_copy_button_clicked(self, _button):
        safe_entry: SafeEntry = self.unlocked_database.current_element
        otp_token = safe_entry.otp_token() or ""
        self.unlocked_database.send_to_clipboard(
            otp_token,
            _("One-time password copied"),
        )

    def _on_attributes_add_button_activated(self, _widget, _action_name, _pspec):
        window = self.unlocked_database.window
        entry = self.unlocked_database.current_element
        db_manager = self.unlocked_database.database_manager
        dialog = AddAttributeDialog(window, db_manager, entry)

        def on_add_attribute(_dialog, key, value):
            self.add_attribute_property_row(key, value)

        dialog.connect("add_attribute", on_add_attribute)
        dialog.present()

    #
    # Attachment Handling
    #

    @Gtk.Template.Callback()
    def on_attachment_list_box_activated(self, _widget, list_box_row):
        self.unlocked_database.start_database_lock_timer()
        if list_box_row.get_name() == "AddAttachmentRow":
            self.on_add_attachment_row_clicked()
        else:
            attachment = list_box_row.attachment
            AttachmentWarningDialog(self, attachment).present()

    def on_add_attachment_row_clicked(self):
        self.unlocked_database.start_database_lock_timer()
        select_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for selecting attachment file
            _("Select Attachment"),
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
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            safe_entry: SafeEntry = self.unlocked_database.current_element

            def callback(gfile, result):
                try:
                    gbytes, _stream = gfile.load_bytes_finish(result)
                except GLib.Error as err:
                    logging.debug("Could not read attachment: %s", err.message)
                else:
                    filename = gfile.get_basename()
                    data = gbytes.get_data()
                    new_attachment = safe_entry.add_attachment(data, filename)
                    self.add_attachment_row(new_attachment)

            for attachment in dialog.get_files():
                attachment.load_bytes_async(None, callback)

    def add_attachment_row(self, attachment):
        safe_entry: SafeEntry = self.unlocked_database.current_element
        attachment_row = AttachmentEntryRow(safe_entry, attachment)
        self.attachment_list_box.prepend(attachment_row)

    @Gtk.Template.Callback()
    def _on_username_copy_button_clicked(self, _button):
        username = self.username_entry_row.props.text
        self.unlocked_database.send_to_clipboard(
            username,
            _("Username copied"),
        )

    @Gtk.Template.Callback()
    def on_copy_url_button_clicked(self, widget, _icon_pos, _data=None):
        self.unlocked_database.send_to_clipboard(
            widget.get_text(),
            _("Address copied"),
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
        self.otp_error_revealer.reveal(reveal_error)

        return GLib.SOURCE_CONTINUE
