# SPDX-License-Identifier: GPL-3.0-only
""" GUI Page and function in order to create a new Safe"""
from __future__ import annotations

import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, Gtk

from gsecrets.utils import KeyFileFilter, generate_keyfile


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/create_database.ui")
class CreateDatabase(Adw.Bin):
    """Creates a new Safe when invoked"""

    # TODO Add an accelerator for Escape that
    # calls on_headerbar_back_button_clicked().
    # Can be done on GTK 4 with GtkShortcutController.

    __gtype_name__ = "CreateDatabase"

    stack = Gtk.Template.Child()

    password_action_row = Gtk.Template.Child()

    password_creation_input = Gtk.Template.Child()

    password_check_button = Gtk.Template.Child()
    password_check_input = Gtk.Template.Child()

    password_repeat_button = Gtk.Template.Child()
    password_repeat_input1 = Gtk.Template.Child()
    password_repeat_input2 = Gtk.Template.Child()

    generate_keyfile_button = Gtk.Template.Child()

    open_safe_button = Gtk.Template.Child()

    new_password = ""

    composite = False

    def __init__(self, window, dbm):
        super().__init__()

        self.database_manager = dbm
        self.window = window
        self.back_button = window.create_database_headerbar.back_button

        self.back_button.props.sensitive = True
        self.back_button.connect("clicked", self.on_headerbar_back_button_clicked)

    def do_realize(self):  # pylint: disable=arguments-differ
        Gtk.Widget.do_realize(self)
        self.password_action_row.grab_focus()

    def success_page(self):
        self.stack.set_visible_child_name("safe-successfully-create")
        # TODO This should be improved upon. Widgets should not
        # modify widgets outside of their scope.
        self.back_button.props.sensitive = False
        self.open_safe_button.grab_focus()

    def failure_page(self):
        self.stack.set_visible_child_name("password-creation")
        self.clear_input_fields()
        self.window.send_notification(_("Unable to create database"))

    def keyfile_generation_page(self):
        self.stack.set_visible_child_name("keyfile-creation")
        self.generate_keyfile_button.grab_focus()

    def on_headerbar_back_button_clicked(self, _widget):
        """Back button: Always goes back to the page in which you select the
        authentication method. In the case we are already in that page
        we kill this page."""
        if self.stack.get_visible_child_name() == "select_auth_method":
            self.window.view = self.window.View.RECENT_FILES
        else:
            self.stack.set_visible_child_name("select_auth_method")
            self.clear_input_fields()
            self.composite = False

    def _on_set_credentials(self, dbm, result):
        try:
            is_saved = dbm.set_credentials_finish(result)
        except GLib.Error as err:
            logging.error("Could not set credentials: %s", err.message)
            self.failure_page()
        else:
            if is_saved:
                self.success_page()
            else:  # Unreachable
                self.failure_page()
        finally:
            self.new_password = ""

    @Gtk.Template.Callback()
    def on_password_generated(self, _popover, password):
        self.password_creation_input.props.text = password
        self.password_check_input.props.text = password

    @Gtk.Template.Callback()
    def on_auth_chooser_row_activated(
        self, _widget: Gtk.ListBox, row: Gtk.ListBoxRow
    ) -> None:
        if row.get_name() == "password":
            self.stack.set_visible_child_name("password-creation")
            self.password_creation_input.grab_focus()
        elif row.get_name() == "keyfile":
            self.keyfile_generation_page()
        elif row.get_name() == "composite":
            self.composite = True
            self.stack.set_visible_child_name("password-creation")
            self.password_creation_input.grab_focus()

    @Gtk.Template.Callback()
    def on_password_creation_button_clicked(self, _widget: Gtk.Button) -> None:
        self.database_manager.set_password_try(self.password_creation_input.get_text())
        self.stack.set_visible_child_name("check-password")
        self.password_check_input.grab_focus()

    @Gtk.Template.Callback()
    def on_password_check_button_clicked(self, _widget: Gtk.Button) -> None:
        password_check = self.password_check_input.get_text()

        if self.database_manager.compare_passwords(password_check):
            self.new_password = password_check

            self.show_pwc_loading()
            if self.composite:
                self.keyfile_generation_page()
            else:
                self.database_manager.set_credentials_async(
                    password_check, callback=self._on_set_credentials
                )
        else:
            self.stack.set_visible_child_name("passwords-dont-match")
            self.password_repeat_input1.grab_focus()

    @Gtk.Template.Callback()
    def on_password_repeat_button_clicked(self, _widget: Gtk.Button) -> None:

        passwd: str = self.password_repeat_input1.get_text()
        self.database_manager.set_password_try(passwd)
        conf_passwd: str = self.password_repeat_input2.get_text()

        if self.database_manager.compare_passwords(conf_passwd):
            self.new_password = conf_passwd

            self.show_pwr_loading()
            if self.composite:
                self.keyfile_generation_page()
            else:
                self.database_manager.set_credentials_async(
                    self.new_password, callback=self._on_set_credentials,
                )
        else:
            self.window.send_notification(_("Passwords do not match"))
            self.clear_input_fields()
            self.password_repeat_input1.add_css_class("error")
            self.password_repeat_input2.add_css_class("error")

    @Gtk.Template.Callback()
    def on_generate_keyfile_button_clicked(self, _widget: Gtk.Button) -> None:
        """cb invoked when we create a new keyfile for a newly created Safe"""
        keyfile_dlg = Gtk.FileChooserNative.new(
            _("Generate Keyfile"),
            self.window,
            Gtk.FileChooserAction.SAVE,
            _("_Generate"),
            None,
        )
        keyfile_dlg.set_modal(True)
        keyfile_dlg.set_current_name(_("Keyfile"))
        keyfile_dlg.add_filter(KeyFileFilter().file_filter)

        keyfile_dlg.connect("response", self._on_filechooser_response, keyfile_dlg)
        keyfile_dlg.show()

    def _on_filechooser_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType, _dialog: Gtk.Dialog
    ) -> None:
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            self.generate_keyfile_button.set_sensitive(False)
            self.generate_keyfile_button.set_label(_("Generating…"))
            keyfile = dialog.get_file()
            keyfile_path = keyfile.get_path()
            logging.debug("New keyfile location: %s", keyfile_path)

            def callback(gfile, result, keyfile_hash):
                password = self.new_password
                try:
                    gfile.replace_contents_finish(result)
                except GLib.Error as err:
                    logging.debug("Could not create keyfile: %s", err.message)
                    self.window.send_notification(_("Could not create keyfile"))
                    self.generate_keyfile_button.set_sensitive(True)
                    self.generate_keyfile_button.set_label(_("Generate"))
                else:
                    if not self.composite:
                        password = ""

                    self.database_manager.set_credentials_async(
                        password, keyfile_path, keyfile_hash,
                        self._on_set_credentials,
                    )

            generate_keyfile(keyfile, callback)

    @Gtk.Template.Callback()
    def on_finish_button_clicked(self, _widget: Gtk.Button) -> None:
        self.window.start_database_opening_routine(self.database_manager.path)

    @Gtk.Template.Callback()
    def on_password_repeat_input_activate(self, _widget: Gtk.Entry) -> None:
        self.password_repeat_button.activate()

    def show_pwc_loading(self):
        password_check_button = self.password_check_button
        spinner = Gtk.Spinner()
        spinner.start()
        password_check_button.set_child(spinner)
        password_check_button.set_sensitive(False)
        self.password_check_input.set_sensitive(False)

    def show_pwr_loading(self):
        password_repeat_button = self.password_repeat_button
        spinner = Gtk.Spinner()
        spinner.start()
        password_repeat_button.set_child(spinner)
        password_repeat_button.set_sensitive(False)
        self.password_repeat_input1.set_sensitive(False)
        self.password_repeat_input2.set_sensitive(False)

    def clear_input_fields(self) -> None:
        """Empty all Entry textfields"""
        self.password_creation_input.set_text("")
        self.password_check_input.set_text("")
        self.password_repeat_input1.set_text("")
        self.password_repeat_input2.set_text("")
