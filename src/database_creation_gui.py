import gi
import shutil
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
from main import MainWindow
import database
from database import KeepassLoader

class DatabaseCreationGui:

    builder = Gtk.Builder()
    builder.add_from_file("ui/database_creation.ui")
    keepass_loader = NotImplemented
    main_window = MainWindow()

    def __init__(self, keepass_loader):
        self.keepass_loader = keepass_loader
        self.password_creation()
 
    def password_creation(self):
        stack = self.builder.get_object("database_creation_stack")
        stack.set_visible_child(stack.get_child_by_name("page0"))
        password_creation_button = self.builder.get_object("password_creation_button")
        password_creation_button.connect("clicked", self.on_password_creation_button_clicked)
        self.main_window.add(stack)

    def on_password_creation_button_clicked(self, widget):
        password_creation_input = self.builder.get_object("password_creation_input")
        self.keepass_loader.set_password_try(password_creation_input.get_text())

        self.check_password_page()

    def check_password_page(self):
        stack = self.builder.get_object("database_creation_stack")
        stack.set_visible_child(stack.get_child_by_name("page1"))

        password_check_button = self.builder.get_object("password_check_button")
        password_check_button.connect("clicked", self.on_password_check_button_clicked)

    def on_password_check_button_clicked(self, widget):
        password_check_input = self.builder.get_object("password_check_input")
        self.keepass_loader.set_password_check(password_check_input.get_text())

        if self.keepass_loader.compare_passwords():
            self.keepass_loader.set_database_password(password_check_input.get_text())
            self.success_page()
        else:
            self.repeat_page()

    def success_page(self):
        print("Datenbank Pfad: " + self.keepass_loader.get_database())
        self.keepass_loader.set_database_password(KeepassLoader.password_check)

        stack = self.builder.get_object("database_creation_stack")
        stack.set_visible_child(stack.get_child_by_name("page3"))

        self.clear_input_fields()

    def repeat_page(self):
        stack = self.builder.get_object("database_creation_stack")
        stack.set_visible_child(stack.get_child_by_name("page2"))

        password_repeat_button = self.builder.get_object("password_repeat_button")
        password_repeat_button.connect("clicked", self.on_password_repeat_button_clicked)

    def on_password_repeat_button_clicked(self, widget):
        password_repeat_input1 = self.builder.get_object("password_repeat_input1")
        password_repeat_input2 = self.builder.get_object("password_repeat_input2")

        self.keepass_loader.set_password_try(password_repeat_input1.get_text())
        self.keepass_loader.set_password_check(password_repeat_input2.get_text())

        if self.keepass_loader.compare_passwords():
            self.keepass_loader.set_database_password(password_repeat_input2.get_text())
            self.keepass_loader.save_database()
            self.success_page()
        else:
            self.clear_input_fields()
            password_repeat_input1.get_style_context().add_class("error")
            password_repeat_input2.get_style_context().add_class("error")

    def clear_input_fields(self):
        password_creation_input = self.builder.get_object("password_creation_input")
        password_check_input = self.builder.get_object("password_check_input")
        password_repeat_input1 = self.builder.get_object("password_repeat_input1")
        password_repeat_input2 = self.builder.get_object("password_repeat_input2")

        password_creation_input.set_text("")
        password_check_input.set_text("")
        password_repeat_input1.set_text("")
        password_repeat_input2.set_text("")
        

def run_database_creation_gui(keepass_loader):
    DatabaseCreationGui(keepass_loader)