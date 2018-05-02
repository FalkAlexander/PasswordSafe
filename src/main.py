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

def assembleWindow():
    fenster.connect("destroy", Gtk.main_quit)
    fenster.set_default_size(800, 500)

    builder = Gtk.Builder()
    builder.add_from_file("ui/headerbar.glade")

    headerbar = builder.get_object("headerbar")
    fenster.set_titlebar(headerbar)

    grid = Gtk.Grid()
    fenster.add(grid)

    button = Gtk.Button(label="Gruppen ausgeben")
    button.connect("clicked", on_button_clicked)
    grid.attach(button, 0, 0, 1, 1)

    button2 = Gtk.Button(label="Passwort ändern")
    button2.connect("clicked", on_password_change)
    grid.attach(button2, 1, 0, 1, 1)

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
    respone = dialog.run()
    if respone == Gtk.ResponseType.OK:
        print("Saving..." + dialog.get_filename())
        shutil.copy2('data/database.kdbx', dialog.get_filename())
        dialog.close()
    elif respone == Gtk.ResponseType.CANCEL:
        print("Database creation canceled")
        dialog.close()


def on_button_clicked(widget):
    print("Gruppen ausgeben")
    KeepassLoader.readDB()
    KeepassLoader.addGroup()
    KeepassLoader.addEntry()
    KeepassLoader.printGroup()
    KeepassLoader.saveGroup()

def on_password_change(widget):
    print("Passwort ändern")
    KeepassLoader.changePassword()

def get_widget(file, widget):
    builder = Gtk.Builder()
    builder.add_from_file(file)
    widget = builder.get_object(widget)
    return widget

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
