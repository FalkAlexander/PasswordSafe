import gi
import os
import shutil
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
from os.path import exists, join, dirname, realpath
from pykeepass import PyKeePass
import KeepassLoader

fenster = Gtk.Window(title="KeepassGtk")

builder = Gtk.Builder()
builder.add_from_file("ui/password_creation.glade")

def assembleWindow():
    fenster.connect("destroy", Gtk.main_quit)
    fenster.set_default_size(800, 500)

    builder = Gtk.Builder()
    builder.add_from_file("ui/headerbar.glade")

    headerbar = builder.get_object("headerbar")
    fenster.set_titlebar(headerbar)

    #grid = Gtk.Grid()
    #fenster.add(grid)

    #button = Gtk.Button(label="Gruppen ausgeben")
    #button.connect("clicked", on_button_clicked)
    #grid.attach(button, 0, 0, 1, 1)

    #button2 = Gtk.Button(label="Passwort ändern")
    #button2.connect("clicked", on_password_change)
    #grid.attach(button2, 1, 0, 1, 1)

    file_open_button = builder.get_object("open_button")
    file_open_button.connect("clicked", open_filechooser)

    file_new_button = builder.get_object("new_button")
    file_new_button.connect("clicked", create_filechooser)


# Events

def open_filechooser(widget):
    dialog = Gtk.FileChooserDialog("Choose Keepass Database", fenster, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        print("File selected: " + dialog.get_filename())
        dialog.close()
    elif response == Gtk.ResponseType.CANCEL:
        print("File selection canceled")
        dialog.close()

def create_filechooser(widget):
    dialog = Gtk.FileChooserDialog("Create new Database", fenster, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
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
        KeepassLoader.set_database(dialog.get_filename())
        print("Bekomme Datenbank Pfad: " + KeepassLoader.get_database())
        password_creation()
    elif response == Gtk.ResponseType.CANCEL:
        print("Database creation canceled")
        dialog.close()

#def get_widget(file, widget):
#    builder = Gtk.Builder()
#    builder.add_from_file(file)
#    widget = builder.get_object(widget)
#    return widget

def password_creation():
    stack = builder.get_object("database_creation_stack")
    stack.set_visible_child(stack.get_child_by_name("page0"))
    password_creation_button = builder.get_object("password_creation_button")
    password_creation_button.connect("clicked", on_password_creation_button_clicked)
    fenster.add(stack)

def on_password_creation_button_clicked(widget):
    password_creation_input = builder.get_object("password_creation_input")
    KeepassLoader.set_password_try(password_creation_input.get_text())

    check_password_page()

def check_password_page():
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
    

def config():
    HOME = os.getenv("HOME")
    CONFIG_PATH = join(HOME, '.config/keepassgtk')
    CONFIG_FILE = join(CONFIG_PATH, 'config.conf')

    if not exists(CONFIG_PATH):
        os.mkdir(CONFIG_PATH)

    if not exists(CONFIG_FILE):
        cfg = GLib.KeyFile()
        cfg.set_string('settings', 'theme-variant', 'white')
        cfg.save_to_file(CONFIG_FILE)
        cfg.unref()

config()
assembleWindow()
fenster.show_all()
Gtk.main()

