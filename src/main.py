import gi
import shutil
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
from pykeepass import PyKeePass
import database
from database import KeepassLoader
import config

class MainWindow(Gtk.Window):

    keepass_loader = NotImplemented

    def __init__(self):
        config.configure()
        self.assemble_window()


    def assemble_window(self):
        Gtk.Window.__init__(self, title="KeepassGtk")
        self.connect("destroy", Gtk.main_quit)
        self.set_default_size(800, 500)

        builder = Gtk.Builder()
        builder.add_from_file("ui/headerbar.glade")
        
        headerbar = builder.get_object("headerbar")
        self.set_titlebar(headerbar)

        file_open_button = builder.get_object("open_button")
        file_open_button.connect("clicked", self.open_filechooser)

        file_new_button = builder.get_object("new_button")
        file_new_button.connect("clicked", self.create_filechooser)


    # Events

    def open_filechooser(self, widget):
        dialog = Gtk.FileChooserDialog("Choose Keepass Database", self, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("File selected: " + dialog.get_filename())
            dialog.close()
        elif response == Gtk.ResponseType.CANCEL:
            print("File selection cancelled")
            dialog.close()

    def create_filechooser(self, widget):
        dialog = Gtk.FileChooserDialog("Create new Database", self, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_current_name("Database.kdbx")

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Keepass 2 Database")
        filter_text.add_mime_type("application/x-keepass2")
        dialog.add_filter(filter_text)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Saving..." + dialog.get_filename())
            shutil.copy2('data/database.kdbx', dialog.get_filename())
            dialog.close()
            print("Setze Datenbank Pfad: " + dialog.get_filename())
            self.keepass_loader = KeepassLoader(dialog.get_filename(), "liufhre86ewoiwejmrcu8owe")
            print("Bekomme Datenbank Pfad: " + self.keepass_loader.get_database())
            self.password_creation()
        elif response == Gtk.ResponseType.CANCEL:
            print("Database creation cancelled")
            dialog.close()

    def password_creation(self):
        builder = Gtk.Builder()
        builder.add_from_file("ui/database_creation.glade")

        stack = builder.get_object("database_creation_stack")
        stack.set_visible_child(stack.get_child_by_name("page0"))
        password_creation_button = builder.get_object("password_creation_button")
        password_creation_button.connect("clicked", self.on_password_creation_button_clicked)
        self.add(stack)

    def on_password_creation_button_clicked(self, widget):
        password_creation_input = builder.get_object("password_creation_input")
        self.keepass_loader.set_password_try(password_creation_input.get_text())

        self.check_password_page()

    def check_password_page(self):
        stack = builder.get_object("database_creation_stack")
        stack.set_visible_child(stack.get_child_by_name("page1"))

        password_check_button = builder.get_object("password_check_button")
        password_check_button.connect("clicked", on_password_check_button_clicked)

    def on_password_check_button_clicked(widget):
        password_check_input = builder.get_object("password_check_input")
        KeepassLoader.set_password_check(password_check_input.get_text())

        if KeepassLoader.compare_passwords():
            KeepassLoader.set_database_password(password_check_input.get_text())
            success_page()
        else:
            repeat_page()

    def success_page():
        print("Datenbank Pfad: " + KeepassLoader.get_database())
        KeepassLoader.set_database_password(KeepassLoader.password_check)

        stack = builder.get_object("database_creation_stack")
        stack.set_visible_child(stack.get_child_by_name("page3"))

        clear_input_fields()

    def repeat_page():
        stack = builder.get_object("database_creation_stack")
        stack.set_visible_child(stack.get_child_by_name("page2"))

        password_repeat_button = builder.get_object("password_repeat_button")
        password_repeat_button.connect("clicked", on_password_repeat_button_clicked)

    def on_password_repeat_button_clicked(widget):
        password_repeat_input1 = builder.get_object("password_repeat_input1")
        password_repeat_input2 = builder.get_object("password_repeat_input2")

        KeepassLoader.set_password_try(password_repeat_input1.get_text())
        KeepassLoader.set_password_check(password_repeat_input2.get_text())

        if KeepassLoader.compare_passwords():
            KeepassLoader.set_database_password(password_repeat_input2.get_text())
            KeepassLoader.save_database()
            success_page()
        else:
            clear_input_fields()
            password_repeat_input1.get_style_context().add_class("error")
            password_repeat_input2.get_style_context().add_class("error")

    def clear_input_fields():
        password_creation_input = builder.get_object("password_creation_input")
        password_check_input = builder.get_object("password_check_input")
        password_repeat_input1 = builder.get_object("password_repeat_input1")
        password_repeat_input2 = builder.get_object("password_repeat_input2")

        password_creation_input.set_text("")
        password_check_input.set_text("")
        password_repeat_input1.set_text("")
        password_repeat_input2.set_text("")

main_window = MainWindow()
main_window.show_all()
Gtk.main()
