import gi
import ntpath
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
from keepassgtk.database import KeepassLoader
from keepassgtk.database_open_gui import DatabaseOpenGui
import keepassgtk.config_manager
from keepassgtk.logging_manager import LoggingManager

class DatabaseOpeningGui:
    builder = NotImplemented
    parent_widget = NotImplemented
    window = NotImplemented
    switched = False
    database_filepath = NotImplemented
    keepass_loader = NotImplemented
    keyfile = NotImplemented
    composite = False
    composite_keyfile_path = NotImplemented

    def __init__(self, window, widget, filepath):
        self.window = window
        self.parent_widget = widget
        self.database_filepath = filepath
        self.unlock_database()
        self.logging_manager = LoggingManager(True)

    #
    # Stack Pages
    #
 
    def unlock_database(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/run/terminal/KeepassGtk/unlock_database.ui")

        self.set_headerbar()

        #self.parent_widget.add(self.stack)

        self.assemble_stack()

    def assemble_stack(self):
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        unlock_database_stack_box = self.builder.get_object("unlock_database_stack_box")
        unlock_database_stack_switcher = self.builder.get_object("unlock_database_stack_switcher")
        unlock_database_stack_switcher.set_stack(self.stack)

        password_unlock_stack_page = self.builder.get_object("password_unlock_stack_page")
        keyfile_unlock_stack_page = self.builder.get_object("keyfile_unlock_stack_page")
        composite_unlock_stack_page = self.builder.get_object("composite_unlock_stack_page")

        self.stack.add_titled(password_unlock_stack_page, "password_unlock", "Password")
        self.stack.child_set_property(password_unlock_stack_page, "icon-name", "input-dialpad-symbolic")

        self.stack.add_titled(keyfile_unlock_stack_page, "keyfile_unlock", "Keyfile")
        self.stack.child_set_property(keyfile_unlock_stack_page, "icon-name", "mail-attachment-symbolic")

        self.stack.add_titled(composite_unlock_stack_page, "composite_unlock", "Composite")
        self.stack.child_set_property(composite_unlock_stack_page, "icon-name", "insert-link-symbolic")

        unlock_database_stack_box.add(self.stack)
        unlock_database_stack_box.show_all()

        self.parent_widget.add(unlock_database_stack_box)
    
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
    # Events
    #

    def on_unlock_input_secondary_clicked(self, widget, position, eventbutton):
        if widget.get_visibility():
            widget.set_invisible_char("●")
            widget.set_visibility(False)
        else:
            widget.set_visibility(True)

    def on_headerbar_back_button_clicked(self, widget):
        self.window.close_tab(self.parent_widget)
        self.window.set_headerbar()

    def on_switch_to_keyfile_button_clicked(self, widget):
        self.stack.set_visible_child(self.stack.get_child_by_name("page1"))

    def on_switch_to_password_button_clicked(self, widget):
        self.stack.set_visible_child(self.stack.get_child_by_name("page0"))

    def on_switch_to_composite_button_clicked(self, widget):
        self.stack.set_visible_child(self.stack.get_child_by_name("page3"))

    def on_unlock_database_button_clicked(self, widget):
        password_unlock_input = self.builder.get_object("password_unlock_input")

        if password_unlock_input.get_text() != "":
            try:
                self.keepass_loader = KeepassLoader(self.database_filepath, password_unlock_input.get_text())
                #self.keepass_loader = KeepassLoader(self.database_filepath, password_unlock_input.get_text(), self.composite_keyfile_path)

                self.open_database_page()

                self.logging_manager.log_debug("Opening of database was successfull")

            #OSError:master key invalid
            except(OSError): 
                password_unlock_input.grab_focus()
                password_unlock_input.get_style_context().add_class("error")
                self.clear_input_fields()

                self.logging_manager.log_debug("Could not open database, wrong password")


    def on_keyfile_open_button_clicked(self, widget):
        self.logging_manager.log_debug("Opening keyfile chooser dialog")

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

            keyfile_path = keyfile_chooser_dialog.get_filename()
            self.stack.set_visible_child(self.stack.get_child_by_name("page2"))
            keyfile_name = self.builder.get_object("keyfile_name")
            keyfile_name.set_text(keyfile_path)
            
        elif response == Gtk.ResponseType.CANCEL:
            self.logging_manager.log_debug("File selection canceled")
            keyfile_chooser_dialog.close()


    def on_keyfile_unlock_button_clicked(self, widget):
        keyfile_name = self.builder.get_object("keyfile_name")
        keyfile_path = keyfile_name.get_text()
        keyfile_open_button = self.builder.get_object("keyfile_open_button")
        try:
            self.keepass_loader = KeepassLoader(self.database_filepath, password=None, keyfile=keyfile_path)
            self.open_database_page()
            self.logging_manager.log_debug("Database successfully with keyfile opened")

        except(OSError):
            self.stack.set_visible_child(self.stack.get_child_by_name("page1"))
            keyfile_open_button.get_style_context().add_class(Gtk.STYLE_CLASS_DpESTRUCTIVE_ACTION)
            keyfile_open_button.set_label("Try again")
            
            self.logging_manager.log_debug("Invalid keyfile chosen")
            self.logging_manager.log_debug("Keyfile path: " + keyfile_path)


    def on_composite_keyfile_button_clicked(self, widget):
        filechooser_opening_dialog = Gtk.FileChooserDialog(
            "Choose Keyfile", self.window, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN,
             Gtk.ResponseType.OK))
        composite_keyfile_button = self.builder.get_object("composite_keyfile_button")

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
            composite_keyfile_button.set_label(ntpath.basename(file_path))

            self.composite_keyfile_path = file_path
        elif response == Gtk.ResponseType.CANCEL:
            self.logging_manager.log_debug("File selection cancelled")
            filechooser_opening_dialog.close()


    def on_composite_unlock_button_clicked(self, widget):
        composite_password = self.builder.get_object("composite_password")
        composite_keyfile_button = self.builder.get_object("composite_keyfile_button")

        if composite_password.get_text() != "":
            try:
                self.keepass_loader = KeepassLoader(self.database_filepath, composite_password.get_text(), self.composite_keyfile_path)

                self.open_database_page()

                self.logging_manager.log_debug("Opening of database was successfull")

            #OSError:master key invalid
            except(OSError): 
                composite_password.grab_focus()
                composite_password.get_style_context().add_class("error")
                composite_keyfile_button.get_style_context().remove_class("suggested-action")
                composite_keyfile_button.get_style_context().add_class("destructive-action")
                self.clear_input_fields()

                self.logging_manager.log_debug("Could not open database, wrong password")
        else:
            composite_password.get_style_context().add_class("error")


    #
    # Open Database
    #
    def open_database_page(self):
        self.clear_input_fields()
        self.parent_widget.remove(self.stack)

        keepassgtk.config_manager.create_config_entry_string("history", "last-opened-db", str(self.database_filepath))
        keepassgtk.config_manager.save_config()
            
        DatabaseOpenGui(self.window, self.parent_widget, self.keepass_loader)

    #
    # Helper Functions
    #

    def clear_input_fields(self):
        password_unlock_input = self.builder.get_object("password_unlock_input")
        composite_password = self.builder.get_object("composite_password")
        password_unlock_input.set_text("")
        composite_password.set_text("")
