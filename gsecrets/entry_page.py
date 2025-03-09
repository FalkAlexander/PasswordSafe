# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from gettext import gettext as _

import validators
from gi.repository import Adw, GLib, GObject, Gtk

from gsecrets.attachment_warning_dialog import AttachmentWarningDialog
from gsecrets.color_widget import ColorEntryRow
from gsecrets.safe_element import ICONS, SafeEntry
from gsecrets.widgets.add_attribute_dialog import AddAttributeDialog
from gsecrets.widgets.attachment_entry_row import AttachmentEntryRow
from gsecrets.widgets.attribute_entry_row import AttributeEntryRow
from gsecrets.widgets.entry_page_icon import EntryPageIcon
from gsecrets.widgets.entry_page_tag import EntryPageTag
from gsecrets.widgets.history_window import HistoryWindow
from gsecrets.widgets.notes_dialog import NotesDialog
from gsecrets.widgets.protected_attribute_entry_row import ProtectedAttributeEntryRow

if typing.TYPE_CHECKING:
    from gi.repository import Gio
    from pykeepass.attachment import Attachment

    from gsecrets.safe_element import SafeElement
    from gsecrets.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/entry_page.ui")
class EntryPage(Adw.Bin):
    # pylint: disable=too-many-public-methods

    __gtype_name__ = "EntryPage"

    title_entry_row = Gtk.Template.Child()
    url_entry_row = Gtk.Template.Child()

    credentials_group = Gtk.Template.Child()

    otp_error_revealer = Gtk.Template.Child()
    otp_preferences_group = Gtk.Template.Child()
    otp_progress_icon = Gtk.Template.Child()
    otp_secret_entry_row = Gtk.Template.Child()
    otp_token_row = Gtk.Template.Child()

    notes_preferences_group = Gtk.Template.Child()
    notes_property_value_entry = Gtk.Template.Child()

    color_property_bin = Gtk.Template.Child()

    icon_entry_box = Gtk.Template.Child()

    _tags_group = Gtk.Template.Child()
    _tag_entry_box = Gtk.Template.Child()

    attachments_preferences_group = Gtk.Template.Child()
    attachment_list_box = Gtk.Template.Child()

    attribute_list_box = Gtk.Template.Child()
    attributes_preferences_group = Gtk.Template.Child()

    expiration_date_preferences_group = Gtk.Template.Child()
    expiration_date_row = Gtk.Template.Child()

    _window_title = Gtk.Template.Child()

    show_all_preferences_group = Gtk.Template.Child()

    otp_timer_handler: int | None = None

    safe_entry = GObject.Property(type=SafeEntry)

    _tags: list[EntryPageTag] = []

    def __init__(
        self,
        u_d: UnlockedDatabase,
        entry: SafeElement,
        add_all: bool,
    ) -> None:
        # Setup actions, must be done before initializing the template.
        self.install_action("entry.copy_password", None, self._on_copy_action)
        self.install_action("entry.copy_user", None, self._on_copy_action)
        self.install_action("entry.copy_otp", None, self._on_copy_action)
        self.install_action("entry.copy_url", None, self._on_copy_action)
        self.install_action("entry.add_attribute", None, self._on_add_attribute)
        self.install_action("entry.add_attachment", None, self._on_add_attachment)
        self.install_action(
            "entry.password_history",
            None,
            self._on_password_history_action,
        )
        self.install_action(
            "entry.save_in_history",
            None,
            self._on_save_in_history_action,
        )

        super().__init__(safe_entry=entry)

        self.unlocked_database = u_d
        self.toggeable_widget_list = [
            self.otp_preferences_group,
            self.notes_preferences_group,
            self.attachments_preferences_group,
            self.attributes_preferences_group,
            self.expiration_date_preferences_group,
            self._tags_group,
        ]

        self.insert_entry_properties_into_listbox(add_all)

        safe_entry: SafeEntry = self.props.safe_entry
        safe_entry.updated.connect(self._on_safe_entry_updated)

        safe_entry.history_saved.connect(self._on_history_saved)
        if not safe_entry.history:
            self.action_set_enabled("entry.password_history", False)

        safe_entry.connect("notify::name", self._on_name_notify)
        self._set_title(safe_entry)

    def _set_title(self, entry):
        if entry.parentgroup.is_root_group:
            title = entry.name
        else:
            title = f"{entry.parentgroup.name} ⟩ {entry.name}"

        self._window_title.props.title = title

    def _on_name_notify(self, entry, _pspec):
        self._set_title(entry)

    def do_unroot(self) -> None:  # pylint: disable=arguments-differ
        if self.otp_timer_handler is not None:
            GLib.source_remove(self.otp_timer_handler)
            self.otp_timer_handler = None

        Gtk.Widget.do_unroot(self)

    def insert_entry_properties_into_listbox(self, add_all: bool) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        safe_entry = self.props.safe_entry

        # Create the name_property_row
        safe_entry.bind_property(
            "name",
            self.title_entry_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        # Credentials Group
        self.credentials_group.unlocked_database = self.unlocked_database
        self.credentials_group.props.entry = self.props.safe_entry

        # OTP token
        safe_entry.connect("notify::otp", self.otp_update)
        if safe_entry.otp_token():
            self.otp_update(safe_entry, None)
            self.show_row(self.otp_preferences_group, True, add_all)

        # Url
        safe_entry.bind_property(
            "url",
            self.url_entry_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        # OTP secret
        safe_entry.bind_property(
            "otp",
            self.otp_secret_entry_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        # Notes
        textbuffer = self.notes_property_value_entry.get_buffer()
        safe_entry.bind_property(
            "notes",
            textbuffer,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        self.notes_property_value_entry.set_buffer(textbuffer)
        self.show_row(self.notes_preferences_group, safe_entry.notes, add_all)

        # Color
        self.color_property_bin.set_child(
            ColorEntryRow(self.unlocked_database, safe_entry),
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
            "selected-children-changed",
            self.on_entry_icon_button_toggled,
        )

        # Tags
        self._update_tags()
        self.show_row(self._tags_group, bool(safe_entry.tags), add_all)

        # Attachments
        for attachment in safe_entry.attachments:
            self.add_attachment_row(attachment)

        self.show_row(
            self.attachments_preferences_group,
            safe_entry.attachments,
            add_all,
        )

        # Attributes
        self.show_row(self.attributes_preferences_group, safe_entry.attributes, add_all)

        def factory(item):
            key, value = item.key, item.value
            if safe_entry.is_attribute_protected(key):
                return ProtectedAttributeEntryRow(safe_entry, key, value).row

            return AttributeEntryRow(safe_entry, key, value)

        self.attribute_list_box.set_model(safe_entry.attributes, factory)

        # Expiration Date
        self.expiration_date_row.props.safe_entry = safe_entry
        self.show_row(
            self.expiration_date_preferences_group,
            safe_entry.expires,
            add_all,
        )

        # Show more row
        for widget in self.toggeable_widget_list:
            if not widget.get_visible():
                self.show_all_preferences_group.props.visible = True
                break

    def _update_tags(self):
        safe_entry = self.props.safe_entry

        for tag in self._tags:
            self._tag_entry_box.remove(tag)

        self._tags = []

        if safe_entry.tags:
            for tag in safe_entry.tags:
                widget = EntryPageTag(tag)
                widget.remove_button.connect(
                    "clicked",
                    self._on_remove_button_clicked,
                    tag,
                )
                self._tag_entry_box.append(widget)
                self._tags.append(widget)

    def _on_remove_button_clicked(self, _button, tag_name):
        safe_entry = self.props.safe_entry
        # Remove
        tags = safe_entry.tags
        tags.remove(tag_name)
        safe_entry.tags = tags if tags else ""

        # Update tag flowbox
        self._update_tags()

    @Gtk.Template.Callback()
    def _on_tag_add_clicked(self, _widget):
        entry = Adw.EntryRow()
        entry.props.activates_default = True
        entry.props.title = _("Enter tag name")

        group = Adw.PreferencesGroup()
        group.add(entry)

        dialog = Adw.AlertDialog.new()
        dialog.set_heading(_("Add New Tag"))
        dialog.add_response("cancel", _("_Cancel"))
        dialog.add_response("add", _("_Add"))
        dialog.set_default_response("add")
        dialog.set_close_response("cancel")
        dialog.set_extra_child(group)

        dialog.connect("response::add", self._on_tag_add_response, entry)
        dialog.present(self.unlocked_database.window)

        entry.grab_focus()

    def _on_tag_add_response(
        self,
        _dialog: Adw.MessageDialog,
        _response: str,
        entry: Adw.EntryRow,
    ) -> None:
        tag_name = entry.props.text
        safe_entry = self.props.safe_entry
        tags = safe_entry.tags or []

        if tag_name in tags:
            window = self.unlocked_database.window
            window.send_notification(_("The tag already exists"))
            return

        tags.append(tag_name)
        safe_entry.tags = tags
        self._update_tags()

    #
    # Events
    #

    def _on_password_history_action(self, _widget, _action, _param):
        safe_entry = self.props.safe_entry

        window = HistoryWindow(safe_entry, self.unlocked_database)
        window.present(self)

    def _on_save_in_history_action(self, _widget, _action, _param):
        safe_entry = self.props.safe_entry
        safe_entry.save_history()

        self.unlocked_database.window.send_notification(_("Saved in history"))

    def _on_history_saved(self, entry):
        if not entry.history:
            self.action_set_enabled("entry.password_history", False)
        else:
            self.action_set_enabled("entry.password_history", True)

    def _on_copy_action(
        self,
        _widget: Gtk.Widget,
        action_name: str,
        _parameter: GLib.Variant,
    ) -> None:
        if self.unlocked_database.props.database_locked:
            return

        if action_name == "entry.copy_user":
            username = self.credentials_group.username
            self.unlocked_database.send_to_clipboard(username, _("Username copied"))
        elif action_name == "entry.copy_password":
            self.credentials_group.copy_password()
        elif action_name == "entry.copy_url":
            url = self.url_entry_row.props.text
            self.unlocked_database.send_to_clipboard(url, _("Address copied"))
        elif action_name == "entry.copy_otp":
            safe_entry: SafeEntry = self.props.safe_entry
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

        self.show_all_preferences_group.props.visible = False

    @Gtk.Template.Callback()
    def on_notes_detach_button_clicked(self, _button):
        self.unlocked_database.start_database_lock_timer()
        safe_entry = self.props.safe_entry
        NotesDialog(self.unlocked_database, safe_entry).present(self)

    def on_entry_icon_button_toggled(self, flowbox):
        if not flowbox.get_selected_children():
            return

        selected_row = flowbox.get_selected_children()[0]
        icon = selected_row.get_name()

        safe_entry = self.props.safe_entry
        safe_entry.props.icon = icon

    def _on_launch(self, launcher, result, window):
        try:
            launcher.launch_finish(result)
        except GLib.Error:
            logging.exception("Could not launch uri")
            window.send_notification(_("Could not open URL"))

    @Gtk.Template.Callback()
    def on_visit_url_button_clicked(self, _button):
        self.unlocked_database.start_database_lock_timer()
        url = self.url_entry_row.props.text
        window = self.unlocked_database.window
        if not validators.url(url):
            url = "https://" + url
            if not validators.url(url):
                window.send_notification(_("The address is not valid"))
                return

        launcher = Gtk.UriLauncher.new(url)
        launcher.launch(window, None, self._on_launch, window)

    @Gtk.Template.Callback()
    def on_otp_copy_button_clicked(self, _button: Gtk.Button) -> None:
        safe_entry: SafeEntry = self.props.safe_entry
        otp_token = safe_entry.otp_token() or ""
        self.unlocked_database.send_to_clipboard(
            otp_token,
            _("One-time password copied"),
        )

    def _on_add_attribute(self, _widget, _action_name, _pspec):
        window = self.unlocked_database.window
        entry = self.props.safe_entry
        db_manager = self.unlocked_database.database_manager
        dialog = AddAttributeDialog(db_manager, entry)
        dialog.present(window)

    #
    # Attachment Handling
    #

    @Gtk.Template.Callback()
    def on_attachment_list_box_activated(self, _widget, list_box_row):
        self.unlocked_database.start_database_lock_timer()
        attachment = list_box_row.attachment
        AttachmentWarningDialog(self, attachment).present(self)

    def _on_add_attachment(self, _widget, _action_name, _pspec):
        self.unlocked_database.start_database_lock_timer()

        dialog = Gtk.FileDialog.new()
        # NOTE: Filechooser title for selecting attachment file
        dialog.props.title = _("Select Attachments")
        dialog.props.accept_label = _("_Add")

        dialog.open_multiple(
            self.unlocked_database.window,
            None,
            self._on_select_filechooser_response,
        )

    def _on_select_filechooser_response(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
    ) -> None:
        try:
            files = dialog.open_multiple_finish(result)
        except GLib.Error as err:
            if not err.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED):
                logging.exception("Could not open files")
        else:
            safe_entry: SafeEntry = self.props.safe_entry

            def callback(gfile, result):
                try:
                    gbytes, _stream = gfile.load_bytes_finish(result)
                except GLib.Error:
                    logging.exception("Could not read attachment")
                else:
                    filename = gfile.get_basename()
                    data = gbytes.get_data()
                    new_attachment = safe_entry.add_attachment(data, filename)
                    self.add_attachment_row(new_attachment)

            for attachment in files:
                attachment.load_bytes_async(None, callback)

    def add_attachment_row(self, attachment: Attachment) -> None:
        safe_entry: SafeEntry = self.props.safe_entry
        attachment_row = AttachmentEntryRow(
            safe_entry, attachment, self.attachment_list_box
        )
        self.attachment_list_box.append(attachment_row)

    @Gtk.Template.Callback()
    def _on_url_copy_button_clicked(self, _button):
        url = self.url_entry_row.props.text
        self.unlocked_database.send_to_clipboard(url, _("Address copied"))

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
            self.otp_token_row.props.visible = True
            self.otp_token_row.props.title = otp_token
            self.otp_timer_handler = GObject.timeout_add(
                100,
                self.otp_update,
                safe_entry,
                None,
            )
        else:
            self.otp_token_row.props.visible = False

        if not otp_token and safe_entry.props.otp:
            self.otp_error_revealer.reveal(True)
            self.otp_secret_entry_row.add_css_class("error")
        else:
            self.otp_error_revealer.reveal(False)
            self.otp_secret_entry_row.remove_css_class("error")

        return GLib.SOURCE_CONTINUE
