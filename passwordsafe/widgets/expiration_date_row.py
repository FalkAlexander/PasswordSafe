# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gtk

from passwordsafe.safe_element import SafeEntry


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/expiration_date_row.ui")
class ExpirationDateRow(Adw.Bin):

    __gtype_name__ = "ExpirationDateRow"

    action_row = Gtk.Template.Child()
    calendar = Gtk.Template.Child()
    popover = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()
    remove_button = Gtk.Template.Child()
    popover_edit_button = Gtk.Template.Child()
    list_box = Gtk.Template.Child()

    _safe_entry = None

    @GObject.Property(type=SafeEntry, flags=GObject.ParamFlags.READWRITE)
    def safe_entry(self) -> SafeEntry:
        return self._safe_entry

    @safe_entry.setter  # type: ignore
    def safe_entry(self, entry: SafeEntry) -> None:
        self._safe_entry = entry

        entry.bind_property(
            "expires",
            self.remove_button,
            "sensitive",
            GObject.BindingFlags.SYNC_CREATE,
        )
        entry.connect(
            "notify::expired",
            self.on_safe_entry_notify_expired,
        )
        expiry_date = entry.expiry_time

        if entry.props.expires:
            self.calendar.select_day(expiry_date)
            self.action_row.props.title = expiry_date.format("%e %b %Y")
            if entry.props.expired:
                self.action_row.props.subtitle = _("Entry expired")

    def on_safe_entry_notify_expired(
        self, safe_entry: SafeEntry, _gparam: GObject.ParamSpecBoolean
    ) -> None:
        if safe_entry.props.expired:
            self.action_row.props.subtitle = _("Entry expired")
        else:
            self.action_row.props.subtitle = None

    @Gtk.Template.Callback()
    def on_edit_button_clicked(self, _button: Gtk.Button) -> None:
        safe_entry = self.props.safe_entry
        date = self.calendar.get_date()
        safe_entry.expiry_time = date
        self.action_row.props.title = date.format("%e %b %Y")

        safe_entry.props.expires = True
        if safe_entry.props.expired:
            self.action_row.props.subtitle = _("Entry expired.")

        self.popover.popdown()

    @Gtk.Template.Callback()
    def on_remove_button_clicked(self, _button: Gtk.Button) -> None:
        safe_entry = self.props.safe_entry
        self.action_row.props.title = _("Expiration date not set")
        self.action_row.props.subtitle = None
        now = GLib.DateTime.new_now_utc()
        self.calendar.select_day(now)
        safe_entry.props.expires = False

    @Gtk.Template.Callback()
    def on_mnemonic_activate(self, _widget, _group_cycling):
        # FIXME MenuButtons don't implement the Actionable interface
        # therefore activatable_widget and mnemonic_widget do not work.
        # See https://gitlab.gnome.org/GNOME/gtk/-/issues/4079
        self.edit_button.popup()

    @Gtk.Template.Callback()
    def on_row_activated(self, _listbox: Gtk.ListBox, _row: Gtk.ListBoxRow) -> None:
        self.edit_button.popup()
