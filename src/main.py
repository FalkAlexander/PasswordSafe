import os
from os.path import exists
import shutil
import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk
import pykeepass
from pykeepass import PyKeePass
import config
import database
from database import KeepassLoader
import database_creation_gui
from database_creation_gui import DatabaseCreationGui
import container_page
from container_page import ContainerPage

class MainWindow(Gtk.Window):

    keepass_loader = NotImplemented
    container = NotImplemented
    override_dialog = NotImplemented
    filechooser_creation_dialog = NotImplemented


    def __init__(self):
        config.configure()
        self.assemble_window()


    def assemble_window(self):
        Gtk.Window.__init__(self, title="KeepassGtk")
        self.connect("destroy", Gtk.main_quit)
        self.set_default_size(800, 500)

        builder = Gtk.Builder()
        builder.add_from_file("ui/main_headerbar.ui")
        
        headerbar = builder.get_object("headerbar")
        self.set_titlebar(headerbar)

        file_open_button = builder.get_object("open_button")
        file_open_button.connect("clicked", self.open_filechooser)

        file_new_button = builder.get_object("new_button")
        file_new_button.connect("clicked", self.create_filechooser)

        self.create_container()


    def create_container(self):
        self.container = Gtk.Notebook()

        self.container.set_border_width(0)
        self.container.set_scrollable(True)
        self.container.set_show_border(False)

        self.add(self.container)


    def destroy_container(self):
        self.container.destroy()


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
        self.filechooser_creation_dialog = Gtk.FileChooserDialog("Create new Database", self, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        self.filechooser_creation_dialog.set_current_name("Database.kdbx")

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Keepass 2 Database")
        filter_text.add_mime_type("application/x-keepass2")
        self.filechooser_creation_dialog.add_filter(filter_text)

        response = self.filechooser_creation_dialog.run()
        if response == Gtk.ResponseType.OK:
            print("KLICK")
            print("Saving..." + self.filechooser_creation_dialog.get_filename())
            self.does_file_exist()   
        elif response == Gtk.ResponseType.CANCEL:
            print("Database creation cancelled")
            self.filechooser_creation_dialog.close()


    def does_file_exist(self):
        if os.path.exists(self.filechooser_creation_dialog.get_filename()):
            builder = Gtk.Builder()
            builder.add_from_file("ui/override_dialog.ui")
            self.override_dialog = builder.get_object("override_dialog")

            cancel_button = builder.get_object("cancel_button")
            override_button = builder.get_object("override_button")

            cancel_button.connect("clicked", self.on_cancel_button_clicked)
            override_button.connect("clicked", self.on_override_button_clicked)

            self.override_dialog.show_all()
        else:
            self.create_tab()


    def create_tab(self):
        shutil.copy2('data/database.kdbx', self.filechooser_creation_dialog.get_filename())
        self.filechooser_creation_dialog.close()

        page_instance = ContainerPage(self.filechooser_creation_dialog.get_filename())

        tab_hbox = Gtk.HBox(False, 0)
        
        regex = re.search("[^\.]+", self.filechooser_creation_dialog.get_current_name())
        tab_title = regex[0]
        tab_label = Gtk.Label(tab_title)
        tab_hbox.pack_start(tab_label, False, False, False)

        icon = Gio.ThemedIcon(name="window-close-symbolic")
        close_image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        close_button = Gtk.Button()
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_focus_on_click(False)
        close_button.connect("clicked", self.on_tab_close_button_clicked, page_instance)
        close_button.add(close_image)

        tab_hbox.pack_start(close_button, False, False, False)
        tab_hbox.show_all()

        self.container.append_page(page_instance, tab_hbox)
        self.container.set_current_page(self.container.page_num(page_instance))
        self.update_tab_bar_visibility()

        self.keepass_loader = KeepassLoader(self.filechooser_creation_dialog.get_filename(), "liufhre86ewoiwejmrcu8owe")
        DatabaseCreationGui(page_instance, self.keepass_loader)


    def update_tab_bar_visibility(self):
        if self.container.get_n_pages() > 1:
            self.container.set_show_tabs(True)
        else:
            self.container.set_show_tabs(False)

    #
    # Events
    #

    def on_tab_close_button_clicked(self, sender, widget):
        page_num = self.container.page_num(widget)
        self.container.remove_page(page_num)
        self.update_tab_bar_visibility()

    def on_cancel_button_clicked(self, widget):
        self.override_dialog.destroy()
        self.filechooser_creation_dialog.destroy()

    def on_override_button_clicked(self, widget):
        self.create_tab()
        self.override_dialog.destroy()


main_window = MainWindow()
main_window.show_all()
Gtk.main()
