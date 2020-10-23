from gettext import gettext as _
from gi.repository import Gio, GLib, Gdk, Gtk, Handy
from gi.repository.GdkPixbuf import Pixbuf
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.create_database import CreateDatabase
from passwordsafe.container_page import ContainerPage
from passwordsafe.error_info_bar import ErrorInfoBar
from passwordsafe.unlock_database import UnlockDatabase
import passwordsafe.config_manager

import logging
import os
import ntpath
import threading


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
    opened_databases = []
    databases_to_save = []
    spinner = NotImplemented

    mobile_width = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._info_bar = None
        self._info_bar_response_id = None

        self.assemble_window()

        if Gio.Application.get_default().development_mode is True:
            passwordsafe.config_manager.set_development_backup_mode(True)

    def assemble_window(self):
        window_size = passwordsafe.config_manager.get_window_size()
        self.set_default_size(window_size[0], window_size[1])

        self.create_headerbar()
        self.first_start_screen()

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

        if Gio.Application.get_default().development_mode is True:
            context = self.get_style_context()
            context.add_class("devel")

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

    def responsive_listener(self, win: Gtk.ApplicationWindow):
        """invoked on check-resize events"""
        if self.get_allocation().width < 700:
            if not self.mobile_width:
                self.mobile_width = True
                self.change_layout()
        else:
            if self.mobile_width:
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
            scrolled_page = db.stack.get_child_by_name(page_uuid.urn)

            # For Entry/Group Browser, Edit Page and Selection Mode
            db.responsive_ui.action_bar()
            db.responsive_ui.headerbar_title()
            db.responsive_ui.headerbar_back_button()
            if not scrolled_page.edit_page:
                db.responsive_ui.headerbar_selection_button()

        if self.container is NotImplemented \
           or self.container.get_n_pages() == 0:
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

        if self.get_application().file_list:
            for g_file in self.get_application().file_list:
                self.start_database_opening_routine(g_file.get_basename(), g_file.get_path())
        elif passwordsafe.config_manager.get_first_start_screen() and filepath and os.path.exists(filepath):
            logging.debug("Found last opened database: %s", filepath)
            tab_title = ntpath.basename(filepath)
            self.start_database_opening_routine(tab_title, filepath)
        else:
            self.logging.debug("No / Not valid last opened database found.")
            self.assemble_first_start_screen()

    def assemble_first_start_screen(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/main_window.ui")

        pix = Pixbuf.new_from_resource_at_scale("/org/gnome/PasswordSafe/images/welcome.png", 256, 256, True)

        if passwordsafe.config_manager.get_last_opened_list():
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
                hdy = Handy.Clamp()
                hdy.set_maximum_size(400)
                hdy.props.vexpand = True
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

    def _on_info_bar_response(self, _info_bar=None, _response_id=None):
        self._info_bar.hide()
        self._info_bar.disconnect(self._info_bar_response_id)
        self._info_bar = None
        self._info_bar_response_id = None

    def open_filechooser(self, _widget, _none):
        if self._info_bar is not None:
            self._on_info_bar_response()

        filechooser_opening_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for opening an existing keepass safe kdbx file
            _("Choose a Keepass safe"), self, Gtk.FileChooserAction.OPEN,
            None, None)

        supported_mime_types = [
            "application/x-keepass2",
            "application/octet-stream"
        ]

        filter_text = Gtk.FileFilter()
        # NOTE: KeePass + version number is a proper name, do not translate
        filter_text.set_name(_("KeePass 3.1/4 Database"))
        for mime_type in supported_mime_types:
            filter_text.add_mime_type(mime_type)
        filechooser_opening_dialog.add_filter(filter_text)
        filechooser_opening_dialog.set_local_only(False)

        response = filechooser_opening_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            db_filename = filechooser_opening_dialog.get_filename()
            logging.debug("File selected: %s", db_filename)

            db_gfile = Gio.File.new_for_path(db_filename)
            try:
                db_file_info = db_gfile.query_info(
                    "standard::content-type", Gio.FileQueryInfoFlags.NONE,
                    None)
            except GLib.Error as e:
                logging.debug("Unable to query info for file {}: {}".format(
                    db_filename, e.message))
                return

            file_content_type = db_file_info.get_content_type()
            file_mime_type = Gio.content_type_get_mime_type(file_content_type)
            if file_mime_type not in supported_mime_types:
                logging.debug(
                    "Unsupported mime type {}".format(file_mime_type))
                main_message = _(
                    'Unable to open file "{}".'.format(db_filename))
                mime_desc = Gio.content_type_get_description(file_content_type)
                second_message = _(
                    "File type {} ({}) is not supported.".format(
                        mime_desc, file_mime_type))
                self._info_bar = ErrorInfoBar(main_message, second_message)
                self._info_bar_response_id = self._info_bar.connect(
                    "response", self._on_info_bar_response)
                first_child = self.first_start_grid.get_children()[0]
                self.first_start_grid.attach_next_to(
                    self._info_bar, first_child, Gtk.PositionType.TOP, 1, 1)
                return

            database_already_opened = False

            for db in self.opened_databases:
                if db.database_manager.database_path == db_filename:
                    database_already_opened = True
                    page_num = self.container.page_num(db.parent_widget)
                    self.container.set_current_page(page_num)
                    db.show_database_action_revealer("Database already opened")

            if database_already_opened is False:
                tab_title = self.create_tab_title_from_filepath(db_filename)
                self.start_database_opening_routine(tab_title, db_filename)
        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection canceled")

    def start_database_opening_routine(self, tab_title, filepath):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/create_database.ui")
        headerbar = builder.get_object("headerbar")

        UnlockDatabase(self, self.create_tab(tab_title, headerbar), filepath)

    #
    # Create Database Methods
    #

    def create_filechooser(self, _widget, _none):
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

        page_instance = ContainerPage(headerbar, Gio.Application.get_default().development_mode)

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

        if not self.container.get_n_pages():
            self.container.hide()
            self.remove(self.container)

            builder = Gtk.Builder()
            builder.add_from_resource(
                "/org/gnome/PasswordSafe/main_window.ui")

            Pixbuf.new_from_resource_at_scale("/org/gnome/PasswordSafe/images/welcome.png", 256, 256, True)

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

    def on_last_opened_list_box_activated(self, _widget, list_box_row):
        path = list_box_row.get_name()
        self.start_database_opening_routine(ntpath.basename(path), Gio.File.new_for_uri(path).get_path())

    def on_tab_close_button_clicked(self, _sender, widget):
        page_num = self.container.page_num(widget)
        is_contained = False

        for db in self.opened_databases:
            if db.window.container.page_num(db.parent_widget) == page_num:
                db.database_locked = True
                db.stop_save_loop()
                db.clipboard.clear()
                is_contained = True
                if db.database_manager.is_dirty:
                    if passwordsafe.config_manager.get_save_automatically() is True:
                        save_thread = threading.Thread(target=db.database_manager.save_database)
                        save_thread.daemon = False
                        save_thread.start()
                    else:
                        db.show_save_dialog()
                else:
                    self.container.remove_page(page_num)
                    self.update_tab_bar_visibility()
                    self.opened_databases.remove(db)

        if is_contained is False:
            self.container.remove_page(page_num)
            self.update_tab_bar_visibility()

    def on_cancel_button_clicked(self, _widget):
        self.override_dialog.destroy()
        self.filechooser_creation_dialog.destroy()

    def on_override_button_clicked(self, _widget):
        self.copy_database_file()

        tab_title = self.create_tab_title_from_filepath(
            self.filechooser_creation_dialog.get_current_name())
        self.start_database_creation_routine(tab_title)

        self.override_dialog.destroy()

    def on_tab_switch(self, _notebook, tab, _pagenum):
        headerbar = tab.get_headerbar()
        self.set_titlebar(headerbar)

    def on_save_check_button_toggled(self, check_button, db):
        if check_button.get_active():
            self.databases_to_save.append(db)
        else:
            self.databases_to_save.remove(db)

    #
    # Application Quit Dialog
    #

    def save_window_size(self):
        window_size = [self.get_size().width, self.get_size().height]
        passwordsafe.config_manager.set_window_size(window_size)

    def do_delete_event(self, _window) -> bool:
        """invoked when we hit the window close button"""
        # Just invoke the app.quit action, it cleans up stuff
        # and will invoke the on_application_shutdown()
        self.application.activate_action("quit")
        return True  # we handled event, don't call destroy

    def on_application_shutdown(self) -> bool:
        """Clean up unsaved databases, and shutdown

        This function is invoked by the application.quit method
        :returns: True if handled (don't quit), False if shutdown
        """
        unsaved_databases_list = []
        self.databases_to_save.clear()

        for db in self.opened_databases:
            if db.database_manager.is_dirty \
               and not db.database_manager.save_running:
                if passwordsafe.config_manager.get_save_automatically() is True:
                    db.stop_save_loop()
                    save_thread = threading.Thread(target=db.database_manager.save_database)
                    save_thread.daemon = False
                    save_thread.start()
                else:
                    unsaved_databases_list.append(db)

        if len(unsaved_databases_list) == 1:
            res = db.show_save_dialog()  # This will also save it
            if not res:
                return True  # User Canceled, don't quit
        elif len(unsaved_databases_list) > 1:
            # Multiple unsaved files, ask which to save
            builder = Gtk.Builder()
            builder.add_from_resource(
                "/org/gnome/PasswordSafe/quit_dialog.ui")
            self.quit_dialog = builder.get_object("quit_dialog")
            self.quit_dialog.set_transient_for(self)

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

            res = self.quit_dialog.run()
            self.quit_dialog.destroy()
            if res == Gtk.ResponseType.CANCEL:
                self.databases_to_save.clear()
                return True
            elif res == Gtk.ResponseType.OK:
                pass  # Do noting, go on...

        for db in self.opened_databases:
            db.cancel_timers()
            db.unregister_dbus_signal()
            db.clipboard.clear()
            for tmpfile in db.scheduled_tmpfiles_deletion:
                try:
                    tmpfile.delete()
                except Exception:
                    logging.warning("Skipping deletion of tmpfile...")

        self.save_window_size()
        if self.databases_to_save:
            # This will invoke application.quit() when done...
            save_thread = threading.Thread(target=self.threaded_database_saving)
            save_thread.daemon = False
            save_thread.start()
            return True
        return False  # caller should quit() the app
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
        delete_element_action = Gio.SimpleAction.new("element.delete", None)
        delete_element_action.connect("activate", self.execute_gio_action, "on_element_delete_menu_button_clicked")
        self.application.add_action(delete_element_action)

        duplicate_entry_action = Gio.SimpleAction.new("entry.duplicate", None)
        duplicate_entry_action.connect("activate", self.execute_gio_action, "on_entry_duplicate_menu_button_clicked")
        self.application.add_action(duplicate_entry_action)

        references_entry_action = Gio.SimpleAction.new("entry.references", None)
        references_entry_action.connect("activate", self.execute_gio_action, "on_entry_references_menu_button_clicked")
        self.application.add_action(references_entry_action)

        properties_element_action = Gio.SimpleAction.new("element.properties", None)
        properties_element_action.connect("activate", self.execute_gio_action, "on_element_properties_menu_button_clicked")
        self.application.add_action(properties_element_action)

        edit_group_action = Gio.SimpleAction.new("group.edit", None)
        edit_group_action.connect("activate", self.execute_gio_action, "on_group_edit_menu_button_clicked")
        self.application.add_action(edit_group_action)

        delete_group_action = Gio.SimpleAction.new("group.delete", None)
        delete_group_action.connect("activate", self.execute_gio_action, "on_group_delete_menu_button_clicked")
        self.application.add_action(delete_group_action)

    # MenuButton Popover Actions
    def add_database_menubutton_popover_actions(self):
        db_add_entry_action = Gio.SimpleAction.new("db.add_entry", None)
        db_add_entry_action.connect("activate", self.execute_gio_action, "on_database_add_entry_clicked")
        self.application.add_action(db_add_entry_action)

        db_add_group_action = Gio.SimpleAction.new("db.add_group", None)
        db_add_group_action.connect("activate", self.execute_gio_action, "on_database_add_group_clicked")
        self.application.add_action(db_add_group_action)

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

        if name == "on_element_delete_menu_button_clicked":
            action_db.on_element_delete_menu_button_clicked(action, param)
        elif name == "on_entry_duplicate_menu_button_clicked":
            action_db.on_entry_duplicate_menu_button_clicked(action, param)
        elif name == "on_entry_references_menu_button_clicked":
            action_db.show_references_dialog(action, param)
        elif name == "on_element_properties_menu_button_clicked":
            action_db.show_properties_dialog(action, param)
        elif name == "on_group_edit_menu_button_clicked":
            action_db.on_group_edit_menu_button_clicked(action, param)
        elif name == "on_group_delete_menu_button_clicked":
            action_db.on_group_delete_menu_button_clicked(action, param)
        elif name == "on_database_add_entry_clicked":
            action_db.on_add_entry_button_clicked(None)
        elif name == "on_database_add_group_clicked":
            action_db.on_add_group_button_clicked(None)
        elif name == "on_database_settings_entry_clicked":
            action_db.on_database_settings_entry_clicked(action, param)
        elif name == "on_sort_menu_button_entry_clicked":
            action_db.on_sort_menu_button_entry_clicked(action, param, arg)
        elif name == "on_selection_popover_button_clicked":
            action_db.selection_ui.on_selection_popover_button_clicked(action, param, arg)
        elif name == "on_edit_undo":
            action_db.undo_redo_receiver(arg)
        elif name == "on_edit_redo":
            action_db.undo_redo_receiver(arg)

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

        undo_action = Gio.SimpleAction.new("undo")
        undo_action.connect("activate", self.execute_gio_action, "on_edit_undo", "undo")
        self.application.add_action(undo_action)

        redo_action = Gio.SimpleAction.new("redo")
        redo_action.connect("activate", self.execute_gio_action, "on_edit_redo", "redo")
        self.application.add_action(redo_action)

    # Accelerator Action Handler
    def execute_accel_action(self, _action, _param, name, arg=None):
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
            scrolled_page = action_db.stack.get_child_by_name(group_uuid.urn)
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
        """Saves all databases and calls quit()

        Suitable to be called from a separate thread"""
        for db in self.databases_to_save:
            db.database_manager.save_database()
        GLib.idle_add(self.application.quit)
