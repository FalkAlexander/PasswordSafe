from gi.repository import Gio, Gdk, Gtk
from keepassgtk.logging_manager import LoggingManager
from keepassgtk.pathbar import Pathbar
from keepassgtk.entry_row import EntryRow
from keepassgtk.group_row import GroupRow
from keepassgtk.scrolled_page import ScrolledPage
from keepassgtk.database_settings_dialog import DatabaseSettingsDialog
from threading import Timer
import keepassgtk.password_generator 
import keepassgtk.config_manager
import gi
import ntpath

gi.require_version('Gtk', '3.0')


class UnlockedDatabase:
    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    headerbar = NotImplemented
    headerbar_search = NotImplemented
    scrolled_window = NotImplemented
    stack = NotImplemented
    database_manager = NotImplemented
    logging_manager = LoggingManager(True)
    current_group = NotImplemented
    pathbar = NotImplemented
    overlay = NotImplemented
    scheduled_page_destroy = []
    clipboard = NotImplemented
    list_box_sorting = NotImplemented
    clipboard_timer = NotImplemented
    database_lock_timer = NotImplemented
    search_list_box = NotImplemented

    entry_marked_for_delete = NotImplemented
    group_marked_for_delete = NotImplemented
    group_marked_for_edit = NotImplemented

    def __init__(self, window, widget, dbm):
        self.window = window
        self.parent_widget = widget
        self.database_manager = dbm
        self.assemble_listbox()
        self.window.opened_databases.append(self)

    #
    # Stack Pages
    #

    def assemble_listbox(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/run/terminal/KeepassGtk/unlocked_database.ui")

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        self.overlay = Gtk.Overlay()
        self.parent_widget.add(self.overlay)

        database_action_overlay = self.builder.get_object("database_action_overlay")

        self.overlay.add_overlay(database_action_overlay)

        self.current_group = self.database_manager.get_root_group()

        self.stack = self.builder.get_object("list_stack")
        self.overlay.add(self.stack)
        self.overlay.show_all()

        self.set_headerbar()
        self.prepare_actions()

        self.list_box_sorting = keepassgtk.config_manager.get_sort_order()
        self.start_database_lock_timer()

        self.show_page_of_new_directory(False)

    #
    # Headerbar
    #

    # Assemble headerbar
    def set_headerbar(self):
        self.headerbar = self.builder.get_object("headerbar")

        save_button = self.builder.get_object("save_button")
        save_button.connect("clicked", self.on_save_button_clicked)

        lock_button = self.builder.get_object("lock_button")
        lock_button.connect("clicked", self.on_lock_button_clicked)

        mod_box = self.builder.get_object("mod_box")
        browser_buttons_box = self.builder.get_object("browser_buttons_box")
        mod_box.add(browser_buttons_box)

        search_button = self.builder.get_object("search_button")
        search_button.connect("clicked", self.set_search_headerbar)

        add_entry_button = self.builder.get_object("add_entry_button")
        add_entry_button.connect("clicked", self.on_add_entry_button_clicked)

        add_group_button = self.builder.get_object("add_group_button")
        add_group_button.connect("clicked", self.on_add_group_button_clicked)

        add_property_button = self.builder.get_object("add_property_button")
        add_property_button.connect("clicked", self.on_add_property_button_clicked)

        # Search Headerbar
        headerbar_search_box_close_button = self.builder.get_object("headerbar_search_box_close_button")
        headerbar_search_box_close_button.connect("clicked", self.on_headerbar_search_close_button_clicked)

        search_settings_popover_local_button = self.builder.get_object("search_settings_popover_local_button")
        search_settings_popover_fulltext_button = self.builder.get_object("search_settings_popover_fulltext_button")

        search_local_button = self.builder.get_object("search_local_button")
        search_local_button.connect("toggled", self.on_search_filter_button_toggled)

        search_fulltext_button = self.builder.get_object("search_fulltext_button")
        search_fulltext_button.connect("toggled", self.on_search_filter_button_toggled)

        headerbar_search_entry = self.builder.get_object("headerbar_search_entry")
        headerbar_search_entry.connect("changed", self.on_headerbar_search_entry_changed, search_local_button, search_fulltext_button)
        headerbar_search_entry.connect("activate", self.on_headerbar_search_entry_enter_pressed)

        self.set_gio_actions()

        self.parent_widget.set_headerbar(self.headerbar)
        self.window.set_titlebar(self.headerbar)

        self.pathbar = Pathbar(self, self.database_manager, self.database_manager.get_root_group(), self.headerbar)

    def set_gio_actions(self):
        db_settings_action = Gio.SimpleAction.new("db.settings", None)
        db_settings_action.connect("activate", self.on_database_settings_entry_clicked)

        az_button_action = Gio.SimpleAction.new("sort.az", None)
        az_button_action.connect("activate", self.on_sort_menu_button_entry_clicked, "A-Z")

        za_button_action = Gio.SimpleAction.new("sort.za", None)
        za_button_action.connect("activate", self.on_sort_menu_button_entry_clicked, "Z-A")

        last_added_button_action = Gio.SimpleAction.new("sort.last_added", None)
        last_added_button_action.connect("activate", self.on_sort_menu_button_entry_clicked, "last_added")

        self.window.application.add_action(db_settings_action)
        self.window.application.add_action(az_button_action)
        self.window.application.add_action(za_button_action)
        self.window.application.add_action(last_added_button_action)

        #menubutton_popover_a_z_button = self.builder.get_object("menubutton_popover_a-z_button")
        #box = menubutton_popover_a_z_button.get_children()[0]
        #radio_box = Gtk.Box()
        #box.add(radio_box)
        #radio_box.set_halign(Gtk.Align.END)
        #radio_button = Gtk.RadioButton()
        #radio_box.add(radio_button)
        #radio_box.set_hexpand(True)
        #menubutton_popover_a_z_button.show_all()

    # Search headerbar
    def set_search_headerbar(self, widget):
        hscb = self.builder.get_object("headerbar_search_box_close_button")
        if hscb.get_active() is False:
            hscb.set_active(True)

        self.headerbar_search = self.builder.get_object("headerbar_search")
        self.parent_widget.set_headerbar(self.headerbar_search)
        self.window.set_titlebar(self.headerbar_search)
        self.builder.get_object("headerbar_search_entry").grab_focus()

        self.prepare_search_page()

    def remove_search_headerbar(self, widget):
        self.parent_widget.set_headerbar(self.headerbar)
        self.window.set_titlebar(self.headerbar)

    # Group and entry browser headerbar
    def set_browser_headerbar(self):
        mod_box = self.builder.get_object("mod_box")

        for child in mod_box.get_children():
            mod_box.remove(child)

        mod_box.add(self.builder.get_object("browser_buttons_box"))

    # Entry creation/editing page headerbar
    def set_entry_page_headerbar(self):
        mod_box = self.builder.get_object("mod_box")

        for child in mod_box.get_children():
            mod_box.remove(child)

        mod_box.add(self.builder.get_object("entry_page_mod_box"))

        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)
        scrolled_page = self.stack.get_child_by_name(entry_uuid)
        if scrolled_page.add_button_disabled is True:
            self.builder.get_object("add_property_button").set_sensitive(False)
        else:
            self.builder.get_object("add_property_button").set_sensitive(True)

    # Group creation/editing headerbar
    def set_group_edit_page_headerbar(self):
        mod_box = self.builder.get_object("mod_box")

        for child in mod_box.get_children():
            mod_box.remove(child)

    # Actions for MenuButton Popover
    def prepare_actions(self):
        delete_entry_action = Gio.SimpleAction.new("entry.delete", None)
        delete_entry_action.connect("activate", self.on_entry_delete_menu_button_clicked)
        self.window.application.add_action(delete_entry_action)

        edit_group_action = Gio.SimpleAction.new("group.edit", None)
        edit_group_action.connect("activate", self.on_group_edit_menu_button_clicked)
        self.window.application.add_action(edit_group_action)

        delete_group_action = Gio.SimpleAction.new("group.delete", None)
        delete_group_action.connect("activate", self.on_group_delete_menu_button_clicked)
        self.window.application.add_action(delete_group_action)

    # Set Search stack page
    def prepare_search_page(self):
        if self.stack.get_child_by_name("search") is None:
            scrolled_page = ScrolledPage(False)
            viewport = Gtk.Viewport()
            builder = Gtk.Builder()
            builder.add_from_resource("/run/terminal/KeepassGtk/unlocked_database.ui")
            self.search_list_box = builder.get_object("list_box")
            self.search_list_box.connect("row-activated", self.on_list_box_row_activated)
            viewport.add(self.search_list_box)
            scrolled_page.add(viewport)
            scrolled_page.show_all()
            self.stack.add_named(scrolled_page, "search")

        self.stack.set_visible_child(self.stack.get_child_by_name("search"))

    #
    # Group and Entry Management
    #

    def show_page_of_new_directory(self, edit_group):
        # First, remove stack pages which should not exist because they are scheduled for remove
        self.destroy_scheduled_stack_page()

        # Check if we need to remove the search headerbar
        if self.parent_widget.get_headerbar() is not self.headerbar:
            self.remove_search_headerbar(None)

        # Creation of group edit page
        if edit_group is True:
            self.destroy_scheduled_stack_page()

            builder = Gtk.Builder()
            builder.add_from_resource("/run/terminal/KeepassGtk/group_page.ui")

            scrolled_window = ScrolledPage(True)

            viewport = Gtk.Viewport()
            scrolled_window.properties_list_box = builder.get_object("properties_list_box")
            viewport.add(scrolled_window.properties_list_box)
            scrolled_window.add(viewport)
            scrolled_window.show_all()

            stack_page_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)
            if self.stack.get_child_by_name(stack_page_uuid) is not None:
                stack_page = self.stack.get_child_by_name(stack_page_uuid)
                stack_page.destroy()

            self.add_stack_page(scrolled_window)
            self.insert_group_properties_into_listbox(scrolled_window.properties_list_box)
            self.set_group_edit_page_headerbar()     
        # If the stack page with current group's uuid isn't existing - we need to create it (first time opening of group/entry)       
        elif self.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is None and self.stack.get_child_by_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group)) is None and edit_group is False:
            # Create not existing stack page for group
            if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
                builder = Gtk.Builder()
                builder.add_from_resource("/run/terminal/KeepassGtk/unlocked_database.ui")
                list_box = builder.get_object("list_box")
                list_box.connect("row-activated", self.on_list_box_row_activated)

                scrolled_window = ScrolledPage(False)
                viewport = Gtk.Viewport()
                viewport.add(list_box)
                scrolled_window.add(viewport)
                scrolled_window.show_all()

                self.add_stack_page(scrolled_window)
                self.insert_groups_into_listbox(list_box)
                self.insert_entries_into_listbox(list_box)
            # Create not existing stack page for entry
            else:
                builder = Gtk.Builder()
                builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

                scrolled_window = ScrolledPage(True)

                viewport = Gtk.Viewport()
                scrolled_window.properties_list_box = builder.get_object("properties_list_box")
                viewport.add(scrolled_window.properties_list_box)
                scrolled_window.add(viewport)
                scrolled_window.show_all()

                self.add_stack_page(scrolled_window)
                self.insert_entry_properties_into_listbox(scrolled_window.properties_list_box, False)
        # Stack page with current group's uuid already exists, we only need to switch stack page
        else:
            # For group
            if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
                self.stack.set_visible_child_name(self.database_manager.get_group_uuid_from_group_object(self.current_group))
                self.set_browser_headerbar()
            # For entry
            else:
                self.stack.set_visible_child_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
                self.set_entry_page_headerbar()

    def add_stack_page(self, scrolled_window):
        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
            self.stack.add_named(scrolled_window, self.database_manager.get_group_uuid_from_group_object(self.current_group))
        else:
            self.stack.add_named(scrolled_window, self.database_manager.get_entry_uuid_from_entry_object(self.current_group))

        self.switch_stack_page()

    def switch_stack_page(self):
        page_uuid = NotImplemented

        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
            page_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)
            self.set_browser_headerbar()
        else:
            page_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)
            self.set_entry_page_headerbar()

        if page_uuid in self.scheduled_page_destroy:
            stack_page = self.stack.get_child_by_name(page_uuid)

            if stack_page is not None:
                stack_page.destroy()
                
            self.scheduled_page_destroy.remove(page_uuid)
            self.show_page_of_new_directory(False)

        if self.stack.get_child_by_name(page_uuid) is None:
            self.show_page_of_new_directory(False)
        else:
            self.stack.set_visible_child_name(page_uuid)

    def update_current_stack_page(self):
        stack_page_name = self.database_manager.get_group_uuid_from_group_object(self.current_group)
        stack_page = self.stack.get_child_by_name(stack_page_name)
        stack_page.destroy()
        self.show_page_of_new_directory(False)

    def set_current_group(self, group):
        self.current_group = group

    def get_current_group(self):
        return self.current_group

    def schedule_stack_page_for_destroy(self, page_name):
        self.scheduled_page_destroy.append(page_name)

    def destroy_scheduled_stack_page(self):
        page_uuid = NotImplemented
        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
            page_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)
        else:
            page_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)

        if page_uuid in self.scheduled_page_destroy:
            stack_page_name = self.stack.get_child_by_name(page_uuid)
            if stack_page_name is not None:
                stack_page_name.destroy()
            self.scheduled_page_destroy.remove(page_uuid)

    #
    # Create Group & Entry Rows
    #

    def insert_groups_into_listbox(self, list_box):
        groups = NotImplemented
        sorted_list = []

        if self.current_group.is_root_group:
            groups = self.database_manager.get_groups_in_root()
        else:
            groups = self.database_manager.get_groups_in_folder(self.database_manager.get_group_uuid_from_group_object(self.current_group))

        for group in groups:
            group_row = GroupRow(self, self.database_manager, group)
            sorted_list.append(group_row)
        if self.list_box_sorting == "A-Z":
            sorted_list.sort(key=lambda group: str.lower(group.label), reverse=False)
        elif self.list_box_sorting == "Z-A":
            sorted_list.sort(key=lambda group: str.lower(group.label), reverse=True)

        for group_row in sorted_list:
            list_box.add(group_row)

    def insert_entries_into_listbox(self, list_box):
        entries = self.database_manager.get_entries_in_folder(self.database_manager.get_group_uuid_from_group_object(self.current_group))
        sorted_list = []

        for entry in entries:
            entry_row = EntryRow(self, self.database_manager, entry)
            sorted_list.append(entry_row)

        if self.list_box_sorting == "A-Z":
            sorted_list.sort(key=lambda entry: str.lower(entry.label), reverse=False)
        elif self.list_box_sorting == "Z-A":
            sorted_list.sort(key=lambda entry: str.lower(entry.label), reverse=True)

        for entry_row in sorted_list:
            list_box.add(entry_row)

    def rebuild_all_pages(self):
        for page in self.stack.get_children():
            if page.check_is_edit_page() is False:
                page.destroy()

        self.show_page_of_new_directory(False)
        
    #
    # Create Property Rows
    #

    def insert_entry_properties_into_listbox(self, properties_list_box, add_all):
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)
        scrolled_page = self.stack.get_child_by_name(entry_uuid)

        if self.database_manager.has_entry_name(entry_uuid) is True or add_all is True:
            if scrolled_page.name_property_row is NotImplemented:
                scrolled_page.name_property_row = builder.get_object("name_property_row")
                scrolled_page.name_property_value_entry = builder.get_object("name_property_value_entry")
                value = self.database_manager.get_entry_name_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_name(entry_uuid) is True:
                    scrolled_page.name_property_value_entry.set_text(value)
                else:
                    scrolled_page.name_property_value_entry.set_text("")

                scrolled_page.name_property_value_entry.connect("changed", self.on_property_value_entry_changed, "name")
                properties_list_box.add(scrolled_page.name_property_row)
            elif scrolled_page.name_property_row is not "":
                value = self.database_manager.get_entry_name_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_name(entry_uuid) is True:
                    scrolled_page.name_property_value_entry.set_text(value)
                else:
                    scrolled_page.name_property_value_entry.set_text("")

                scrolled_page.name_property_value_entry.connect("changed", self.on_property_value_entry_changed, "name")
                properties_list_box.add(scrolled_page.name_property_row)

        if self.database_manager.has_entry_username(entry_uuid) is True or add_all is True:
            if scrolled_page.username_property_row is NotImplemented:
                scrolled_page.username_property_row = builder.get_object("username_property_row")
                scrolled_page.username_property_value_entry = builder.get_object("username_property_value_entry")
                value = self.database_manager.get_entry_username_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_username(entry_uuid) is True:
                    scrolled_page.username_property_value_entry.set_text(value)
                else:
                    scrolled_page.username_property_value_entry.set_text("")

                scrolled_page.username_property_value_entry.connect("icon-press", self.on_copy_secondary_button_clicked)
                scrolled_page.username_property_value_entry.connect("changed", self.on_property_value_entry_changed, "username")
                properties_list_box.add(scrolled_page.username_property_row)
            elif scrolled_page.username_property_row is not "":
                value = self.database_manager.get_entry_username_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_username(entry_uuid) is True:
                    scrolled_page.username_property_value_entry.set_text(value)
                else:
                    scrolled_page.username_property_value_entry.set_text("")

                scrolled_page.username_property_value_entry.connect("icon-press", self.on_copy_secondary_button_clicked)
                scrolled_page.username_property_value_entry.connect("changed", self.on_property_value_entry_changed, "username")
                properties_list_box.add(scrolled_page.username_property_row)

        if self.database_manager.has_entry_password(entry_uuid) is True or add_all is True:                
            if scrolled_page.password_property_row is NotImplemented:
                scrolled_page.password_property_row = builder.get_object("password_property_row")
                scrolled_page.password_property_value_entry = builder.get_object("password_property_value_entry")
                scrolled_page.show_password_button = builder.get_object("show_password_button")
                scrolled_page.generate_password_button = builder.get_object("generate_password_button")
                value = self.database_manager.get_entry_password_from_entry_uuid(entry_uuid)

                if self.database_manager.has_entry_password(entry_uuid) is True:
                    scrolled_page.password_property_value_entry.set_text(value)
                else:
                    scrolled_page.password_property_value_entry.set_text("")

                scrolled_page.password_property_value_entry.connect("icon-press", self.on_copy_secondary_button_clicked)
                scrolled_page.password_property_value_entry.connect("changed", self.on_property_value_entry_changed, "password")

                self.change_password_entry_visibility(scrolled_page.password_property_value_entry, scrolled_page.show_password_button)
                self.show_generate_password_popover(scrolled_page.generate_password_button, scrolled_page.password_property_value_entry)

                properties_list_box.add(scrolled_page.password_property_row)
            elif scrolled_page.password_property_row is not "":
                value = self.database_manager.get_entry_password_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_password(entry_uuid) is True:
                    scrolled_page.password_property_value_entry.set_text(value)
                else:
                    scrolled_page.password_property_value_entry.set_text("")

                scrolled_page.password_property_value_entry.connect("icon-press", self.on_copy_secondary_button_clicked)
                scrolled_page.password_property_value_entry.connect("changed", self.on_property_value_entry_changed, "password")
                properties_list_box.add(scrolled_page.password_property_row)

        if self.database_manager.has_entry_url(entry_uuid) is True or add_all is True:
            if scrolled_page.url_property_row is NotImplemented:
                scrolled_page.url_property_row = builder.get_object("url_property_row")
                scrolled_page.url_property_value_entry = builder.get_object("url_property_value_entry")
                value = self.database_manager.get_entry_url_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_url(entry_uuid) is True:
                    scrolled_page.url_property_value_entry.set_text(value)
                else:
                    scrolled_page.url_property_value_entry.set_text("")

                scrolled_page.url_property_value_entry.connect("icon-press", self.on_link_secondary_button_clicked)
                scrolled_page.url_property_value_entry.connect("changed", self.on_property_value_entry_changed, "url")
                properties_list_box.add(scrolled_page.url_property_row)
            elif scrolled_page.url_property_row is not "":
                value = self.database_manager.get_entry_url_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_url(entry_uuid) is True:
                    scrolled_page.url_property_value_entry.set_text(value)
                else:
                    scrolled_page.url_property_value_entry.set_text("")

                scrolled_page.url_property_value_entry.connect("icon-press", self.on_link_secondary_button_clicked)
                scrolled_page.url_property_value_entry.connect("changed", self.on_property_value_entry_changed, "url")
                properties_list_box.add(scrolled_page.url_property_row)

        if self.database_manager.has_entry_notes(entry_uuid) is True or add_all is True:
            if scrolled_page.notes_property_row is NotImplemented:
                scrolled_page.notes_property_row = builder.get_object("notes_property_row")
                scrolled_page.notes_property_value_entry = builder.get_object("notes_property_value_entry")
                value = self.database_manager.get_entry_notes_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_notes(entry_uuid) is True:
                    scrolled_page.notes_property_value_entry.set_text(value)
                else:
                    scrolled_page.notes_property_value_entry.set_text("")
                scrolled_page.notes_property_value_entry.connect("changed", self.on_property_value_entry_changed, "notes")
                properties_list_box.add(scrolled_page.notes_property_row)
            elif scrolled_page.notes_property_row is not "":
                value = self.database_manager.get_entry_notes_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_notes(entry_uuid) is True:
                    scrolled_page.notes_property_value_entry.set_text(value)
                else:
                    scrolled_page.notes_property_value_entry.set_text("")
                scrolled_page.notes_property_value_entry.connect("changed", self.on_property_value_entry_changed, "notes")
                properties_list_box.add(scrolled_page.notes_property_row)

        if scrolled_page.name_property_row is not NotImplemented and scrolled_page.username_property_row is not NotImplemented and scrolled_page.password_property_row is not NotImplemented and scrolled_page.url_property_row is not NotImplemented and scrolled_page.notes_property_row is not NotImplemented:
            scrolled_page.add_button_disabled = True
            self.builder.get_object("add_property_button").set_sensitive(False)

    def insert_group_properties_into_listbox(self, properties_list_box):
        group_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)

        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/group_page.ui")

        name_property_row = builder.get_object("name_property_row")
        name_property_value_entry = builder.get_object("name_property_value_entry")
        name_property_value_entry.connect("changed", self.on_property_value_group_changed, "name")

        notes_property_row = builder.get_object("notes_property_row")
        notes_property_value_entry = builder.get_object("notes_property_value_entry")
        notes_property_value_entry.connect("changed", self.on_property_value_group_changed, "notes")

        name_value = self.database_manager.get_group_name_from_uuid(group_uuid)
        notes_value = self.database_manager.get_group_notes_from_group_uuid(group_uuid)

        if self.database_manager.has_group_name(group_uuid) is True:
            name_property_value_entry.set_text(name_value)
        else:
            name_property_value_entry.set_text("")

        if self.database_manager.has_group_notes(group_uuid) is True:
            notes_property_value_entry.set_text(notes_value)
        else:
            notes_property_value_entry.set_text("")

        properties_list_box.add(name_property_row)
        properties_list_box.add(notes_property_row)

    #
    # Events
    #

    def on_list_box_row_activated(self, widget, list_box_row):
        self.start_database_lock_timer()

        if list_box_row.get_type() == "EntryRow":
            self.set_current_group(self.database_manager.get_entry_object_from_uuid(list_box_row.get_entry_uuid()))
            self.pathbar.add_pathbar_button_to_pathbar(list_box_row.get_entry_uuid())
            self.show_page_of_new_directory(False)
        elif list_box_row.get_type() == "GroupRow":
            self.set_current_group(self.database_manager.get_group_object_from_uuid(list_box_row.get_group_uuid()))
            self.pathbar.add_pathbar_button_to_pathbar(list_box_row.get_group_uuid())
            self.show_page_of_new_directory(False)

    def on_save_button_clicked(self, widget):
        self.start_database_lock_timer()
        self.database_manager.save_database()
        self.show_database_action_revealer("Database saved")

    def on_lock_button_clicked(self, widget):
        if self.database_manager.made_database_changes() is True:
            self.show_save_dialog()
        else:
            self.lock_database()

    def on_save_dialog_save_button_clicked(self, widget, save_dialog):
        self.start_database_lock_timer()
        self.database_manager.save_database()
        save_dialog.destroy()
        self.lock_database()

    def on_save_dialog_discard_button_clicked(self, widget, save_dialog):
        self.start_database_lock_timer()
        save_dialog.destroy()
        self.lock_database()

    def on_add_entry_button_clicked(self, widget):
        self.start_database_lock_timer()
        self.database_manager.changes = True
        entry = self.database_manager.add_entry_to_database("", "", "", "", "", "0", self.database_manager.get_group_uuid_from_group_object(self.current_group))
        self.current_group = entry
        self.pathbar.add_pathbar_button_to_pathbar(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
        self.show_page_of_new_directory(False)

        self.show_database_action_revealer("Added Entry")

    def on_add_group_button_clicked(self, widget):
        self.start_database_lock_timer()
        self.database_manager.changes = True
        group = self.database_manager.add_group_to_database("", "0", "", self.current_group)
        self.current_group = group
        self.pathbar.add_pathbar_button_to_pathbar(self.database_manager.get_group_uuid_from_group_object(self.current_group))
        self.show_page_of_new_directory(True)

        self.show_database_action_revealer("Added Group")

    def on_add_property_button_clicked(self, widget):
        self.start_database_lock_timer()
        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)
        scrolled_page = self.stack.get_child_by_name(entry_uuid)

        for row in scrolled_page.properties_list_box.get_children():
            scrolled_page.properties_list_box.remove(row)

        self.insert_entry_properties_into_listbox(scrolled_page.properties_list_box, True)

    def on_property_value_entry_changed(self, widget, type):
        self.start_database_lock_timer()
        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)

        scrolled_page = self.stack.get_child_by_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
        scrolled_page.set_made_database_changes(True)

        if type == "name":
            self.database_manager.set_entry_name(entry_uuid, widget.get_text())

            pathbar_button = self.pathbar.get_pathbar_button(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
            pathbar_button.set_label(widget.get_text())

        elif type == "username":
            self.database_manager.set_entry_username(entry_uuid, widget.get_text())
        elif type == "password":
            self.database_manager.set_entry_password(entry_uuid, widget.get_text())
        elif type == "url":
            self.database_manager.set_entry_url(entry_uuid, widget.get_text())
        elif type == "notes":
            self.database_manager.set_entry_notes(entry_uuid, widget.get_text())

    def on_property_value_group_changed(self, widget, type):
        self.start_database_lock_timer()
        group_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)

        scrolled_page = self.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(self.current_group))
        scrolled_page.set_made_database_changes(True)

        if type == "name":
            self.database_manager.set_group_name(group_uuid, widget.get_text())

            for pathbar_button in self.pathbar.get_children():
                if pathbar_button.get_name() == "PathbarButtonDynamic":
                    if pathbar_button.get_uuid() == self.database_manager.get_group_uuid_from_group_object(self.current_group):
                        pathbar_button.set_label(widget.get_text())
        elif type == "notes":
            self.database_manager.set_group_notes(group_uuid, widget.get_text())

    def on_entry_row_button_pressed(self, widget, event):
        self.start_database_lock_timer()
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.entry_marked_for_delete = self.database_manager.get_entry_object_from_uuid(widget.get_parent().get_entry_uuid())
            entry_context_popover = self.builder.get_object("entry_context_popover")
            entry_context_popover.set_relative_to(widget)
            entry_context_popover.show_all()
            entry_context_popover.popup()

    def on_entry_delete_menu_button_clicked(self, action, param):
        self.start_database_lock_timer()
        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.entry_marked_for_delete)

        # If the deleted entry is in the pathbar, we need to rebuild the pathbar
        if self.pathbar.is_pathbar_button_in_pathbar(entry_uuid) is True:
            self.pathbar.rebuild_pathbar(self.current_group)

        self.database_manager.delete_entry_from_database(self.entry_marked_for_delete)
        self.update_current_stack_page()

    def on_group_row_button_pressed(self, widget, event):
        self.start_database_lock_timer()
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.group_marked_for_delete = self.database_manager.get_group_object_from_uuid(widget.get_parent().get_group_uuid())
            self.group_marked_for_edit = self.database_manager.get_group_object_from_uuid(widget.get_parent().get_group_uuid())
            group_context_popover = self.builder.get_object("group_context_popover")
            group_context_popover.set_relative_to(widget)
            group_context_popover.show_all()
            group_context_popover.popup()

    def on_group_delete_menu_button_clicked(self, action, param):
        self.start_database_lock_timer()
        group_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.group_marked_for_delete)

        # If the deleted group is in the pathbar, we need to rebuild the pathbar
        if self.pathbar.is_pathbar_button_in_pathbar(group_uuid) is True:
            self.pathbar.rebuild_pathbar(self.current_group)

        self.database_manager.delete_group_from_database(self.group_marked_for_delete)
        self.update_current_stack_page()

    def on_group_edit_menu_button_clicked(self, action, param):
        self.start_database_lock_timer()
        group_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.group_marked_for_edit)

        self.set_current_group(self.group_marked_for_edit)
        self.pathbar.add_pathbar_button_to_pathbar(group_uuid)
        self.show_page_of_new_directory(True)

    def on_show_password_button_toggled(self, toggle_button, entry):
        self.start_database_lock_timer()
        if entry.get_visibility() is True:
            entry.set_visibility(False)
        else:
            entry.set_visibility(True)

    def on_copy_secondary_button_clicked(self, widget, position, eventbutton):
        self.start_database_lock_timer()
        if self.clipboard_timer is not NotImplemented:
            self.clipboard_timer.cancel()

        self.clipboard.set_text(widget.get_text(), -1)
        clear_clipboard_time = keepassgtk.config_manager.get_clear_clipboard()
        self.clipboard_timer = Timer(clear_clipboard_time, self.clear_clipboard)
        self.clipboard_timer.start()

    def on_link_secondary_button_clicked(self, widget, position, eventbutton):
        self.start_database_lock_timer()
        Gtk.show_uri_on_window(self.window, widget.get_text(), Gtk.get_current_event_time())

    def on_popup_generate_password_popover(self, widget, entry):
        self.start_database_lock_timer()
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

        popover = builder.get_object("generate_password_popover")
        digit_spin_button = builder.get_object("digit_spin_button")
        generate_button = builder.get_object("generate_button")

        digit_adjustment = Gtk.Adjustment(16, 5, 50, 1, 5)
        digit_spin_button.set_adjustment(digit_adjustment)

        generate_button.connect("clicked", self.on_generate_button_clicked, builder, entry, digit_spin_button)

        popover.set_relative_to(widget)
        popover.show_all()
        popover.popup()

    def on_generate_button_clicked(self, widget, builder, entry, digit_spin_button):
        self.start_database_lock_timer()
        high_letter_toggle_button = builder.get_object("high_letter_toggle_button")
        low_letter_toggle_button = builder.get_object("low_letter_toggle_button")
        number_toggle_button = builder.get_object("number_toggle_button")
        special_toggle_button = builder.get_object("special_toggle_button")

        digits = digit_spin_button.get_value_as_int()

        password = keepassgtk.password_generator.generate(digits, high_letter_toggle_button.get_active(), low_letter_toggle_button.get_active(), number_toggle_button.get_active(), special_toggle_button.get_active())
        entry.set_text(password)

    def on_database_settings_entry_clicked(self, action, param):
        DatabaseSettingsDialog(self)

    def on_sort_menu_button_entry_clicked(self, action, param, sorting):
        self.start_database_lock_timer()
        keepassgtk.config_manager.set_sort_order(sorting)
        self.list_box_sorting = sorting
        self.rebuild_all_pages()

    def on_headerbar_search_close_button_clicked(self, widget):
        self.remove_search_headerbar(None)
        self.show_page_of_new_directory(False)

    def on_headerbar_search_entry_changed(self, widget, search_local_button, search_fulltext_button):
        fulltext = False
        result_list = []

        for row in self.search_list_box.get_children():
            self.search_list_box.remove(row)

        if search_fulltext_button.get_active() is True:
            fulltext = True

        if search_local_button.get_active() is True:
            result_list = self.database_manager.local_search(self.current_group, widget.get_text(), fulltext)
        else:
            result_list = self.database_manager.global_search(widget.get_text(), fulltext)

        if widget.get_text() is not "":
            for uuid in result_list:
                if self.database_manager.check_is_group(uuid):
                    group_row = GroupRow(self, self.database_manager, self.database_manager.get_group_object_from_uuid(uuid))
                    self.search_list_box.add(group_row)
                else:
                    entry_row = EntryRow(self, self.database_manager, self.database_manager.get_entry_object_from_uuid(uuid))
                    self.search_list_box.add(entry_row)

    def on_headerbar_search_entry_enter_pressed(self, widget):
        if widget.get_text() is not "":
            uuid = NotImplemented
            first_row = NotImplemented

            if self.search_list_box.get_children()[0].type is "GroupRow":
                uuid = self.search_list_box.get_children()[0].get_group_uuid()
                first_row = self.database_manager.get_group_object_from_uuid(uuid)
            else:
                uuid = self.search_list_box.get_children()[0].get_entry_uuid()
                first_row = self.database_manager.get_entry_object_from_uuid(uuid)

            self.current_group = first_row
            self.pathbar.add_pathbar_button_to_pathbar(uuid)
            self.show_page_of_new_directory(False)

    def on_search_filter_button_toggled(self, widget):
        headerbar_search_entry = self.builder.get_object("headerbar_search_entry")
        search_local_button = self.builder.get_object("search_local_button")
        search_fulltext_button = self.builder.get_object("search_fulltext_button")

        self.on_headerbar_search_entry_changed(headerbar_search_entry, search_local_button, search_fulltext_button)

    #
    # Dialog Creator
    #

    def show_save_dialog(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/save_dialog.ui")

        save_dialog = builder.get_object("save_dialog")
        save_dialog.set_destroy_with_parent(True)
        save_dialog.set_modal(True)
        save_dialog.set_transient_for(self.window)

        discard_button = builder.get_object("discard_button")
        save_button = builder.get_object("save_button")

        discard_button.connect("clicked", self.on_save_dialog_discard_button_clicked, save_dialog)
        save_button.connect("clicked", self.on_save_dialog_save_button_clicked, save_dialog)

        save_dialog.present()

    def show_database_action_revealer(self, message):
        database_action_box = self.builder.get_object("database_action_box")
        context = database_action_box.get_style_context()
        context.add_class('NotifyRevealer')

        database_action_label = self.builder.get_object("database_action_label")
        database_action_label.set_text(message)

        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())
        revealer_timer = Timer(3.0, self.hide_database_action_revealer)
        revealer_timer.start()

    def hide_database_action_revealer(self):
        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())

    def lock_database(self):
        self.cancel_timers()
        self.window.opened_databases.remove(self)
        self.window.close_tab(self.parent_widget)
        self.window.start_database_opening_routine(ntpath.basename(self.database_manager.database_path), self.database_manager.database_path)

    #
    # Helper Methods
    #

    def change_password_entry_visibility(self, entry, toggle_button):
        toggle_button.connect("toggled", self.on_show_password_button_toggled, entry)

        if keepassgtk.config_manager.get_show_password_fields() is False:
            entry.set_visibility(False)
        else:
            toggle_button.toggled()
            entry.set_visibility(True)

    def show_generate_password_popover(self, show_password_button, entry):
        show_password_button.connect("clicked", self.on_popup_generate_password_popover, entry)

    def clear_clipboard(self):
        clear_clipboard_time = keepassgtk.config_manager.get_clear_clipboard()
        if clear_clipboard_time is not 0:
            self.clipboard.clear()

    def start_database_lock_timer(self):
        if self.database_lock_timer is not NotImplemented:
            self.database_lock_timer.cancel()
        timeout = keepassgtk.config_manager.get_database_lock_timeout() * 60
        if timeout is not 0:
            self.database_lock_timer = Timer(timeout, self.lock_database)
            self.database_lock_timer.start()   

    def cancel_timers(self):
        if self.clipboard_timer is not NotImplemented:
            self.clipboard_timer.cancel()

        if self.database_lock_timer is not NotImplemented:
            self.database_lock_timer.cancel()
