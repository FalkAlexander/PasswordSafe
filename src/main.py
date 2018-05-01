import gi
import os
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
from os.path import exists, join, dirname, realpath
from pykeepass import PyKeePass
import KeepassLoader

fenster = Gtk.Window(title="KeePass")

def assembleWindow():
    fenster.connect("destroy", Gtk.main_quit)

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
