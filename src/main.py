import os
from os.path import exists
import shutil
import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk
import pykeepass
from pykeepass import PyKeePass
import config_manager
import logging_manager
import database
from database import KeepassLoader
import database_creation_gui
from database_creation_gui import DatabaseCreationGui
import container_page
from container_page import ContainerPage
import database_opening_gui
from database_opening_gui import DatabaseOpeningGui

class MainWindow(Gtk.Window):

    keepass_loader = NotImplemented
    container = NotImplemented
    override_dialog = NotImplemented
    filechooser_creation_dialog = NotImplemented
    headerbar = NotImplemented
    first_start_grid = NotImplemented


    def __init__(self):
        config_manager.configure()
        self.assemble_window()


    def assemble_window(self):
        Gtk.Window.__init__(self, title="KeepassGtk")
        self.connect("destroy", Gtk.main_quit)
        self.set_default_size(800, 500)

        self.enable_debug()

        self.create_headerbar()

        self.first_start_screen()

    def enable_debug(self):
        logging_manager.debug = True

    #
    # Headerbar
    #

    def create_headerbar(self):
        builder = Gtk.Builder()
        builder.add_from_file("ui/main_headerbar.ui")
        
        self.headerbar = builder.get_object("headerbar")

        file_open_button = builder.get_object("open_button")
        file_open_button.connect("clicked", self.open_filechooser)

        file_new_button = builder.get_object("new_button")
        file_new_button.connect("clicked", self.create_filechooser)

        self.set_titlebar(self.headerbar)


    def set_headerbar(self):
        self.set_titlebar(self.headerbar)

    
    def get_headerbar(self):
        return self.headerbar

    #
    # First Start Screen
    #    

    def first_start_screen(self):
        if config_manager.has_group("history") and config_manager.get_string("history", "last-opened-db") != "" and exists(config_manager.get_string("history", "last-opened-db")):
            logging_manager.log_debug("Found last opened database entry (" + config_manager.get_string("history", "last-opened-db") + ")")

            regex = re.search("^(([A-Z]:)?[\.]?[\\{1,2}/]?.*[\\{1,2}/])*(.+)\.(.+)", config_manager.get_string("history", "last-opened-db"))
            tab_title = regex[0]
            self.start_database_opening_routine(tab_title, config_manager.get_string("history", "last-opened-db"))
        else:
            logging_manager.log_debug("No / Not valid last opened database entry found.")
            builder = Gtk.Builder()
            builder.add_from_file("ui/main_headerbar.ui")

            self.first_start_grid = builder.get_object("first_start_grid")
            self.add(self.first_start_grid)

    #
    # Container Methods (Gtk Notebook holds tabs)
    #

    def create_container(self):
        if self.first_start_grid != NotImplemented:
            self.first_start_grid.destroy()

        self.container = Gtk.Notebook()

        self.container.set_border_width(0)
        self.container.set_scrollable(True)
        self.container.set_show_border(False)
        self.container.connect("switch-page", self.on_tab_switch)

        self.add(self.container)
        self.show_all()


    def destroy_container(self):
        self.container.destroy()

    #
    # Open Database Methods
    #

    def open_filechooser(self, widget):
        filechooser_opening_dialog = Gtk.FileChooserDialog("Choose Keepass Database", self, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Keepass 2 Database")
        filter_text.add_mime_type("application/x-keepass2")
        filechooser_opening_dialog.add_filter(filter_text)

        response = filechooser_opening_dialog.run()
        if response == Gtk.ResponseType.OK:
            logging_manager.log_debug("File selected: " + filechooser_opening_dialog.get_filename())
            filechooser_opening_dialog.close()

            folder_path = filechooser_opening_dialog.get_current_folder() + "/"
            file_path = filechooser_opening_dialog.get_filename()

            tab_title = self.create_tab_title_from_filepath(file_path.replace(folder_path, ""))
            self.start_database_opening_routine(tab_title, filechooser_opening_dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            logging_manager.log_debug("File selection canceled")
            filechooser_opening_dialog.close()

    def start_database_opening_routine(self, tab_title, filepath):
        #self.keepass_loader = KeepassLoader(self.filechooser_creation_dialog.get_filename(), "liufhre86ewoiwejmrcu8owe")
        builder = Gtk.Builder()
        builder.add_from_file("ui/create_database.ui")
        headerbar = builder.get_object("headerbar")

        DatabaseOpeningGui(self, self.create_tab(tab_title, headerbar), filepath)   


    #
    # Create Database Methods
    #

    def create_filechooser(self, widget):
        self.filechooser_creation_dialog = Gtk.FileChooserDialog("Create new Database", self, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        self.filechooser_creation_dialog.set_current_name("Database.kdbx")
        self.filechooser_creation_dialog.set_modal(True)

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Keepass 2 Database")
        filter_text.add_mime_type("application/x-keepass2")
        self.filechooser_creation_dialog.add_filter(filter_text)

        response = self.filechooser_creation_dialog.run()
        if response == Gtk.ResponseType.OK:
            self.does_file_exist()   
        elif response == Gtk.ResponseType.CANCEL:
            self.filechooser_creation_dialog.close()


    def does_file_exist(self):
        if os.path.exists(self.filechooser_creation_dialog.get_filename()):
            builder = Gtk.Builder()
            builder.add_from_file("ui/override_dialog.ui")
            self.override_dialog = builder.get_object("override_dialog")

            self.override_dialog.set_parent(self.filechooser_creation_dialog)
            self.override_dialog.set_destroy_with_parent(True)
            self.override_dialog.set_modal(True)

            cancel_button = builder.get_object("cancel_button")
            override_button = builder.get_object("override_button")

            cancel_button.connect("clicked", self.on_cancel_button_clicked)
            override_button.connect("clicked", self.on_override_button_clicked)

            self.override_dialog.show_all()
        else:
            self.copy_database_file()

            tab_title = self.create_tab_title_from_filepath(self.filechooser_creation_dialog.get_current_name())
            self.start_database_creation_routine(tab_title)


    def copy_database_file(self):
        shutil.copy2('data/database.kdbx', self.filechooser_creation_dialog.get_filename())
        self.filechooser_creation_dialog.close()


    def start_database_creation_routine(self, tab_title):
        self.keepass_loader = KeepassLoader(self.filechooser_creation_dialog.get_filename(), "liufhre86ewoiwejmrcu8owe")
        builder = Gtk.Builder()
        builder.add_from_file("ui/create_database.ui")
        headerbar = builder.get_object("headerbar")
        DatabaseCreationGui(self, self.create_tab(tab_title, headerbar), self.keepass_loader)

    #
    # Tab Manager
    #

    def create_tab(self, title, headerbar):
        if self.container == NotImplemented:
            self.create_container()

        page_instance = ContainerPage(headerbar)

        tab_hbox = Gtk.HBox(False, 0)
        tab_label = Gtk.Label(title)
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

        return page_instance


    def update_tab_bar_visibility(self):
        if self.container.get_n_pages() > 1:
            self.container.set_show_tabs(True)
        else:
            self.container.set_show_tabs(False)


    def create_tab_title_from_filepath(self, filepath):
        regex = re.search("[^\.]+", filepath)
        title = regex[0]
        return title


    def close_tab(self, child_widget):
        page_num = self.container.page_num(child_widget)
        self.container.remove_page(page_num)
        self.update_tab_bar_visibility()

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
        self.copy_database_file()

        tab_title = self.create_tab_title_from_filepath(self.filechooser_creation_dialog.get_current_name())
        self.start_database_creation_routine(tab_title)

        self.override_dialog.destroy()


    def on_tab_switch(self, notebook, tab, pagenum):
        headerbar = tab.get_headerbar()
        self.set_titlebar(headerbar)


main_window = MainWindow()
main_window.show_all()
Gtk.main()
