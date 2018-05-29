from gi.repository import Gio, Gtk
from keepassgtk.database_manager import DatabaseManager
from keepassgtk.unlocked_database import UnlockedDatabase
import keepassgtk.config_manager
from keepassgtk.logging_manager import LoggingManager
import gi
gi.require_version('Gtk', '3.0')
import ntpath
import threading


class UnlockDatabase:
    builder = NotImplemented
    parent_widget = NotImplemented
    window = NotImplemented
    database_filepath = NotImplemented
    database_manager = NotImplemented
    unlock_database_stack_box = NotImplemented
    keyfile = NotImplemented
    composite_keyfile_path = NotImplemented
    logging_manager = LoggingManager(True)
    overlay = NotImplemented

    def __init__(self, window, widget, filepath):
        self.window = window
        self.parent_widget = widget
        self.database_filepath = filepath
        self.unlock_database()

    def unlock_database(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/run/terminal/KeepassGtk/unlock_database.ui")

        self.set_headerbar()

        self.assemble_stack()
        self.connect_events()

    #
    # Headerbar
    #

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")
        headerbar.set_subtitle(self.database_filepath)
        self.window.set_titlebar(headerbar)
        self.parent_widget.set_headerbar(headerbar)
        back_button = self.builder.get_object("back_button")
        back_button.connect("clicked", self.on_headerbar_back_button_clicked)

    #
    # Stack
    #

    def assemble_stack(self):
        self.overlay = Gtk.Overlay()

        unlock_failed_overlay = self.builder.get_object("unlock_failed_overlay")
        self.overlay.add_overlay(unlock_failed_overlay)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.unlock_database_stack_box = self.builder.get_object("unlock_database_stack_box")
        unlock_database_stack_switcher = self.builder.get_object("unlock_database_stack_switcher")
        unlock_database_stack_switcher.set_stack(stack)

        password_unlock_stack_page = self.builder.get_object("password_unlock_stack_page")
        keyfile_unlock_stack_page = self.builder.get_object("keyfile_unlock_stack_page")
        composite_unlock_stack_page = self.builder.get_object("composite_unlock_stack_page")

        stack.add_titled(password_unlock_stack_page, "password_unlock", "Password")
        stack.child_set_property(password_unlock_stack_page, "icon-name", "input-dialpad-symbolic")

        stack.add_titled(keyfile_unlock_stack_page, "keyfile_unlock", "Keyfile")
        stack.child_set_property(keyfile_unlock_stack_page, "icon-name", "mail-attachment-symbolic")

        stack.add_titled(composite_unlock_stack_page, "composite_unlock", "Composite")
        stack.child_set_property(composite_unlock_stack_page, "icon-name", "insert-link-symbolic")

        self.overlay.add(stack)
        self.unlock_database_stack_box.add(self.overlay)
        self.unlock_database_stack_box.show_all()

        self.parent_widget.add(self.unlock_database_stack_box)

    def connect_events(self):
        password_unlock_button = self.builder.get_object("password_unlock_button")
        password_unlock_button.connect("clicked", self.on_password_unlock_button_clicked)

        keyfile_unlock_button = self.builder.get_object("keyfile_unlock_button")
        keyfile_unlock_button.connect("clicked", self.on_keyfile_unlock_button_clicked)

        composite_unlock_button = self.builder.get_object("composite_unlock_button")
        composite_unlock_button.connect("clicked", self.on_composite_unlock_button_clicked)

        keyfile_unlock_select_button = self.builder.get_object("keyfile_unlock_select_button")
        keyfile_unlock_select_button.connect("clicked", self.on_keyfile_unlock_select_button_clicked)

        composite_unlock_select_button = self.builder.get_object("composite_unlock_select_button")
        composite_unlock_select_button.connect("clicked", self.on_composite_unlock_select_button_clicked)

        password_unlock_entry = self.builder.get_object("password_unlock_entry")
        password_unlock_entry.connect("activate", self.on_password_unlock_button_clicked)
        password_unlock_entry.connect("icon-press", self.on_password_unlock_entry_secondary_clicked)

    #
    # Events
    #

    def on_password_unlock_entry_secondary_clicked(self, widget, position, eventbutton):
        if widget.get_visibility():
            widget.set_invisible_char("●")
            widget.set_visibility(False)
        else:
            widget.set_visibility(True)

    def on_headerbar_back_button_clicked(self, widget):
        self.window.set_headerbar()
        self.window.close_tab(self.parent_widget)

    def on_password_unlock_button_clicked(self, widget):
        password_unlock_entry = self.builder.get_object("password_unlock_entry")

        if password_unlock_entry.get_text() != "":
            try:
                self.database_manager = DatabaseManager(self.database_filepath, password_unlock_entry.get_text())
                self.open_database_page()
                self.logging_manager.log_debug("Opening of database was successfull")
            except(OSError):
                self.show_unlock_failed_revealer()

                password_unlock_entry.grab_focus()
                password_unlock_entry.get_style_context().add_class("error")
                self.clear_input_fields()
                self.logging_manager.log_debug("Could not open database, wrong password")

    def on_keyfile_unlock_select_button_clicked(self, widget):
        keyfile_chooser_dialog = Gtk.FileChooserDialog("Choose a keyfile", self.window, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Keyfile")
        filter_text.add_mime_type("application/octet-stream")
        filter_text.add_mime_type("application/x-keepass2")
        filter_text.add_mime_type("text/plain")
        filter_text.add_mime_type("application/x-iwork-keynote-sffkey")
        keyfile_chooser_dialog.add_filter(filter_text)

        response = keyfile_chooser_dialog.run()
        if response == Gtk.ResponseType.OK:
            self.logging_manager.log_debug("File selected: " + keyfile_chooser_dialog.get_filename())
            keyfile_chooser_dialog.close()

            keyfile_unlock_select_button = self.builder.get_object("keyfile_unlock_select_button")
            keyfile_unlock_select_button.get_style_context().remove_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
            keyfile_unlock_select_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
            keyfile_unlock_select_button.set_label(ntpath.basename(keyfile_chooser_dialog.get_filename()))

        elif response == Gtk.ResponseType.CANCEL:
            self.logging_manager.log_debug("File selection canceled")
            keyfile_chooser_dialog.close()

    def on_keyfile_unlock_button_clicked(self, widget):
        keyfile_unlock_select_button = self.builder.get_object("keyfile_unlock_select_button")
        keyfile_path = keyfile_unlock_select_button.get_label()

        try:
            self.database_manager = DatabaseManager(self.database_filepath, password=None, keyfile=keyfile_path)
            self.open_database_page()
            self.logging_manager.log_debug("Database successfully opened with keyfile")
        except(OSError, IndexError):
            self.show_unlock_failed_revealer()

            keyfile_unlock_select_button.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
            keyfile_unlock_select_button.set_label("Try again")

            self.logging_manager.log_debug("Invalid keyfile chosen")
            self.logging_manager.log_debug("Keyfile path: " + keyfile_path)

    def on_composite_unlock_select_button_clicked(self, widget):
        filechooser_opening_dialog = Gtk.FileChooserDialog(
            "Choose Keyfile", self.window, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN,
             Gtk.ResponseType.OK))
        composite_unlock_select_button = self.builder.get_object("composite_unlock_select_button")

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Keyfile")
        filter_text.add_mime_type("application/octet-stream")
        filter_text.add_mime_type("application/x-keepass2")
        filter_text.add_mime_type("text/plain")
        filter_text.add_mime_type("application/x-iwork-keynote-sffkey")
        filechooser_opening_dialog.add_filter(filter_text)

        response = filechooser_opening_dialog.run()
        if response == Gtk.ResponseType.OK:
            self.logging_manager.log_debug("File selected: " + filechooser_opening_dialog.get_filename())
            filechooser_opening_dialog.close()
            file_path = filechooser_opening_dialog.get_filename()
            composite_unlock_select_button.set_label(ntpath.basename(file_path))
            self.composite_keyfile_path = file_path
        elif response == Gtk.ResponseType.CANCEL:
            self.logging_manager.log_debug("File selection cancelled")
            filechooser_opening_dialog.close()

    def on_composite_unlock_button_clicked(self, widget):
        composite_unlock_entry = self.builder.get_object("composite_unlock_entry")
        composite_unlock_select_button = self.builder.get_object("composite_unlock_select_button")

        if composite_unlock_entry.get_text() is not "":
            try:
                self.database_manager = DatabaseManager(self.database_filepath, composite_unlock_entry.get_text(), self.composite_keyfile_path)
                self.open_database_page()
                self.logging_manager.log_debug("Opening of database was successfull")
            except(OSError):
                self.show_unlock_failed_revealer()

                composite_unlock_entry.grab_focus()
                composite_unlock_entry.get_style_context().add_class("error")
                composite_unlock_select_button.get_style_context().remove_class("suggested-action")
                composite_unlock_select_button.get_style_context().add_class("destructive-action")
                self.clear_input_fields()

                self.logging_manager.log_debug("Could not open database, wrong password")
        else:
            composite_unlock_entry.get_style_context().add_class("error")

    #
    # Open Database
    #
    def open_database_page(self):
        self.clear_input_fields()
        keepassgtk.config_manager.create_config_entry_string("history", "last-opened-db", str(self.database_filepath))
        keepassgtk.config_manager.save_config()

        self.unlock_database_stack_box.destroy()
        UnlockedDatabase(self.window, self.parent_widget, self.database_manager)

    #
    # Helper Functions
    #

    def clear_input_fields(self):
        password_unlock_entry = self.builder.get_object("password_unlock_entry")
        composite_unlock_entry = self.builder.get_object("composite_unlock_entry")
        password_unlock_entry.set_text("")
        composite_unlock_entry.set_text("")

    def show_unlock_failed_revealer(self):
        unlock_failed_box = self.builder.get_object("unlock_failed_box")
        context = unlock_failed_box.get_style_context()
        context.add_class('NotifyRevealer')

        unlock_failed_revealer = self.builder.get_object("unlock_failed_revealer")
        unlock_failed_revealer.set_reveal_child(not unlock_failed_revealer.get_reveal_child())
        revealer_timer = threading.Timer(3.0, self.hide_unlock_failed_revealer)
        revealer_timer.start()

    def hide_unlock_failed_revealer(self):
        unlock_failed_revealer = self.builder.get_object("unlock_failed_revealer")
        unlock_failed_revealer.set_reveal_child(not unlock_failed_revealer.get_reveal_child())
