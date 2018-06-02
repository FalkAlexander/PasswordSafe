from gi.repository import Gtk
from keepassgtk.logging_manager import LoggingManager
from keepassgtk.pathbar import Pathbar
from keepassgtk.entry_row import EntryRow
from keepassgtk.group_row import GroupRow
import gi
import ntpath
import threading
gi.require_version('Gtk', '3.0')


class UnlockedDatabase:
    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    scrolled_window = NotImplemented
    stack = NotImplemented
    database_manager = NotImplemented
    logging_manager = LoggingManager(True)
    current_group = NotImplemented
    pathbar = NotImplemented
    overlay = NotImplemented
    properties_list_box = NotImplemented

    mod_box = NotImplemented
    add_entry_button = NotImplemented
    add_folder_button = NotImplemented
    add_property_button = NotImplemented

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

        self.overlay = Gtk.Overlay()
        self.parent_widget.add(self.overlay)

        database_action_overlay = self.builder.get_object("database_action_overlay")

        self.overlay.add_overlay(database_action_overlay)

        self.current_group = self.database_manager.get_root_group()

        self.stack = self.builder.get_object("list_stack")
        self.overlay.add(self.stack)
        self.overlay.show_all()

        self.set_headerbar()

        self.show_page_of_new_directory()

    #
    # Headerbar
    #

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")

        save_button = self.builder.get_object("save_button")
        save_button.connect("clicked", self.on_save_button_clicked)

        lock_button = self.builder.get_object("lock_button")
        lock_button.connect("clicked", self.on_lock_button_clicked)

        self.mod_box = self.builder.get_object("mod_box")

        self.add_entry_button = self.builder.get_object("add_entry_button")
        self.add_entry_button.connect("clicked", self.on_add_entry_button_clicked)
        self.mod_box.add(self.add_entry_button)

        self.add_folder_button = self.builder.get_object("add_folder_button")
        self.add_folder_button.connect("clicked", self.on_add_folder_button_clicked)
        self.mod_box.add(self.add_folder_button)

        self.add_property_button = self.builder.get_object("add_property_button")
        self.add_property_button.connect("clicked", self.on_add_property_button_clicked)

        self.parent_widget.set_headerbar(headerbar)
        self.window.set_titlebar(headerbar)

        self.pathbar = Pathbar(self, self.database_manager, self.database_manager.get_root_group(), headerbar)

    def set_entry_page_headerbar(self):
        self.mod_box.remove(self.add_entry_button)
        self.mod_box.remove(self.add_folder_button)

        self.add_property_button.set_sensitive(True)

        self.mod_box.add(self.add_property_button)

    def remove_entry_page_headerbar(self):
        self.mod_box.remove(self.add_property_button)

        if self.add_entry_button not in self.mod_box.get_children() and self.add_folder_button not in self.mod_box.get_children():
            self.mod_box.add(self.add_entry_button)
            self.mod_box.add(self.add_folder_button)

    #
    # Group and Entry Management
    #

    def show_page_of_new_directory(self):
        if self.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is None and self.stack.get_child_by_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group)) is None:
            if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
                builder = Gtk.Builder()
                builder.add_from_resource("/run/terminal/KeepassGtk/unlocked_database.ui")
                list_box = builder.get_object("list_box")
                list_box.connect("row-activated", self.on_list_box_row_activated)
                list_box.connect("row-selected", self.on_list_box_row_selected)

                scrolled_window = builder.get_object("scrolled_window")
                viewport = Gtk.Viewport()
                viewport.add(list_box)
                scrolled_window.add(viewport)
                scrolled_window.show_all()

                self.add_stack_page(scrolled_window)
                self.insert_groups_into_listbox(list_box)
                self.insert_entries_into_listbox(list_box)
            else:
                builder = Gtk.Builder()
                builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")
                self.properties_list_box = builder.get_object("properties_list_box")

                scrolled_window = builder.get_object("scrolled_window")
                viewport = Gtk.Viewport()
                viewport.add(self.properties_list_box)
                scrolled_window.add(viewport)
                scrolled_window.show_all()

                self.add_stack_page(scrolled_window)
                self.insert_properties_into_listbox(self.properties_list_box, False)
        else:
            if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
                self.stack.set_visible_child_name(self.database_manager.get_group_uuid_from_group_object(self.current_group))
                self.remove_entry_page_headerbar()
            else:
                self.stack.set_visible_child_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
                self.set_entry_page_headerbar()

    def add_stack_page(self, viewport):
        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
            self.stack.add_named(viewport, self.database_manager.get_group_uuid_from_group_object(self.current_group))
        else:
            self.stack.add_named(viewport, self.database_manager.get_entry_uuid_from_entry_object(self.current_group))

        self.switch_stack_page()

    def switch_stack_page(self):
        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
            self.stack.set_visible_child_name(self.database_manager.get_group_uuid_from_group_object(self.current_group))
            self.remove_entry_page_headerbar()
        else:
            self.stack.set_visible_child_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
            self.set_entry_page_headerbar()

    def set_current_group(self, group):
        self.current_group = group

    def get_current_group(self):
        return self.current_group

    #
    # Create Group & Entry Rows
    #

    def insert_groups_into_listbox(self, list_box):
        groups = NotImplemented

        if self.current_group.is_root_group:
            groups = self.database_manager.get_groups_in_root()
        else:
            groups = self.database_manager.get_groups_in_folder(self.database_manager.get_group_uuid_from_group_object(self.current_group))

        for group in groups:
            group_row = GroupRow(self.database_manager, group)
            list_box.add(group_row)

    def insert_entries_into_listbox(self, list_box):
        entries = self.database_manager.get_entries_in_folder(self.database_manager.get_group_uuid_from_group_object(self.current_group))

        for entry in entries:
            entry_row = EntryRow(self.database_manager, entry)
            list_box.add(entry_row)

    #
    # Create Property Entries
    #

    def insert_properties_into_listbox(self, properties_list_box, add_all):
        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)

        if self.database_manager.has_entry_name(entry_uuid) is True or add_all is True:
            builder = Gtk.Builder()
            builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

            name_property_row = builder.get_object("name_property_row")
            name_property_value_entry = builder.get_object("name_property_value_entry")

            value = self.database_manager.get_entry_name_from_entry_uuid(entry_uuid)

            if self.database_manager.has_entry_name(entry_uuid) is True:
                name_property_value_entry.set_text(value)
            else:
                name_property_value_entry.set_text("")

            name_property_value_entry.connect("changed", self.on_property_value_entry_changed, "name")

            properties_list_box.add(name_property_row)

        if self.database_manager.has_entry_username(entry_uuid) is True or add_all is True:
            builder = Gtk.Builder()
            builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

            username_property_row = builder.get_object("username_property_row")
            username_property_value_entry = builder.get_object("username_property_value_entry")

            value = self.database_manager.get_entry_username_from_entry_uuid(entry_uuid)

            if self.database_manager.has_entry_username(entry_uuid) is True:
                username_property_value_entry.set_text(value)
            else:
                username_property_value_entry.set_text("")

            username_property_value_entry.connect("changed", self.on_property_value_entry_changed, "username")

            properties_list_box.add(username_property_row)

        if self.database_manager.has_entry_password(entry_uuid) is True or add_all is True:
            builder = Gtk.Builder()
            builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

            password_property_row = builder.get_object("password_property_row")
            password_property_value_entry = builder.get_object("password_property_value_entry")

            value = self.database_manager.get_entry_password_from_entry_uuid(entry_uuid)

            if self.database_manager.has_entry_password(entry_uuid) is True:
                password_property_value_entry.set_text(value)
            else:
                password_property_value_entry.set_text("")

            password_property_value_entry.connect("changed", self.on_property_value_entry_changed, "password")

            properties_list_box.add(password_property_row)

        if self.database_manager.has_entry_url(entry_uuid) is True or add_all is True:
            builder = Gtk.Builder()
            builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

            url_property_row = builder.get_object("url_property_row")
            url_property_value_entry = builder.get_object("url_property_value_entry")

            value = self.database_manager.get_entry_url_from_entry_uuid(entry_uuid)

            if self.database_manager.has_entry_url(entry_uuid) is True:
                url_property_value_entry.set_text(value)
            else:
                url_property_value_entry.set_text("")

            url_property_value_entry.connect("changed", self.on_property_value_entry_changed, "url")

            properties_list_box.add(url_property_row)

        if self.database_manager.has_entry_notes(entry_uuid) is True or add_all is True:
            builder = Gtk.Builder()
            builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

            notes_property_row = builder.get_object("notes_property_row")
            notes_property_value_entry = builder.get_object("notes_property_value_entry")

            value = self.database_manager.get_entry_notes_from_entry_uuid(entry_uuid)

            if self.database_manager.has_entry_notes(entry_uuid) is True:
                notes_property_value_entry.set_text(value)
            else:
                notes_property_value_entry.set_text("")

            notes_property_value_entry.connect("changed", self.on_property_value_entry_changed, "notes")

            properties_list_box.add(notes_property_row)

    #
    # Events
    #

    def on_list_box_row_activated(self, widget, list_box_row):
        if list_box_row.get_type() == "EntryRow":
            self.set_current_group(self.database_manager.get_entry_object_from_uuid(list_box_row.get_entry_uuid()))
            self.pathbar.add_pathbar_button_to_pathbar(list_box_row.get_entry_uuid())
            self.show_page_of_new_directory()
        elif list_box_row.get_type() == "GroupRow":
            self.set_current_group(self.database_manager.get_group_object_from_uuid(list_box_row.get_group_uuid()))
            self.pathbar.add_pathbar_button_to_pathbar(list_box_row.get_group_uuid())
            self.show_page_of_new_directory()

    def on_list_box_row_selected(self, widget, list_box_row):
        self.logging_manager.log_debug(list_box_row.get_label() + " selected")

    def on_save_button_clicked(self, widget):
        self.database_manager.save_database()
        self.show_database_action_revealer("Database saved")

    def on_lock_button_clicked(self, widget):
        if self.database_manager.made_database_changes is True:
            self.show_save_dialog()
        else:
            self.lock_database()

    def on_save_dialog_save_button_clicked(self, widget, save_dialog):
        self.database_manager.save_database()
        save_dialog.destroy()

    def on_save_dialog_discard_button_clicked(self, widget, save_dialog):
        save_dialog.destroy()

    def on_add_entry_button_clicked(self, widget):
        self.database_manager.changes = True
        self.show_database_action_revealer("Testing only")

    def on_add_folder_button_clicked(self, widget):
        self.database_manager.changes = True
        self.show_database_action_revealer("Testing only")

    def on_add_property_button_clicked(self, widget):
        for row in self.properties_list_box.get_children():
            self.properties_list_box.remove(row)

        self.insert_properties_into_listbox(self.properties_list_box, True)

    def on_property_value_entry_changed(self, widget, type):
        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)

        if type == "name":
            self.database_manager.set_entry_name(entry_uuid, widget.get_text())

            for pathbar_button in self.pathbar.get_children():
                if pathbar_button.get_name() == "PathbarButtonDynamic":
                    if pathbar_button.get_uuid() == self.database_manager.get_entry_uuid_from_entry_object(self.current_group):
                        print("ja")
                        pathbar_button.set_label(widget.get_text())

        elif type == "username":
            self.database_manager.set_entry_username(entry_uuid, widget.get_text())
        elif type == "password":
            self.database_manager.set_entry_password(entry_uuid, widget.get_text())
        elif type == "url":
            self.database_manager.set_entry_url(entry_uuid, widget.get_text())
        elif type == "notes":
            self.database_manager.set_entry_notes(entry_uuid, widget.get_text())

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
        revealer_timer = threading.Timer(3.0, self.hide_database_action_revealer)
        revealer_timer.start()

    def hide_database_action_revealer(self):
        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())

    def lock_database(self):
        self.window.opened_databases.remove(self)
        self.window.close_tab(self.parent_widget)
        self.window.start_database_opening_routine(ntpath.basename(self.database_manager.database_path), self.database_manager.database_path)
