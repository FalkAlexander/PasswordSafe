# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import threading
from gettext import gettext as _
from typing import List
from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Handy

import passwordsafe.config_manager
from passwordsafe.container_page import ContainerPage
from passwordsafe.create_database import CreateDatabase
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.error_info_bar import ErrorInfoBar
from passwordsafe.recent_files_page import RecentFilesPage
from passwordsafe.save_dialog import SaveDialog
from passwordsafe.unlock_database import UnlockDatabase
from passwordsafe.unlocked_database import UnlockedDatabase
from passwordsafe.welcome_page import WelcomePage


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/main_window.ui")
class MainWindow(Handy.ApplicationWindow):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    __gtype_name__ = "MainWindow"

    database_manager = NotImplemented
    opened_databases: List[UnlockedDatabase] = []
    databases_to_save: List[UnlockedDatabase] = []
    _filechooser = None

    container = Gtk.Template.Child()
    _headerbar = Gtk.Template.Child()
    _main_view = Gtk.Template.Child()
    new_file_button = Gtk.Template.Child()
    new_file_stack = Gtk.Template.Child()
    open_file_button = Gtk.Template.Child()
    open_file_stack = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _title_stack = Gtk.Template.Child()

    mobile_layout = GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = self.get_application()
        self._info_bar = None
        self._info_bar_response_id = None
        self.welcome_page = WelcomePage()
        self.recent_files_page = RecentFilesPage()

        self._main_view.add(self.welcome_page)
        self._main_view.add(self.recent_files_page)

        self.assemble_window()

        if Gio.Application.get_default().development_mode is True:
            passwordsafe.config_manager.set_development_backup_mode(True)

    def set_titlebar(self, headerbar: Handy.Headebar) -> None:
        if headerbar not in self._title_stack.get_children():
            self._title_stack.add(headerbar)
        self._title_stack.set_visible_child(headerbar)

    def assemble_window(self) -> None:
        window_size = passwordsafe.config_manager.get_window_size()
        self.resize(window_size[0], window_size[1])

        self.create_headerbar()
        self.load_custom_css()
        self.apply_theme()
        self.invoke_initial_screen()

    #
    # Headerbar
    #

    def create_headerbar(self):
        self.set_titlebar(self._headerbar)

        if Gio.Application.get_default().development_mode is True:
            context = self.get_style_context()
            context.add_class("devel")

    def set_headerbar(self):
        self.set_titlebar(self._headerbar)

    def get_headerbar(self):
        return self._headerbar

    #
    # Styles
    #

    def load_custom_css(self) -> None:  # pylint: disable=R0201
        """Load passwordsafe.css and enable it"""
        screen = Gdk.Screen.get_default()

        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("org/gnome/PasswordSafe/passwordsafe.css")

        context = self.get_style_context()
        context.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def apply_theme(self) -> None:  # pylint: disable=R0201
        """Set the bright/dark theme depending on the configuration"""
        gtk_settings = Gtk.Settings.get_default()

        gtk_settings.set_property(
            "gtk-application-prefer-dark-theme",
            passwordsafe.config_manager.get_dark_theme())

    #
    # Responsive Listener
    #

    def do_size_allocate(self, allocation: Gdk.Rectangle) -> None:  # pylint: disable=W0221
        """Handler for resizing event. It is used to check if
        the layout needs to be updated.

        :param GdkEvent event: event
        """
        new_mobile_layout = (self.get_allocation().width < 700)
        if new_mobile_layout != self.props.mobile_layout:
            self.props.mobile_layout = new_mobile_layout
            self.change_layout()

        Handy.ApplicationWindow.do_size_allocate(self, allocation)

    def change_layout(self):
        """Switches all open databases between mobile/desktop layout"""
        for database in self.opened_databases:
            # Do Nothing on Lock Screen
            if database.props.database_locked:
                return

            # Do nothing for Search View
            if database.props.search_active:
                return

            scrolled_page = database.get_current_page()

            # For Group/Entry Edit Page
            if scrolled_page.edit_page:
                return

    @Gtk.Template.Callback()
    def _on_mobile_layout_changed(self, _window, _value):
        if self.props.mobile_layout:
            self.open_file_stack.set_visible_child_name("mobile")
            self.new_file_stack.set_visible_child_name("mobile")
        else:
            self.open_file_stack.set_visible_child_name("desktop")
            self.new_file_stack.set_visible_child_name("desktop")

    #
    # First Start Screen
    #

    def invoke_initial_screen(self) -> None:
        """Present the first start screen if required or autoload files

        If the configuration is set to automatically load the last
        opened safe, this function does that. If it is not set to
        autoload, it presents a list of recently loaded files (or
        displays the empty welcome page if there are no recently
        loaded files).
        """
        if self.application.file_list:
            # file_list is appended to when we invoke the app with
            # files as cmd line parameters. (it is also appended to
            # whenever we open a file via app.open action). If it is
            # populated, simply load those files and don't show any
            # screens.
            for g_file in self.application.file_list:
                self.start_database_opening_routine(g_file.get_path())
            return

        if passwordsafe.config_manager.get_first_start_screen():
            # simply load the last opened file
            filepath = None
            file: Gio.File = Gio.File.new_for_uri(
                passwordsafe.config_manager.get_last_opened_database()
            )
            if Gio.File.query_exists(file):
                filepath = file.get_path()
                logging.debug("Opening last opened database: %s", filepath)
                self.start_database_opening_routine(filepath)
                return

        # Display the screen with last opened files (or welcome page)
        self.display_recent_files_list()

    def display_recent_files_list(self) -> None:
        """Shows the list of recently opened files or invokes welcome page"""
        if not passwordsafe.config_manager.get_last_opened_list():
            logging.debug("No recent files saved")
            self.display_welcome_page()
            return

        recent_files_page = RecentFilesPage()

        if recent_files_page.is_empty:
            logging.debug("No recent files")
            self.display_welcome_page()
            return

        self._main_view.set_visible_child(self.recent_files_page)

    def display_welcome_page(self) -> None:
        """Shown when there is no autoloading and no recent files to display"""
        self._main_view.set_visible_child(self.welcome_page)

    #
    # Open Database Methods
    #

    def _on_info_bar_response(self, _info_bar=None, _response_id=None):
        self._info_bar.hide()
        self._info_bar.disconnect(self._info_bar_response_id)
        self._info_bar = None
        self._info_bar_response_id = None

    @Gtk.Template.Callback()
    def open_filechooser(self, _widget, _user_data=None):
        """Callback function to open a safe.
        This callback can be called from an action activate event or
        a clicked event from a button. In the latter case, no user_data
        is set. Having None as a default value allows to handle both
        events reliably.
        """
        # pylint: disable=too-many-locals
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

        # We need to hold a reference, otherwise the app crashes.
        self._filechooser = filechooser_opening_dialog
        filechooser_opening_dialog.connect("response", self._on_open_filechooser_response, supported_mime_types)
        filechooser_opening_dialog.show()

    def _on_open_filechooser_response(self,
                                      dialog: Gtk.Dialog,
                                      response: Gtk.ResponseType,
                                      supported_mime_types: List[str]) -> None:
        self._filechooser = None
        if response == Gtk.ResponseType.ACCEPT:
            db_filename = dialog.get_file().get_path()
            logging.debug("File selected: %s", db_filename)

            db_gfile = Gio.File.new_for_path(db_filename)
            try:
                db_file_info = db_gfile.query_info(
                    # https://gitlab.gnome.org/GNOME/gvfs/-/issues/529
                    # we can remove standard::content-type when the fix
                    # is merged in distros' gvfs version.
                    "standard::content-type,standard::fast-content-type", Gio.FileQueryInfoFlags.NONE, None
                )
            except GLib.Error as e:  # pylint: disable=C0103
                logging.debug(
                    "Unable to query info for file %s: %s", db_filename, e.message
                )
                return

            file_content_type = db_file_info.get_attribute_as_string("standard::fast-content-type")
            file_mime_type = Gio.content_type_get_mime_type(file_content_type)
            if file_mime_type not in supported_mime_types:
                logging.debug(
                    "Unsupported mime type: %s", file_mime_type)
                main_message = _(
                    'Unable to open file "{}".'.format(db_filename))
                mime_desc = Gio.content_type_get_description(file_content_type)
                second_message = _(
                    "File type {} ({}) is not supported.".format(
                        mime_desc, file_mime_type))
                self._info_bar = ErrorInfoBar(main_message, second_message)
                self._info_bar_response_id = self._info_bar.connect(
                    "response", self._on_info_bar_response)

                # Get 1st child of  first_start_grid, to attach the info bar
                first_start_grid = None
                for child in self._main_view.get_children():
                    if child.props.name == "first_start_grid":
                        first_start_grid = child
                        break
                # FIXME: we should open the error in the info bar,
                # but there is no first_start_grid to attach it to. At
                # least don't crash now, this needs better fixing.
                if first_start_grid is None:
                    return
                first_child = self._main_view.get_visible_child()
                first_start_grid.attach_next_to(
                    self._info_bar, first_child, Gtk.PositionType.TOP, 1, 1)
                return

            database_already_opened = False

            for database in self.opened_databases:
                if database.database_manager.database_path == db_filename:
                    database_already_opened = True
                    page_num = self.container.page_num(database.parent_widget)
                    self.container.set_current_page(page_num)
                    database.show_database_action_revealer("Safe already opened")

            if database_already_opened is False:
                self.start_database_opening_routine(db_filename)
        elif response == Gtk.ResponseType.CANCEL:
            logging.debug("File selection canceled")

    def start_database_opening_routine(self, filepath: str) -> None:
        """Start opening a safe file"""
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/create_database_headerbar.ui")
        headerbar = builder.get_object("headerbar")
        tab_title: str = os.path.basename(filepath)
        UnlockDatabase(self, self.create_tab(tab_title, headerbar), filepath)
        self._main_view.set_visible_child(self.container)

    #
    # Create Database Methods
    #

    @Gtk.Template.Callback()
    def create_filechooser(self, _widget, _user_data=None):
        """Callback function to create a new safe.

        This callback can be called from an action activate event or
        a clicked event from a button. In the latter case, no user_data
        is set. Having None as a default value allows to handle both
        events reliably.
        """
        filechooser_creation_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for creating a new keepass safe kdbx file
            _("Choose location for Keepass safe"),
            self,
            Gtk.FileChooserAction.SAVE,
            _("_Create"),
            None,
        )
        filechooser_creation_dialog.set_current_name(_("Safe") + ".kdbx")
        filechooser_creation_dialog.set_modal(True)

        filter_text = Gtk.FileFilter()
        # NOTE: KeePass + version number is a proper name, do not translate
        filter_text.set_name(_("KeePass 3.1/4 Database"))
        filter_text.add_mime_type("application/x-keepass2")
        filechooser_creation_dialog.add_filter(filter_text)

        # We need to hold a reference, otherwise the app crashes.
        self._filechooser = filechooser_creation_dialog
        filechooser_creation_dialog.connect("response", self._on_create_filechooser_response)
        filechooser_creation_dialog.show()

    def _on_create_filechooser_response(self,
                                        dialog: Gtk.Dialog,
                                        response: Gtk.ResponseType) -> None:
        self._filechooser = None
        if response == Gtk.ResponseType.ACCEPT:
            filepath = dialog.get_file().get_path()

            self._spinner.start()
            self._main_view.set_visible_child(self._spinner)

            creation_thread = threading.Thread(
                target=self.create_new_database, args=[filepath]
            )
            creation_thread.daemon = True
            creation_thread.start()

    def create_new_database(self, filepath: str) -> None:
        """invoked in a separate thread to create a new safe."""

        # Copy our stock database file to `filepath`
        stock_db_file: Gio.File = Gio.File.new_for_uri(
            "resource:///org/gnome/PasswordSafe/database.kdbx")
        new_db_file: Gio.File = Gio.File.new_for_path(filepath)
        stock_db_file.copy(new_db_file, Gio.FileCopyFlags.OVERWRITE)

        tab_title: str = os.path.basename(filepath)
        self.database_manager = DatabaseManager(filepath,
                                                "liufhre86ewoiwejmrcu8owe")
        GLib.idle_add(self.start_database_creation_routine, tab_title)

    def start_database_creation_routine(self, tab_title):
        self._main_view.set_visible_child(self.container)
        self._spinner.stop()
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/create_database_headerbar.ui")
        headerbar = builder.get_object("headerbar")
        parent_widget = self.create_tab(tab_title, headerbar)
        back_button = builder.get_object("back_button")
        create_database = CreateDatabase(
            self, parent_widget,
            self.database_manager,
            back_button)
        self.set_titlebar(headerbar)
        parent_widget.add(create_database)
        back_button.connect("clicked",
                            create_database.on_headerbar_back_button_clicked)

    #
    # Tab Manager
    #

    def create_tab(self, title, headerbar):
        page_instance = ContainerPage(headerbar, Gio.Application.get_default().development_mode)

        tab_hbox = Gtk.Box.new(False, 0)
        tab_label = Gtk.Label.new(title)
        tab_hbox.add(tab_label)

        close_image = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        close_button = Gtk.Button()
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_focus_on_click(False)
        close_button.connect("clicked", self.on_tab_close_button_clicked, page_instance)
        close_button.add(close_image)

        tab_hbox.add(close_button)
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
            self.display_recent_files_list()
        elif not self.container.is_visible():
            self._main_view.set_visible_child(self.container)

    def close_tab(self, child_widget, database=None):
        """Remove a tab from the container.

        If database is defined, it is removed from the list of
        opened_databases

        :param GtkWidget child_widget: tab to close
        :param UnlockedDatabase database: database to remove
        """
        page_num = self.container.page_num(child_widget)
        self.container.remove_page(page_num)
        self.update_tab_bar_visibility()

        if database:
            self.opened_databases.remove(database)

    #
    # Events
    #

    def on_tab_close_button_clicked(self, _sender, widget):
        page_num = self.container.page_num(widget)

        for database in self.opened_databases:
            if database.window.container.page_num(database.parent_widget) == page_num:
                if database.database_manager.is_dirty:
                    if passwordsafe.config_manager.get_save_automatically():
                        database.cleanup()
                        database.save_database()
                    else:
                        save_dialog = SaveDialog(self)
                        save_dialog.connect("response",
                                            self._on_save_dialog_response,
                                            [widget, database])
                        save_dialog.show()
                else:
                    database.cleanup()
                    self.close_tab(widget, database)

                return

        self.close_tab(widget)

    def _on_save_dialog_response(self, dialog, response, args):
        widget, database = args
        dialog.close()
        if response == Gtk.ResponseType.YES:
            database.cleanup()
            self.close_tab(widget, database)
            database.save_database()
        elif response == Gtk.ResponseType.NO:
            database.cleanup()
            self.close_tab(widget, database)

    def on_tab_switch(self, _notebook, tab, _pagenum):
        headerbar = tab.get_headerbar()
        self.set_titlebar(headerbar)

    #
    # Application Quit Dialog
    #

    def save_window_size(self):
        window_size = [self.get_size().width, self.get_size().height]
        passwordsafe.config_manager.set_window_size(window_size)

    def do_delete_event(self, _event: Gdk.EventAny) -> bool:  # pylint:disable=W0221
        """invoked when we hit the window close button"""
        # Just invoke the app.quit action, it cleans up stuff
        # and will invoke the on_application_shutdown()
        self.application.activate_action("quit")
        return True  # we handled event, don't call destroy

    #
    # Gio Actions
    #

    # Find current displayed tab for executing the action
    def find_action_db(self):
        action_db = NotImplemented

        for database in self.opened_databases:
            if self.tab_visible(database.parent_widget):
                action_db = database

        return action_db

    # Entry/Group Row Popover Actions
    def add_row_popover_actions(self):
        actions = [
            ("element.delete", "on_element_delete_menu_button_clicked"),
            ("entry.duplicate", "on_entry_duplicate_menu_button_clicked"),
            ("entry.references", "on_entry_references_menu_button_clicked"),
            ("element.properties", "on_element_properties_menu_button_clicked"),
            ("group.edit", "on_group_edit_menu_button_clicked"),
            ("group.delete", "on_group_delete_menu_button_clicked")
        ]

        for action, name in actions:
            simple_action = Gio.SimpleAction.new(action, None)
            simple_action.connect("activate", self.execute_gio_action, name)
            self.application.add_action(simple_action)

    # MenuButton Popover Actions
    def add_database_menubutton_popover_actions(self):
        actions = [
            ("db.add_entry", "on_database_add_entry_clicked", None),
            ("db.add_group", "on_database_add_group_clicked", None),
            ("db.settings", "on_database_settings_entry_clicked", None),
            ("sort.az", "on_sort_menu_button_entry_clicked", "A-Z"),
            ("sort.za", "on_sort_menu_button_entry_clicked", "Z-A"),
            ("sort.last_added", "on_sort_menu_button_entry_clicked", "last_added"),
        ]

        for action, name, arg in actions:
            simple_action = Gio.SimpleAction.new(action, None)
            simple_action.connect(
                "activate", self.execute_gio_action, name, arg)
            self.application.add_action(simple_action)

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

    # Add Global Accelerator Actions
    # The save_dirty action differs to save in that it is set as disabled
    # by default, and it is used by the main menu to determine if the button
    # should be set to sensitive.
    def add_global_accelerator_actions(self):
        actions = [
            ("db.save", "save", None),
            ("db.save_dirty", "save_dirty", None),
            ("db.lock", "lock", None),
            ("db.add_entry", "add_action", "entry"),
            ("db.add_group", "add_action", "group"),
            ("go_back", "go_back", None),
        ]

        for action, name, arg in actions:
            simple_action = Gio.SimpleAction.new(action, None)
            if name == "save_dirty":
                simple_action.set_enabled(False)
            simple_action.connect(
                "activate", self.execute_accel_action, name, arg)
            self.application.add_action(simple_action)

    # Accelerator Action Handler
    def execute_accel_action(self, _action, _param, name, arg=None):
        action_db = self.find_action_db()
        if action_db is NotImplemented:
            return

        if name in ["save", "save_dirty"]:
            action_db.save_safe()
        elif name == "lock":
            action_db.lock_safe()
        elif name == "go_back":
            action_db.go_back()
        elif name == "add_action":
            if action_db.props.database_locked:
                return

            if action_db.props.selection_mode:
                return

            scrolled_page = action_db.get_current_page()
            if scrolled_page.edit_page:
                return

            if action_db.props.search_active:
                return

            if arg == "entry":
                action_db.on_add_entry_button_clicked(None)
            elif arg == "group":
                action_db.on_add_group_button_clicked(None)

    #
    # Tools
    #
    def tab_visible(self, tab):
        """Checks that the tab is visible

        :returns: True if the tab is visible
        :rtype: bool
        """
        current_page = self.container.get_current_page()
        return self.container.page_num(tab) == current_page
