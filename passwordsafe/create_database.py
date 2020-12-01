# SPDX-License-Identifier: GPL-3.0-only
""" GUI Page and function in order to create a new Safe"""
import logging
import threading
from gettext import gettext as _
from gi.repository import GLib, Gtk

import passwordsafe.keyfile_generator
from passwordsafe.created_database import CreatedDatabase
from passwordsafe.unlock_database import KeyFileFilter


@Gtk.Template(
    resource_path="/org/gnome/PasswordSafe/create_database.ui")
class CreateDatabase(Gtk.Stack):
    """Creates a new Safe when invoked"""

    __gtype_name__ = "CreateDatabase"

    password_creation_input = Gtk.Template.Child()

    password_check_button = Gtk.Template.Child()
    password_check_input = Gtk.Template.Child()

    password_repeat_button = Gtk.Template.Child()
    password_repeat_input1 = Gtk.Template.Child()
    password_repeat_input2 = Gtk.Template.Child()

    generate_keyfile_button = Gtk.Template.Child()

    switched = False
    composite = False

    def __init__(self, window, widget, dbm):
        super().__init__()
        self.database_manager = dbm
        self.window = window
        self.parent_widget = widget

        self.set_headerbar()

    #
    # Stack Pages
    #

    # Password

    def password_creation(self):
        self.set_visible_child_name("password-creation")
        self.password_creation_input.grab_focus()

    def success_page(self):
        # TODO Move created_page here
        self.clear_input_fields()
        if self.composite is False:
            self.parent_widget.remove(self)
            CreatedDatabase(self.window, self.parent_widget, self.database_manager)
        else:
            self.keyfile_creation()

    # Keyfile

    def keyfile_creation(self):
        self.set_visible_child_name("keyfile-creation")

    def set_database_keyfile(self):
        self.parent_widget.remove(self)
        CreatedDatabase(self.window, self.parent_widget, self.database_manager)

    #
    # Headerbar
    #

    def set_headerbar(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/create_database_headerbar.ui")
        headerbar = builder.get_object("headerbar")
        self.window.set_titlebar(headerbar)
        self.parent_widget.set_headerbar(headerbar)

        back_button = builder.get_object("back_button")
        back_button.connect("clicked", self.on_headerbar_back_button_clicked)

    #
    # Events
    #

    def on_headerbar_back_button_clicked(self, _widget):
        if self.get_visible_child_name() == "select_auth_method":
            pass
        if self.get_visible_child_name() == "password-creation":
            self.set_visible_child_name("select_auth_method")
        elif self.get_visible_child_name() == "check-password":
            self.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
            self.set_visible_child_name("select_auth_method")
            self.switched = True
            self.set_visible_child_name("password-creation")
            self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        elif self.get_visible_child_name() == "passwords-dont-match":
            self.window.close_tab(self.parent_widget)
            self.window.set_headerbar()
        elif self.get_visible_child_name() == "keyfile-creation":
            self.window.close_tab(self.parent_widget)
            self.window.set_headerbar()

    @Gtk.Template.Callback()
    def on_auth_chooser_row_activated(self, _widget, row):
        if row.get_name() == "password":
            self.password_creation()
        elif row.get_name() == "keyfile":
            self.keyfile_creation()
        elif row.get_name() == "composite":
            self.composite = True
            self.password_creation()

    @Gtk.Template.Callback()
    def on_password_creation_button_clicked(self, _widget):
        self.database_manager.set_password_try(
            self.password_creation_input.get_text())

        if self.switched:
            self.set_visible_child_name("check-password")
        else:
            self.check_password_page()

    def check_password_page(self):
        self.set_visible_child_name("check-password")

    @Gtk.Template.Callback()
    def on_password_check_button_clicked(self, _widget):
        password_check = self.password_check_input.get_text()

        if self.database_manager.compare_passwords(password_check):
            self.database_manager.password = password_check

            save_thread = threading.Thread(target=self.save_pwc_database_thread)
            save_thread.daemon = True
            save_thread.start()
        else:
            self.set_visible_child_name("passwords-dont-match")

    @Gtk.Template.Callback()
    def on_password_repeat_button_clicked(self, _widget):

        passwd: str = self.password_repeat_input1.get_text()
        self.database_manager.set_password_try(passwd)
        conf_passwd: str = self.password_repeat_input2.get_text()

        if self.database_manager.compare_passwords(conf_passwd):
            self.database_manager.password = conf_passwd

            save_thread = threading.Thread(target=self.save_pwr_database_thread)
            save_thread.daemon = True
            save_thread.start()
        else:
            # TODO Notify the user the passwords don't match.
            self.clear_input_fields()
            self.password_repeat_input1.get_style_context().add_class("error")
            self.password_repeat_input2.get_style_context().add_class("error")

    def save_pwc_database_thread(self):
        GLib.idle_add(self.show_pwc_loading)
        if self.composite is False:
            self.database_manager.save_database()
        GLib.idle_add(self.success_page)

    def show_pwc_loading(self):
        password_check_button = self.password_check_button
        password_check_button.remove(password_check_button.get_children()[0])
        spinner = Gtk.Spinner()
        spinner.start()
        spinner.show()
        password_check_button.add(spinner)
        password_check_button.set_sensitive(False)
        self.password_check_input.set_sensitive(False)

    def save_pwr_database_thread(self):
        GLib.idle_add(self.show_pwr_loading)
        if self.composite is False:
            self.database_manager.save_database()
        GLib.idle_add(self.success_page)

    def show_pwr_loading(self):
        password_repeat_button = self.password_repeat_button
        password_repeat_button.remove(password_repeat_button.get_children()[0])
        spinner = Gtk.Spinner()
        spinner.start()
        spinner.show()
        password_repeat_button.add(spinner)
        password_repeat_button.set_sensitive(False)
        self.password_repeat_input1.set_sensitive(False)
        self.password_repeat_input2.set_sensitive(False)

    @Gtk.Template.Callback()
    def on_generate_keyfile_button_clicked(self, _widget: Gtk.Button) -> None:
        """cb invoked when we create a new keyfile for a newly created Safe"""
        keyfile_dlg = Gtk.FileChooserNative.new(
            _("Choose location for keyfile"),
            self.window, Gtk.FileChooserAction.SAVE,
            _("Generate"), None)
        keyfile_dlg.set_do_overwrite_confirmation(True)
        keyfile_dlg.set_modal(True)
        keyfile_dlg.set_local_only(False)
        keyfile_dlg.add_filter(KeyFileFilter())
        response = keyfile_dlg.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.generate_keyfile_button.set_sensitive(False)
            self.generate_keyfile_button.set_label(_("Generating…"))
            keyfile_path = keyfile_dlg.get_filename()
            logging.debug("New keyfile location: %s", keyfile_path)

            generator_thread = threading.Thread(
                target=passwordsafe.keyfile_generator.generate_keyfile,
                args=(keyfile_path, True, self, self.composite))
            generator_thread.daemon = True
            generator_thread.start()

    #
    # Helper Functions
    #

    def clear_input_fields(self) -> None:
        """Empty all Entry textfields"""
        self.password_creation_input.set_text("")
        self.password_check_input.set_text("")
        self.password_repeat_input1.set_text("")
        self.password_repeat_input2.set_text("")
