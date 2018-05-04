import pykeepass
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
from pykeepass import PyKeePass

def test():
    file_open_button = get_widget("ui/headerbar.glade", "headerbar")
    

def get_widget(file, widget):
    builder = Gtk.Builder()
    builder.add_from_file(file)
    widget = builder.get_object(widget)
    return widget

test()