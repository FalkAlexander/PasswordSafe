from gi.repository import Gtk, GLib
from passwordsafe.created_database import CreatedDatabase
import gi
import threading
gi.require_version('Gtk', '3.0')


class CreateDatabase:
    builder = NotImplemented
    database_manager = NotImplemented
    parent_widget = NotImplemented
    window = NotImplemented
    switched = False

    def __init__(self, window, widget, dbm):
        self.database_manager = dbm
        self.window = window
        self.parent_widget = widget
        self.password_creation()

    #
    # Stack Pages
    #

    def password_creation(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource(
            "/org/gnome/PasswordSafe/create_database.ui")

        self.set_headerbar()

        self.stack = self.builder.get_object("database_creation_stack")
        self.stack.set_visible_child(self.stack.get_child_by_name("page0"))

        password_creation_button = self.builder.get_object(
            "password_creation_button")
        password_creation_button.connect(
            "clicked", self.on_password_creation_button_clicked)

        password_creation_input = self.builder.get_object(
            "password_creation_input")
        password_creation_input.connect(
            "activate", self.on_password_creation_button_clicked)

        self.parent_widget.add(self.stack)
        password_creation_input.grab_focus()

    def success_page(self):
        self.clear_input_fields()
        self.parent_widget.remove(self.stack)

        CreatedDatabase(self.window, self.parent_widget, self.database_manager)

    def repeat_page(self):
        self.stack.set_visible_child(self.stack.get_child_by_name("page2"))

        password_repeat_button = self.builder.get_object(
            "password_repeat_button")
        password_repeat_button.connect(
            "clicked", self.on_password_repeat_button_clicked)

        password_repeat_input2 = self.builder.get_object(
            "password_repeat_input2")
        password_repeat_input2.connect(
            "activate", self.on_password_repeat_button_clicked)

    #
    # Headerbar
    #

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")
        self.window.set_titlebar(headerbar)
        self.parent_widget.set_headerbar(headerbar)

        back_button = self.builder.get_object("back_button")
        back_button.connect("clicked", self.on_headerbar_back_button_clicked)

    #
    # Events
    #

    def on_headerbar_back_button_clicked(self, widget):
        if self.stack.get_visible_child_name() == "page0":
            self.window.set_headerbar()
            self.window.close_tab(self.parent_widget)
        elif self.stack.get_visible_child_name() == "page1":
            self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
            self.switched = True
            self.stack.set_visible_child(self.stack.get_child_by_name("page0"))
            self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        elif self.stack.get_visible_child_name() == "page2":
            self.window.close_tab(self.parent_widget)
            self.window.set_headerbar()

    def on_password_creation_button_clicked(self, widget):
        password_creation_input = self.builder.get_object(
            "password_creation_input")
        self.database_manager.set_password_try(
            password_creation_input.get_text())

        if self.switched:
            self.stack.set_visible_child(self.stack.get_child_by_name("page1"))
        else:
            self.check_password_page()

    def check_password_page(self):
        self.stack.set_visible_child(self.stack.get_child_by_name("page1"))

        password_check_button = self.builder.get_object(
            "password_check_button")
        password_check_button.connect(
            "clicked", self.on_password_check_button_clicked)

        password_check_input = self.builder.get_object("password_check_input")
        password_check_input.connect(
            "activate", self.on_password_check_button_clicked)

    def on_password_check_button_clicked(self, widget):
        password_check_input = self.builder.get_object("password_check_input")
        self.database_manager.set_password_check(
            password_check_input.get_text())

        if self.database_manager.compare_passwords():
            self.database_manager.set_database_password(
                password_check_input.get_text())

            save_thread = threading.Thread(target=self.save_pwc_database_thread)
            save_thread.daemon = True
            save_thread.start()
        else:
            self.repeat_page()

    def on_password_repeat_button_clicked(self, widget):
        password_repeat_input1 = self.builder.get_object(
            "password_repeat_input1")
        password_repeat_input2 = self.builder.get_object(
            "password_repeat_input2")

        self.database_manager.set_password_try(
            password_repeat_input1.get_text())
        self.database_manager.set_password_check(
            password_repeat_input2.get_text())

        if self.database_manager.compare_passwords():
            self.database_manager.set_database_password(
                password_repeat_input2.get_text())

            save_thread = threading.Thread(target=self.save_pwr_database_thread)
            save_thread.daemon = True
            save_thread.start()
        else:
            self.clear_input_fields()
            password_repeat_input1.get_style_context().add_class("error")
            password_repeat_input2.get_style_context().add_class("error")

    def save_pwc_database_thread(self):
        GLib.idle_add(self.show_pwc_loading)
        self.database_manager.save_database()
        GLib.idle_add(self.success_page)

    def show_pwc_loading(self):
        password_check_button = self.builder.get_object("password_check_button")
        password_check_button.remove(password_check_button.get_children()[0])
        spinner = Gtk.Spinner()
        spinner.start()
        spinner.show()
        password_check_button.add(spinner)
        password_check_button.set_sensitive(False)
        self.builder.get_object("password_check_input").set_sensitive(False)

    def save_pwr_database_thread(self):
        GLib.idle_add(self.show_pwr_loading)
        self.database_manager.save_database()
        GLib.idle_add(self.success_page)

    def show_pwr_loading(self):
        password_repeat_button = self.builder.get_object("password_repeat_button")
        password_repeat_button.remove(password_repeat_button.get_children()[0])
        spinner = Gtk.Spinner()
        spinner.start()
        spinner.show()
        password_repeat_button.add(spinner)
        password_repeat_button.set_sensitive(False)
        self.builder.get_object("password_repeat_input1").set_sensitive(False)
        self.builder.get_object("password_repeat_input2").set_sensitive(False)

    #
    # Helper Functions
    #

    def clear_input_fields(self):
        password_creation_input = self.builder.get_object(
            "password_creation_input")
        password_check_input = self.builder.get_object(
            "password_check_input")
        password_repeat_input1 = self.builder.get_object(
            "password_repeat_input1")
        password_repeat_input2 = self.builder.get_object(
            "password_repeat_input2")

        password_creation_input.set_text("")
        password_check_input.set_text("")
        password_repeat_input1.set_text("")
        password_repeat_input2.set_text("")
