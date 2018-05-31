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

        add_button = self.builder.get_object("add_button")
        add_button.connect("clicked", self.on_add_button_clicked)

        self.parent_widget.set_headerbar(headerbar)
        self.window.set_titlebar(headerbar)

        self.pathbar = Pathbar(self, self.database_manager, self.database_manager.get_root_group(), headerbar)

    #
    # Group and Entry Management
    #

    def show_page_of_new_directory(self):
        if self.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is None:
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
            self.stack.set_visible_child_name(
                self.database_manager.get_group_uuid_from_group_object(
                    self.current_group))

    def add_stack_page(self, viewport):
        self.stack.add_named(viewport, self.database_manager.get_group_uuid_from_group_object(self.current_group))
        self.switch_stack_page()

    def switch_stack_page(self):
        self.stack.set_visible_child_name(
            self.database_manager.get_group_uuid_from_group_object(
                self.current_group))

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
    # Events
    #

    def on_list_box_row_activated(self, widget, list_box_row):
        if list_box_row.get_type() == "EntryRow":
            self.logging_manager.log_info("Will show details of the entry in near future. Entry clicked: " + list_box_row.get_label())
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

    def on_add_button_clicked(self, widget):
        self.database_manager.changes = True

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
