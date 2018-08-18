from gi.repository import Gio, GLib, Gdk, Gtk, GObject
from gi.repository.GdkPixbuf import Pixbuf
from passwordsafe.logging_manager import LoggingManager
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.create_database import CreateDatabase
from passwordsafe.container_page import ContainerPage
from passwordsafe.unlock_database import UnlockDatabase
import passwordsafe.config_manager
import os
import ntpath
import gi
import signal
import dbus
from dbus.mainloop.glib import DBusGMainLoop
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')


class MainWindow(Gtk.ApplicationWindow):
    application = NotImplemented
    database_manager = NotImplemented
    container = NotImplemented
    quit_dialog = NotImplemented
    filechooser_creation_dialog = NotImplemented
    headerbar = NotImplemented
    first_start_grid = NotImplemented
    logging_manager = LoggingManager(True)
    opened_databases = []
    databases_to_save = []
    session_bus = NotImplemented

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.assemble_window()

    def assemble_window(self):
        window_size = passwordsafe.config_manager.get_window_size()
        self.set_default_size(window_size[0], window_size[1])
        
        self.create_headerbar()
        self.first_start_screen()

        self.connect("delete-event", self.on_application_quit)

        self.custom_css()
        self.apply_theme()

        self.start_gobject_main_loop()
        self.create_session_bus()

    #
    # Headerbar
    #

    def create_headerbar(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/main_window.ui")

        accelerators = Gtk.AccelGroup()
        self.add_accel_group(accelerators)

        self.headerbar = builder.get_object("headerbar")

        file_open_button = builder.get_object("open_button")
        file_open_button.connect("clicked", self.open_filechooser, None)
        self.bind_accelerator(accelerators, file_open_button, "<Control>o")

        file_new_button = builder.get_object("new_button")
        file_new_button.connect("clicked", self.create_filechooser, None)
        self.bind_accelerator(accelerators, file_new_button, "<Control>n")

        self.set_titlebar(self.headerbar)

    def set_headerbar(self):
        self.set_titlebar(self.headerbar)

    def get_headerbar(self):
        return self.headerbar

    #
    # Keystrokes
    #        

    def bind_accelerator(self, accelerators, widget, accelerator, signal="clicked"):
        key, mod = Gtk.accelerator_parse(accelerator)
        widget.add_accelerator(signal, accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

    #
    # Styles
    #

    def custom_css(self):
        screen = Gdk.Screen.get_default()

        css_provider = Gtk.CssProvider()
        css_provider_resource = Gio.File.new_for_uri(
            "resource:///org/gnome/PasswordSafe/passwordsafe.css")
        css_provider.load_from_file(css_provider_resource)

        context = Gtk.StyleContext()
        context.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def apply_theme(self):
        gtk_settings = Gtk.Settings.get_default()

        if passwordsafe.config_manager.get_dark_theme() is True:
            gtk_settings.set_property("gtk-application-prefer-dark-theme", True)
        else:
            gtk_settings.set_property("gtk-application-prefer-dark-theme", False)

    #
    # DBus
    #

    def start_gobject_main_loop(self):
        DBusGMainLoop(set_as_default=True)
        self.gobject_mainloop = GObject.MainLoop()

    def cancel_gobject_main_loop(self):
        self.gobject_mainloop.quit()

    def create_session_bus(self):
        self.session_bus = dbus.SessionBus()

    #
    # First Start Screen
    #

    def first_start_screen(self):
        filepath = Gio.File.new_for_path(passwordsafe.config_manager.get_last_opened_database()).get_path()

        if len(self.get_application().file_list) is not 0:
            for g_file in self.get_application().file_list:
                self.start_database_opening_routine(g_file.get_basename(), g_file.get_path())
        elif passwordsafe.config_manager.get_first_start_screen() is True and filepath is not "" and Gio.File.query_exists(Gio.File.new_for_path(filepath)) is True:
            self.logging_manager.log_debug("Found last opened database (" + filepath + ")")
            tab_title = ntpath.basename(filepath)
            self.start_database_opening_routine(tab_title, filepath)
        else:
            self.logging_manager.log_debug(
                "No / Not valid last opened database found.")
            self.assemble_first_start_screen()

    def assemble_first_start_screen(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/main_window.ui")

        pix = Pixbuf.new_from_resource_at_scale("/org/gnome/PasswordSafe/images/welcome.png", 256, 256, True)

        if len(passwordsafe.config_manager.get_last_opened_list()) is not 0:
            last_opened_list_box = builder.get_object("last_opened_list_box")
            last_opened_list_box.connect("row-activated", self.on_last_opened_list_box_activated)

            entry_list = []
            entries = 0
            invalid = 0

            for path in passwordsafe.config_manager.get_last_opened_list():
                entries = entries + 1
                if Gio.File.query_exists(Gio.File.new_for_uri(path)):
                    pbuilder = Gtk.Builder()
                    pbuilder.add_from_resource("/org/gnome/PasswordSafe/main_window.ui")

                    last_opened_row = pbuilder.get_object("last_opened_row")
                    filename_label = pbuilder.get_object("filename_label")
                    path_label = pbuilder.get_object("path_label")

                    filename_label.set_text(os.path.splitext(ntpath.basename(path))[0])
                    if "/home/" in path:
                        path_label.set_text("~/" + os.path.relpath(Gio.File.new_for_uri(path).get_path()))
                    else:
                        path_label.set_text(path)
                    last_opened_row.set_name(path)


                    entry_list.append(last_opened_row)
                else:
                    invalid = invalid + 1

            if entries == invalid:
                app_logo = builder.get_object("app_logo")
                app_logo.set_from_pixbuf(pix)
                self.first_start_grid = builder.get_object("first_start_grid")
                self.add(self.first_start_grid)
            else:
                for row in reversed(entry_list):
                    last_opened_list_box.add(row)

                self.first_start_grid = builder.get_object("last_opened_grid")
                self.add(self.first_start_grid)
        else:
            app_logo = builder.get_object("app_logo")
            app_logo.set_from_pixbuf(pix)
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
        filter_text.add_mime_type("application/octet-stream")
        filechooser_opening_dialog.add_filter(filter_text)
        filechooser_opening_dialog.set_local_only(False)

        response = filechooser_opening_dialog.run()
        if response == Gtk.ResponseType.OK:
            self.logging_manager.log_debug(
                "File selected: " + filechooser_opening_dialog.get_filename())
            filechooser_opening_dialog.close()

            database_already_opened = False

            for db in self.opened_databases:
                if db.database_manager.database_path == filechooser_opening_dialog.get_filename():
                    database_already_opened = True
                    page_num = self.container.page_num(db.parent_widget)
                    self.container.set_current_page(page_num)
                    db.show_database_action_revealer("Database already opened")

            if database_already_opened is False:
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
            "/org/gnome/PasswordSafe/create_database.ui")
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
        self.filechooser_creation_dialog.set_do_overwrite_confirmation(True)
        self.filechooser_creation_dialog.set_current_name("Database.kdbx")
        self.filechooser_creation_dialog.set_modal(True)
        self.filechooser_creation_dialog.set_local_only(False)

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Keepass 2 Database")
        filter_text.add_mime_type("application/x-keepass2")
        self.filechooser_creation_dialog.add_filter(filter_text)

        response = self.filechooser_creation_dialog.run()
        if response == Gtk.ResponseType.OK:
            self.copy_database_file()
            tab_title = self.create_tab_title_from_filepath(self.filechooser_creation_dialog.get_current_name())
            self.start_database_creation_routine(tab_title)
        elif response == Gtk.ResponseType.CANCEL:
            self.filechooser_creation_dialog.close()            

    def copy_database_file(self):
        stock_database = Gio.File.new_for_uri(
            "resource:///org/gnome/PasswordSafe/database.kdbx")
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
            "/org/gnome/PasswordSafe/create_database.ui")
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

        if self.container.get_n_pages() is 0:
            self.container.hide()
            self.remove(self.container)

            builder = Gtk.Builder()
            builder.add_from_resource(
                "/org/gnome/PasswordSafe/main_window.ui")

            pix = Pixbuf.new_from_resource_at_scale("/org/gnome/PasswordSafe/images/welcome.png", 256, 256, True)

            self.assemble_first_start_screen()
        else:
            if not self.container.is_visible():
                self.remove(self.first_start_grid)
                self.add(self.container)
                self.container.show_all()

    def create_tab_title_from_filepath(self, filepath):
        return ntpath.basename(filepath)

    def close_tab(self, child_widget):
        page_num = self.container.page_num(child_widget)
        self.container.remove_page(page_num)
        self.update_tab_bar_visibility()

    #
    # Events
    #

    def on_last_opened_list_box_activated(self, widget, list_box_row):
        path = list_box_row.get_name()
        self.start_database_opening_routine(ntpath.basename(path), Gio.File.new_for_uri(path).get_path())

    def on_tab_close_button_clicked(self, sender, widget):
        page_num = self.container.page_num(widget)
        is_contained = False

        for db in self.opened_databases:
            if db.window.container.page_num(db.parent_widget) == page_num:
                is_contained = True
                if db.database_manager.made_database_changes() is True:
                    db.show_save_dialog(True)
                else:
                    self.container.remove_page(page_num)
                    self.update_tab_bar_visibility()
                    self.opened_databases.remove(db)

        if is_contained is False:
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
        for db in self.opened_databases:
            self.session_bus.remove_signal_receiver(db.on_session_lock, 'ActiveChanged', 'org.gnome.ScreenSaver', path='/org/gnome/ScreenSaver')
            db.cancel_timers()
            db.remove_session_bus_signal()

        for db in self.databases_to_save:
            db.database_manager.save_database()

        self.gobject_mainloop.quit()
        self.quit_dialog.destroy()
        self.save_window_size()
        self.application.quit()

    #
    # Application Quit Dialog
    #

    def save_window_size(self):
        window_size = [self.get_size().width, self.get_size().height]
        passwordsafe.config_manager.set_window_size(window_size)

    def on_application_quit(self, window, event):
        unsaved_databases_list = []
        for db in self.opened_databases:
            if db.database_manager.changes is True:
                unsaved_databases_list.append(db)

        if unsaved_databases_list.__len__() > 0:
            builder = Gtk.Builder()
            builder.add_from_resource(
                "/org/gnome/PasswordSafe/quit_dialog.ui")
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
                if "/home/" in db.database_manager.database_path:
                    check_button.set_label("~/" + os.path.relpath(db.database_manager.database_path))
                else:
                    check_button.set_label(Gio.File.new_for_path(db.database_manager.database_path).get_uri())
                check_button.connect("toggled", self.on_save_check_button_toggled, db)
                check_button.set_active(True)
                unsaved_database_row.add(check_button)
                unsaved_database_row.show_all()
                unsaved_databases_list_box.add(unsaved_database_row)

            self.quit_dialog.present()

            return(True)      
        else:
            self.save_window_size()

            for db in self.opened_databases:
                self.session_bus.remove_signal_receiver(db.on_session_lock, 'ActiveChanged', 'org.gnome.ScreenSaver', path='/org/gnome/ScreenSaver')
                db.cancel_timers()

            self.gobject_mainloop.quit()

            
