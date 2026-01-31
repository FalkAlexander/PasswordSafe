# SPDX-License-Identifier: GPL-3.0-only
"""GUI Page and function in order to create a new Safe."""

from __future__ import annotations

import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, Gtk

from gsecrets.password_generator_popover import PasswordGeneratorPopover


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/create_database.ui")
class CreateDatabase(Adw.Bin):
    """Creates a new Safe when invoked."""

    __gtype_name__ = "CreateDatabase"

    stack = Gtk.Template.Child()

    password_row = Gtk.Template.Child()
    password_confirm_row = Gtk.Template.Child()
    provider_group = Gtk.Template.Child()
    create_button = Gtk.Template.Child()
    open_safe_button = Gtk.Template.Child()
    back_button = Gtk.Template.Child()
    match_hint = Gtk.Template.Child()
    banner = Gtk.Template.Child()

    def __init__(self, window, dbm):
        super().__init__()

        self.database_manager = dbm
        self.window = window
        generator = Gtk.MenuButton()
        generator.set_icon_name("dice3-symbolic")
        generator_popover = PasswordGeneratorPopover()
        generator.set_popover(generator_popover)
        generator.set_tooltip_text(_("Generate New Password"))
        generator.add_css_class("flat")
        generator.set_valign(Gtk.Align.CENTER)
        generator_popover.connect("generated", self._on_password_generated)
        self.password_row.add_suffix(generator)
        self.password_row.connect("changed", self._on_password_changed)
        self.password_confirm_row.connect("changed", self._on_password_changed)

        self.back_button.props.sensitive = True
        self.back_button.connect("clicked", self.on_headerbar_back_button_clicked)
        for key_provider in self.window.key_providers.get_key_providers():
            if key_provider.available:
                self.provider_group.add(key_provider.create_database_row())

        self.window.set_default_widget(self.create_button)

    def do_realize(self):  # pylint: disable=arguments-differ
        Gtk.Widget.do_realize(self)
        self.password_row.grab_focus()

    def _on_password_changed(self, _entry: Gtk.Entry) -> None:
        is_match = self.password_row.props.text == self.password_confirm_row.props.text

        if not is_match:
            self.password_confirm_row.add_css_class("error")
            self.match_hint.set_label(_("Passwords do not match"))
        else:
            self.password_confirm_row.remove_css_class("error")
            self.match_hint.set_label("")

        self.create_button.set_sensitive(is_match and self.password_row.props.text)

    def success_page(self):
        self.stack.set_visible_child_name("safe-successfully-create")
        self.clear_input_fields()
        self.open_safe_button.grab_focus()

    def failure_page(self):
        self.stack.set_visible_child_name("select-auth-method")
        self.clear_input_fields()
        self.window.send_notification(_("Unable to create database"))

    def on_headerbar_back_button_clicked(self, _widget):
        self.go_back()

    def go_back(self):
        self.window.invoke_initial_screen()

    def _on_set_credentials(self, dbm, result):
        try:
            is_saved = dbm.set_credentials_finish(result)
        except GLib.Error:
            logging.exception("Could not set credentials")
            self.failure_page()
        else:
            if is_saved:
                self.success_page()
            else:  # Unreachable
                self.failure_page()

    def _on_password_generated(self, _popover, password):
        self.password_row.props.text = password
        self.password_confirm_row.props.text = password

    def _on_generate_composite_key(self, providers, result):
        self.stack.set_sensitive(True)

        try:
            composition_key = providers.generate_composite_key_finish(result)
        except GLib.Error:
            logging.exception("Failed to generate composite key")
            self.window.send_notification(_("Failed to generate composite key"))
            return

        self.database_manager.set_credentials_async(
            password=self.password_confirm_row.props.text,
            composition_key=composition_key,
            callback=self._on_set_credentials,
        )

    @Gtk.Template.Callback()
    def _on_create_button_clicked(self, _button: Gtk.Button) -> None:
        self.stack.set_sensitive(False)
        self.window.key_providers.generate_composite_key_async(
            self.database_manager.get_salt_as_lazy(),
            self._on_generate_composite_key,
        )

    @Gtk.Template.Callback()
    def on_finish_button_clicked(self, _widget: Gtk.Button) -> None:
        self.window.start_database_opening_routine(self.database_manager.path)

    def clear_input_fields(self) -> None:
        """Empty all Entry textfields."""
        self.password_row.set_text("")
        self.password_confirm_row.set_text("")

        for key_provider in self.window.key_providers.get_key_providers():
            key_provider.clear_input_fields()

    def show_banner(self, label: str) -> None:
        self.banner.set_title(label)
        self.banner.set_revealed(True)

    def close_banner(self):
        self.banner.set_revealed(False)
