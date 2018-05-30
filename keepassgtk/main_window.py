from gi.repository import Gio, Gdk, Gtk
from keepassgtk.logging_manager import LoggingManager
from keepassgtk.database_manager import DatabaseManager
from keepassgtk.create_database import CreateDatabase
from keepassgtk.container_page import ContainerPage
from keepassgtk.unlock_database import UnlockDatabase
import keepassgtk.config_manager
import os
from os.path import exists
import ntpath
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')


class MainWindow(Gtk.ApplicationWindow):
    application = NotImplemented
    database_manager = NotImplemented
    container = NotImplemented
    override_dialog = NotImplemented
    quit_dialog = NotImplemented
    filechooser_creation_dialog = NotImplemented
    headerbar = NotImplemented
    first_start_grid = NotImplemented
    logging_manager = LoggingManager(True)
    opened_databases = []
    databases_to_save = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        keepassgtk.config_manager.configure()
        self.assemble_window()

    def assemble_window(self):
        self.set_default_size(800, 500)
        
        self.create_headerbar()
        self.first_start_screen()

        self.connect("delete-event", self.on_application_quit)

        self.custom_css()

    #
    # Headerbar
    #

    def create_headerbar(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/main_window.ui")

        self.headerbar = builder.get_object("headerbar")

        file_open_button = builder.get_object("open_button")
        file_open_button.connect("clicked", self.open_filechooser, None)

        file_new_button = builder.get_object("new_button")
        file_new_button.connect("clicked", self.create_filechooser, None)

        self.set_titlebar(self.headerbar)

    def set_headerbar(self):
        self.set_titlebar(self.headerbar)

    def get_headerbar(self):
        return self.headerbar

    #
    # Styles
    #

    def custom_css(self):
        screen = Gdk.Screen.get_default()

        css_provider = Gtk.CssProvider()
        css_provider_resource = Gio.File.new_for_uri(
            "resource:///run/terminal/KeepassGtk/keepassgtk.css")
        css_provider.load_from_file(css_provider_resource)

        context = Gtk.StyleContext()
        context.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    #
    # First Start Screen
    #

    def first_start_screen(self):
        if keepassgtk.config_manager.has_group("history") and keepassgtk.config_manager.get_string("history", "last-opened-db") != "" and exists(keepassgtk.config_manager.get_string("history", "last-opened-db")):
            self.logging_manager.log_debug(
                "Found last opened database entry (" +
                keepassgtk.config_manager.get_string(
                    "history", "last-opened-db") + ")")

            tab_title = ntpath.basename(keepassgtk.config_manager.get_string(
                "history", "last-opened-db"))
            self.start_database_opening_routine(
                tab_title,
                keepassgtk.config_manager.get_string(
                    "history", "last-opened-db"))
        else:
            self.logging_manager.log_debug(
                "No / Not valid last opened database entry found.")
            builder = Gtk.Builder()
            builder.add_from_resource(
                "/run/terminal/KeepassGtk/main_window.ui")

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

    def open_filechooser(self, widget, none):
        filechooser_opening_dialog = Gtk.FileChooserDialog(
            "Choose Keepass Database", self, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Keepass 2 Database")
        filter_text.add_mime_type("application/x-keepass2")
        filechooser_opening_dialog.add_filter(filter_text)

        response = filechooser_opening_dialog.run()
        if response == Gtk.ResponseType.OK:
            self.logging_manager.log_debug(
                "File selected: " + filechooser_opening_dialog.get_filename())
            filechooser_opening_dialog.close()

            tab_title = self.create_tab_title_from_filepath(
                filechooser_opening_dialog.get_filename())
            self.start_database_opening_routine(
                tab_title, filechooser_opening_dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            self.logging_manager.log_debug("File selection canceled")
            filechooser_opening_dialog.close()

    def start_database_opening_routine(self, tab_title, filepath):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/run/terminal/KeepassGtk/create_database.ui")
        headerbar = builder.get_object("headerbar")

        UnlockDatabase(self, self.create_tab(tab_title, headerbar), filepath)

    #
    # Create Database Methods
    #

    def create_filechooser(self, widget, none):
        self.filechooser_creation_dialog = Gtk.FileChooserDialog(
            "Create new Database", self, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
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
            builder.add_from_resource(
                "/run/terminal/KeepassGtk/override_dialog.ui")
            self.override_dialog = builder.get_object("override_dialog")

            self.override_dialog.set_destroy_with_parent(True)
            self.override_dialog.set_modal(True)
            self.override_dialog.set_transient_for(self.filechooser_creation_dialog)

            cancel_button = builder.get_object("cancel_button")
            override_button = builder.get_object("override_button")

            cancel_button.connect("clicked", self.on_cancel_button_clicked)
            override_button.connect("clicked", self.on_override_button_clicked)

            self.override_dialog.present()
        else:
            self.copy_database_file()

            tab_title = self.create_tab_title_from_filepath(self.filechooser_creation_dialog.get_current_name())
            self.start_database_creation_routine(tab_title)

    def copy_database_file(self):
        stock_database = Gio.File.new_for_uri(
            "resource:///run/terminal/KeepassGtk/database.kdbx")
        new_database = Gio.File.new_for_path(
            self.filechooser_creation_dialog.get_filename())

        stock_database.copy(new_database, Gio.FileCopyFlags.OVERWRITE)
        self.filechooser_creation_dialog.close()

    def start_database_creation_routine(self, tab_title):
        self.database_manager = DatabaseManager(
            self.filechooser_creation_dialog.get_filename(),
            "liufhre86ewoiwejmrcu8owe")
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/run/terminal/KeepassGtk/create_database.ui")
        headerbar = builder.get_object("headerbar")
        CreateDatabase(
            self, self.create_tab(tab_title, headerbar),
            self.database_manager)

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
        return ntpath.basename(filepath)

    def close_tab(self, child_widget):
        page_num = self.container.page_num(child_widget)
        self.container.remove_page(page_num)
        self.update_tab_bar_visibility()

    #
    # Events
    #

    def on_tab_close_button_clicked(self, sender, widget):
        page_num = self.container.page_num(widget)

        for db in self.opened_databases:
            if db.window.container.page_num(db.parent_widget) == page_num:
                self.opened_databases.remove(db)

        self.container.remove_page(page_num)
        self.update_tab_bar_visibility()

    def on_cancel_button_clicked(self, widget):
        self.override_dialog.destroy()
        self.filechooser_creation_dialog.destroy()

    def on_override_button_clicked(self, widget):
        self.copy_database_file()

        tab_title = self.create_tab_title_from_filepath(
            self.filechooser_creation_dialog.get_current_name())
        self.start_database_creation_routine(tab_title)

        self.override_dialog.destroy()

    def on_tab_switch(self, notebook, tab, pagenum):
        headerbar = tab.get_headerbar()
        self.set_titlebar(headerbar)

    def on_save_check_button_toggled(self, check_button, db):
        if check_button.get_active():
            self.databases_to_save.append(db)
        else:
            self.databases_to_save.remove(db)

    def on_back_button_clicked(self, button):
        self.databases_to_save.clear()
        self.quit_dialog.destroy()

    def on_quit_button_clicked(self, button):
        for db in self.databases_to_save:
            db.database_manager.save_database()

        self.quit_dialog.destroy()
        self.application.quit()

    #
    # Application Quit Dialog
    #

    def on_application_quit(self, window, event):
        unsaved_databases_list = []
        for db in self.opened_databases:
            if db.database_manager.changes is True:
                unsaved_databases_list.append(db)

        if unsaved_databases_list.__len__() > 0:
            builder = Gtk.Builder()
            builder.add_from_resource(
                "/run/terminal/KeepassGtk/quit_dialog.ui")
            self.quit_dialog = builder.get_object("quit_dialog")

            self.quit_dialog.set_destroy_with_parent(True)
            self.quit_dialog.set_modal(True)
            self.quit_dialog.set_transient_for(self)

            back_button = builder.get_object("back_button")
            quit_button = builder.get_object("quit_button")

            back_button.connect("clicked", self.on_back_button_clicked)
            quit_button.connect("clicked", self.on_quit_button_clicked)

            unsaved_databases_list_box = builder.get_object("unsaved_databases_list_box")
                
            for db in unsaved_databases_list:
                unsaved_database_row = Gtk.ListBoxRow()
                check_button = Gtk.CheckButton()
                check_button.set_label(db.database_manager.database_path)
                check_button.connect("toggled", self.on_save_check_button_toggled, db)
                unsaved_database_row.add(check_button)
                unsaved_database_row.show_all()
                unsaved_databases_list_box.add(unsaved_database_row)

            self.quit_dialog.present()

            return(True)         
