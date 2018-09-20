from gi.repository import Gio, GLib, Gdk, Gtk, Handy
from gi.repository.GdkPixbuf import Pixbuf
from passwordsafe.logging_manager import LoggingManager
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.create_database import CreateDatabase
from passwordsafe.container_page import ContainerPage
from passwordsafe.unlock_database import UnlockDatabase
import passwordsafe.config_manager
import os
import ntpath
import threading
from gettext import gettext as _


class MainWindow(Gtk.ApplicationWindow):
    application = NotImplemented
    database_manager = NotImplemented
    container = NotImplemented
    quit_dialog = NotImplemented
    filechooser_creation_dialog = NotImplemented
    headerbar = NotImplemented
    file_open_button = NotImplemented
    file_new_button = NotImplemented
    first_start_grid = NotImplemented
    logging_manager = LoggingManager(True)
    opened_databases = []
    databases_to_save = []
    spinner = NotImplemented

    mobile_width = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.assemble_window()

    def assemble_window(self):
        window_size = passwordsafe.config_manager.get_window_size()
        self.set_default_size(window_size[0], window_size[1])

        self.create_headerbar()
        self.first_start_screen()

        self.connect("delete-event", self.on_application_quit)
        self.connect("check-resize", self.responsive_listener)

        self.custom_css()
        self.apply_theme()

    #
    # Headerbar
    #

    def create_headerbar(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/main_window.ui")

        self.headerbar = builder.get_object("headerbar")

        self.file_open_button = builder.get_object("open_button")
        self.file_open_button.connect("clicked", self.open_filechooser, None)

        self.file_new_button = builder.get_object("new_button")
        self.file_new_button.connect("clicked", self.create_filechooser, None)

        self.set_headerbar_button_layout()

        self.set_titlebar(self.headerbar)

    def set_headerbar(self):
        self.set_headerbar_button_layout()
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
    # Responsive Listener
    #

    def responsive_listener(self, window):
        if self.get_allocation().width < 700:
            if self.mobile_width is True:
                return

            self.mobile_width = True
            self.change_layout()
        else:
            if self.mobile_width is True:
                self.mobile_width = False
                self.change_layout()

    def change_layout(self):
        for db in self.opened_databases:
            # Do Nothing on Lock Screen
            if db.database_locked is True:
                return

            # For Search View
            if db.stack.get_visible_child() is db.stack.get_child_by_name("search"):
                return

            page_uuid = db.database_manager.get_group_uuid_from_group_object(db.current_group)
            group_page = NotImplemented
            if db.database_manager.check_is_group(page_uuid) is True:
                group_page = True
            else:
                group_page = False
            scrolled_page = db.stack.get_child_by_name(page_uuid)

            # For Group/Entry Edit Page
            if scrolled_page.edit_page is True and group_page is True:
                db.responsive_ui.action_bar()
                db.responsive_ui.headerbar_title()
                db.responsive_ui.headerbar_back_button()
                return
            elif scrolled_page.edit_page is True and group_page is False:
                db.responsive_ui.action_bar()
                db.responsive_ui.headerbar_title()
                db.responsive_ui.headerbar_back_button()
                return

            # For Entry/Group Browser and Selection Mode
            db.responsive_ui.action_bar()
            db.responsive_ui.headerbar_title()
            db.responsive_ui.headerbar_back_button()
            db.responsive_ui.headerbar_selection_button()

        if self.container is NotImplemented or self.container.get_n_pages() == 0:
            self.set_headerbar_button_layout()

    def set_headerbar_button_layout(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/main_window.ui")

        if self.mobile_width is True:
            self.file_open_button.get_children()[0].set_visible_child_name("mobile")
            self.file_new_button.get_children()[0].set_visible_child_name("mobile")
        else:
            self.file_open_button.get_children()[0].set_visible_child_name("desktop")
            self.file_new_button.get_children()[0].set_visible_child_name("desktop")

    #
    # First Start Screen
    #

    def first_start_screen(self):
        filepath = Gio.File.new_for_uri(passwordsafe.config_manager.get_last_opened_database()).get_path()

        if len(self.get_application().file_list) is not 0:
            for g_file in self.get_application().file_list:
                self.start_database_opening_routine(g_file.get_basename(), g_file.get_path())
        elif passwordsafe.config_manager.get_first_start_screen() is True and filepath is not "" and filepath is not None and os.path.exists(filepath) is True:
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

                # Responsive Container
                hdy = Handy.Column()
                hdy.set_maximum_width(400)
                hdy.add(builder.get_object("select_box"))

                self.first_start_grid.add(hdy)
                self.first_start_grid.show_all()

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
        filechooser_opening_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for opening an existing keepass safe kdbx file
            _("Choose a Keepass safe"), self, Gtk.FileChooserAction.OPEN,
            None, None)

        filter_text = Gtk.FileFilter()
        # NOTE: KeePass + version number is a proper name, do not translate
        filter_text.set_name(_("KeePass 3.1/4 Database"))
        filter_text.add_mime_type("application/x-keepass2")
        filter_text.add_mime_type("application/octet-stream")
        filechooser_opening_dialog.add_filter(filter_text)
        filechooser_opening_dialog.set_local_only(False)

        response = filechooser_opening_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.logging_manager.log_debug(
                "File selected: " + filechooser_opening_dialog.get_filename())

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
        self.filechooser_creation_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for creating a new keepass safe kdbx file
            _("Choose location for Keepass safe"), self, Gtk.FileChooserAction.SAVE,
            _("Save"), None)
        self.filechooser_creation_dialog.set_do_overwrite_confirmation(True)
        self.filechooser_creation_dialog.set_current_name(_("Safe") + ".kdbx")
        self.filechooser_creation_dialog.set_modal(True)
        self.filechooser_creation_dialog.set_local_only(False)

        filter_text = Gtk.FileFilter()
        # NOTE: KeePass + version number is a proper name, do not translate
        filter_text.set_name(_("KeePass 3.1/4 Database"))
        filter_text.add_mime_type("application/x-keepass2")
        self.filechooser_creation_dialog.add_filter(filter_text)

        response = self.filechooser_creation_dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.copy_database_file()
            tab_title = self.create_tab_title_from_filepath(self.filechooser_creation_dialog.get_current_name())

            creation_thread = threading.Thread(target=self.create_new_database_instance, args=[tab_title])
            creation_thread.daemon = True
            creation_thread.start()

            if self.get_children()[0] is self.first_start_grid:
                self.remove(self.first_start_grid)
            builder = Gtk.Builder()
            builder.add_from_resource("/org/gnome/PasswordSafe/main_window.ui")
            if self.get_children()[0] is not self.container:
                self.spinner = builder.get_object("spinner_grid")
                self.add(self.spinner)

    def copy_database_file(self):
        stock_database = Gio.File.new_for_uri(
            "resource:///org/gnome/PasswordSafe/database.kdbx")
        new_database = Gio.File.new_for_path(
            self.filechooser_creation_dialog.get_filename())

        stock_database.copy(new_database, Gio.FileCopyFlags.OVERWRITE)

    def create_new_database_instance(self, tab_title):
        self.database_manager = DatabaseManager(self.filechooser_creation_dialog.get_filename(), "liufhre86ewoiwejmrcu8owe")
        GLib.idle_add(self.start_database_creation_routine, tab_title)

    def start_database_creation_routine(self, tab_title):
        if self.get_children()[0] is self.spinner:
            self.remove(self.spinner)

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

        tab_hbox = Gtk.HBox.new(False, 0)
        tab_label = Gtk.Label.new(title)
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
                db.database_locked = True
                db.stop_save_loop()
                is_contained = True
                if db.database_manager.made_database_changes() is True:
                    if passwordsafe.config_manager.get_save_automatically() is True:
                        save_thread = threading.Thread(target=db.database_manager.save_database)
                        save_thread.daemon = False
                        save_thread.start()
                    else:
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
            db.cancel_timers()
            db.unregister_dbus_signal()

        if len(self.databases_to_save) > 0:
            save_thread = threading.Thread(target=self.threaded_database_saving)
            save_thread.daemon = False
            save_thread.start()
        else:
            self.quit_gtkwindow()

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
                if passwordsafe.config_manager.get_save_automatically() is True:
                    db.stop_save_loop()
                    save_thread = threading.Thread(target=db.database_manager.save_database)
                    save_thread.daemon = False
                    save_thread.start()
                else:
                    unsaved_databases_list.append(db)

        if unsaved_databases_list.__len__() > 1:
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
        elif unsaved_databases_list.__len__() == 1:
            for db in unsaved_databases_list:
                db.cancel_timers()
                db.unregister_dbus_signal()
                db.show_save_dialog(True, False, True)
                return(True)
        else:
            self.save_window_size()

            for db in self.opened_databases:
                db.cancel_timers()

    #
    # Gio Actions
    #

    # Find current displayed tab for executing the action
    def find_action_db(self):
        action_db = NotImplemented

        for db in self.opened_databases:
            if db.window.container.page_num(db.parent_widget) == self.container.get_current_page():
                action_db = db

        return action_db

    # Entry/Group Row Popover Actions
    def add_row_popover_actions(self):
        delete_entry_action = Gio.SimpleAction.new("entry.delete", None)
        delete_entry_action.connect("activate", self.execute_gio_action, "on_entry_delete_menu_button_clicked")
        self.application.add_action(delete_entry_action)

        edit_group_action = Gio.SimpleAction.new("group.edit", None)
        edit_group_action.connect("activate", self.execute_gio_action, "on_group_edit_menu_button_clicked")
        self.application.add_action(edit_group_action)

        delete_group_action = Gio.SimpleAction.new("group.delete", None)
        delete_group_action.connect("activate", self.execute_gio_action, "on_group_delete_menu_button_clicked")
        self.application.add_action(delete_group_action)

    # MenuButton Popover Actions
    def add_database_menubutton_popover_actions(self):
        db_settings_action = Gio.SimpleAction.new("db.settings", None)
        db_settings_action.connect("activate", self.execute_gio_action, "on_database_settings_entry_clicked")
        self.application.add_action(db_settings_action)

        az_button_action = Gio.SimpleAction.new("sort.az", None)
        az_button_action.connect("activate", self.execute_gio_action, "on_sort_menu_button_entry_clicked", "A-Z")
        self.application.add_action(az_button_action)

        za_button_action = Gio.SimpleAction.new("sort.za", None)
        za_button_action.connect("activate", self.execute_gio_action, "on_sort_menu_button_entry_clicked", "Z-A")
        self.application.add_action(za_button_action)

        last_added_button_action = Gio.SimpleAction.new("sort.last_added", None)
        last_added_button_action.connect("activate", self.execute_gio_action, "on_sort_menu_button_entry_clicked", "last_added")
        self.application.add_action(last_added_button_action)

    # Selection Mode Actions
    def add_selection_actions(self):
        selection_all_action = Gio.SimpleAction.new("selection.all", None)
        selection_all_action.connect("activate", self.execute_gio_action, "on_selection_popover_button_clicked", "all")
        self.application.add_action(selection_all_action)

        selection_none_action = Gio.SimpleAction.new("selection.none", None)
        selection_none_action.connect("activate", self.execute_gio_action, "on_selection_popover_button_clicked", "none")
        self.application.add_action(selection_none_action)

    # Gio Action Handler
    def execute_gio_action(self, action, param, name, arg=None):
        action_db = self.find_action_db()
        if action_db is NotImplemented:
            return

        if name == "on_entry_delete_menu_button_clicked":
            action_db.on_entry_delete_menu_button_clicked(action, param)
        elif name == "on_group_edit_menu_button_clicked":
            action_db.on_group_edit_menu_button_clicked(action, param)
        elif name == "on_group_delete_menu_button_clicked":
            action_db.on_group_delete_menu_button_clicked(action, param)
        elif name == "on_database_settings_entry_clicked":
            action_db.on_database_settings_entry_clicked(action, param)
        elif name == "on_sort_menu_button_entry_clicked":
            action_db.on_sort_menu_button_entry_clicked(action, param, arg)
        elif name == "on_selection_popover_button_clicked":
            action_db.selection_ui.on_selection_popover_button_clicked(action, param, arg)

    # Add Global Accelerator Actions
    def add_global_accelerator_actions(self):
        save_action = Gio.SimpleAction.new("db.save", None)
        save_action.connect("activate", self.execute_accel_action, "save")
        self.application.add_action(save_action)

        lock_action = Gio.SimpleAction.new("db.lock", None)
        lock_action.connect("activate", self.execute_accel_action, "lock")
        self.application.add_action(lock_action)

        add_entry_action = Gio.SimpleAction.new("db.add_entry", None)
        add_entry_action.connect("activate", self.execute_accel_action, "add_action", "entry")
        self.application.add_action(add_entry_action)

        add_group_action = Gio.SimpleAction.new("db.add_group", None)
        add_group_action.connect("activate", self.execute_accel_action, "add_action", "group")
        self.application.add_action(add_group_action)

    # Accelerator Action Handler
    def execute_accel_action(self, action, param, name, arg=None):
        action_db = self.find_action_db()
        if action_db is NotImplemented:
            return

        if name == "save":
            action_db.on_save_button_clicked(None)
        elif name == "lock":
            action_db.on_lock_button_clicked(None)
        elif name == "add_action":
            if action_db.database_locked is True:
                return

            if action_db.selection_ui.selection_mode_active is True:
                return

            group_uuid = action_db.database_manager.get_group_uuid_from_group_object(action_db.current_group)
            scrolled_page = action_db.stack.get_child_by_name(group_uuid)
            if scrolled_page.edit_page is True:
                return

            if action_db.stack.get_visible_child() is action_db.stack.get_child_by_name("search"):
                return

            if arg == "entry":
                action_db.on_add_entry_button_clicked(None)
            elif arg == "group":
                action_db.on_add_group_button_clicked(None)

    #
    # Tools
    #

    def threaded_database_saving(self):
        for db in self.databases_to_save:
            db.database_manager.save_database()

        GLib.idle_add(self.quit_gtkwindow)

    def quit_gtkwindow(self):
        self.quit_dialog.destroy()
        self.save_window_size()
        self.application.quit()
            
