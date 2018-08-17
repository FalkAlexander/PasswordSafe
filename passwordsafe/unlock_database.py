from gi.repository import Gio, Gtk
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.unlocked_database import UnlockedDatabase
import passwordsafe.config_manager
from passwordsafe.logging_manager import LoggingManager
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
    keyfile_path = NotImplemented
    composite_keyfile_path = NotImplemented
    logging_manager = LoggingManager(True)
    overlay = NotImplemented
    timeout = NotImplemented
    unlocked_database = NotImplemented
    original_group = NotImplemented
    original_group_edit_page = NotImplemented

    def __init__(self, window, widget, filepath):
        self.window = window
        self.parent_widget = widget
        self.database_filepath = filepath
        self.unlock_database()

    def unlock_database(self, timeout=None, unlocked_database=None, original_group=NotImplemented, original_group_edit_page=False):
        self.timeout = timeout
        self.unlocked_database = unlocked_database
        self.original_group = original_group
        self.original_group_edit_page = original_group_edit_page

        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/unlock_database.ui")

        self.set_headerbar()

        self.assemble_stack()

    #
    # Headerbar
    #

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")
        headerbar.set_subtitle(self.database_filepath)

        if self.timeout is True and self.window.container.get_current_page() == self.window.container.page_num(self.parent_widget):
            self.window.set_titlebar(headerbar)
        elif self.timeout is not True:
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

        if passwordsafe.config_manager.get_remember_composite_key() is True and passwordsafe.config_manager.get_last_used_composite_key() is not "":
            keyfile_path = passwordsafe.config_manager.get_last_used_composite_key()
            composite_unlock_select_button = self.builder.get_object("composite_unlock_select_button")
            composite_unlock_select_button.set_label(ntpath.basename(keyfile_path))
            self.composite_keyfile_path = keyfile_path

        if passwordsafe.config_manager.get_remember_unlock_method() is True:
            stack.set_visible_child(stack.get_child_by_name(passwordsafe.config_manager.get_unlock_method() + "_unlock"))

        self.overlay.add(stack)
        self.unlock_database_stack_box.add(self.overlay)
        self.unlock_database_stack_box.show_all()

        self.parent_widget.add(self.unlock_database_stack_box)

        self.connect_events(stack)

    def connect_events(self, stack):
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
        if stack.get_visible_child_name() == "password_unlock":
            password_unlock_entry.grab_focus()
        password_unlock_entry.connect("activate", self.on_password_unlock_button_clicked)
        password_unlock_entry.connect("icon-press", self.on_password_unlock_entry_secondary_clicked)

        composite_unlock_entry = self.builder.get_object("composite_unlock_entry")
        composite_unlock_entry.connect("activate", self.on_composite_unlock_button_clicked)
        if stack.get_visible_child_name() == "composite_unlock":
            composite_unlock_entry.grab_focus()

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
        if self.timeout is True:
            for db in self.window.opened_databases:
                if db.database_manager.database_path == self.database_manager.database_path:
                    self.window.opened_databases.remove(db)
        self.window.set_headerbar()
        self.window.close_tab(self.parent_widget)

    def on_password_unlock_button_clicked(self, widget):
        password_unlock_entry = self.builder.get_object("password_unlock_entry")

        database_already_opened = False

        for db in self.window.opened_databases:
            if db.database_manager.database_path == self.database_filepath and self.timeout is not True:
                database_already_opened = True
                page_num = self.window.container.page_num(db.parent_widget)
                self.window.container.set_current_page(page_num)

                current_page_num = self.window.container.page_num(self.parent_widget)
                self.window.container.remove_page(current_page_num)
                self.window.update_tab_bar_visibility()

                db.show_database_action_revealer("Database already opened")

        if password_unlock_entry.get_text() != "" and database_already_opened is False:
            if self.timeout is True:
                if password_unlock_entry.get_text() == self.unlocked_database.database_manager.password and self.unlocked_database.database_manager.keyfile_hash is NotImplemented:
                    self.parent_widget.remove(self.unlock_database_stack_box)
                    if self.unlocked_database.search is True:
                        self.parent_widget.set_headerbar(self.unlocked_database.headerbar_search)
                        self.window.set_titlebar(self.unlocked_database.headerbar_search)
                    else:
                        self.parent_widget.set_headerbar(self.unlocked_database.headerbar)
                        self.window.set_titlebar(self.unlocked_database.headerbar)

                    self.unlocked_database.overlay.show()
                    if self.original_group is not NotImplemented:
                        self.unlocked_database.current_group = self.original_group
                        if self.original_group_edit_page is True:
                            self.unlocked_database.show_page_of_new_directory(True, False)
                        else:
                            self.unlocked_database.show_page_of_new_directory(False, False)

                    self.unlocked_database.start_database_lock_timer()
                else:
                    self.show_unlock_failed_revealer()
                    password_unlock_entry.grab_focus()
                    password_unlock_entry.get_style_context().add_class("error")
                    self.clear_input_fields()
                    self.logging_manager.log_debug("Could not open database, wrong password")
            else:
                try:
                    self.database_manager = DatabaseManager(self.database_filepath, password_unlock_entry.get_text())
                    self.set_last_used_unlock_method("password")
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

            self.keyfile_path = keyfile_chooser_dialog.get_filename()
            print(self.keyfile_path)

        elif response == Gtk.ResponseType.CANCEL:
            self.logging_manager.log_debug("File selection canceled")
            keyfile_chooser_dialog.close()

    def on_keyfile_unlock_button_clicked(self, widget):
        keyfile_unlock_select_button = self.builder.get_object("keyfile_unlock_select_button")

        if self.timeout is True:
            if self.keyfile_path is not NotImplemented and self.unlocked_database.database_manager.keyfile_hash == self.database_manager.create_keyfile_hash(self.keyfile_path):
                self.parent_widget.remove(self.unlock_database_stack_box)
                self.keyfile_path = NotImplemented
                if self.unlocked_database.search is True:
                    self.parent_widget.set_headerbar(self.unlocked_database.headerbar_search)
                    self.window.set_titlebar(self.unlocked_database.headerbar_search)
                else:
                    self.parent_widget.set_headerbar(self.unlocked_database.headerbar)
                    self.window.set_titlebar(self.unlocked_database.headerbar)

                self.unlocked_database.overlay.show()
                if self.original_group is not NotImplemented:
                    self.unlocked_database.current_group = self.original_group
                    if self.original_group_edit_page is True:
                        self.unlocked_database.show_page_of_new_directory(True, False)
                    else:
                        self.unlocked_database.show_page_of_new_directory(False, False)

                self.unlocked_database.start_database_lock_timer()
            else:
                self.show_unlock_failed_revealer()

                keyfile_unlock_select_button.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
                keyfile_unlock_select_button.set_label("Try again")

                self.logging_manager.log_debug("Invalid keyfile chosen")
        else:
            try:
                self.database_manager = DatabaseManager(self.database_filepath, password=None, keyfile=self.keyfile_path)
                self.database_manager.set_keyfile_hash(self.keyfile_path)
                self.set_last_used_unlock_method("keyfile")
                self.keyfile_path = NotImplemented
                self.open_database_page()
                self.logging_manager.log_debug("Database successfully opened with keyfile")
            except(OSError, IndexError):
                self.show_unlock_failed_revealer()

                if self.database_manager is not NotImplemented:
                        self.database_manager.keyfile_hash = NotImplemented

                keyfile_unlock_select_button.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
                keyfile_unlock_select_button.set_label("Try again")

                self.logging_manager.log_debug("Invalid keyfile chosen")

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

        if self.timeout is True:
            if (self.composite_keyfile_path is not NotImplemented) and (self.unlocked_database.database_manager.keyfile_hash == self.database_manager.create_keyfile_hash(self.composite_keyfile_path)) and (composite_unlock_entry.get_text() == self.unlocked_database.database_manager.password):
                self.parent_widget.remove(self.unlock_database_stack_box)
                if self.unlocked_database.search is True:
                    self.parent_widget.set_headerbar(self.unlocked_database.headerbar_search)
                    self.window.set_titlebar(self.unlocked_database.headerbar_search)
                else:
                    self.parent_widget.set_headerbar(self.unlocked_database.headerbar)
                    self.window.set_titlebar(self.unlocked_database.headerbar)

                self.unlocked_database.overlay.show()

                self.unlocked_database.overlay.show()
                if self.original_group is not NotImplemented:
                    self.unlocked_database.current_group = self.original_group
                    if self.original_group_edit_page is True:
                        self.unlocked_database.show_page_of_new_directory(True, False)
                    else:
                        self.unlocked_database.show_page_of_new_directory(False, False)

                self.unlocked_database.start_database_lock_timer()
            else:
                self.show_unlock_failed_revealer()

                composite_unlock_entry.grab_focus()
                composite_unlock_entry.get_style_context().add_class("error")
                composite_unlock_select_button.get_style_context().remove_class("suggested-action")
                composite_unlock_select_button.get_style_context().add_class("destructive-action")
                self.clear_input_fields()

                self.logging_manager.log_debug("Could not open database, wrong password")
        else:
            if composite_unlock_entry.get_text() is not "":
                try:
                    self.database_manager = DatabaseManager(self.database_filepath, composite_unlock_entry.get_text(), self.composite_keyfile_path)
                    self.database_manager.set_keyfile_hash(self.composite_keyfile_path)

                    if passwordsafe.config_manager.get_remember_composite_key() is True and self.composite_keyfile_path is not NotImplemented:
                            passwordsafe.config_manager.set_last_used_composite_key(self.composite_keyfile_path)

                    self.set_last_used_unlock_method("composite")

                    self.composite_keyfile_path = NotImplemented
                    self.open_database_page()
                    self.logging_manager.log_debug("Opening of database was successfull")
                except(OSError):
                    self.show_unlock_failed_revealer()

                    if self.database_manager is not NotImplemented:
                        self.database_manager.keyfile_hash = NotImplemented

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
        passwordsafe.config_manager.set_last_opened_database(str(self.database_filepath))

        already_added = False
        list = []
        for path in passwordsafe.config_manager.get_last_opened_list():
            list.append(path)
            if path == self.database_filepath:
                already_added = True

        if already_added is False:
            list.append(self.database_filepath)
        else:
            list.sort(key=self.database_filepath.__eq__)

        if len(list) > 10:
            list.pop(0)

        passwordsafe.config_manager.set_last_opened_list(list)

        self.unlock_database_stack_box.destroy()
        UnlockedDatabase(self.window, self.parent_widget, self.database_manager, self)

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

    def set_last_used_unlock_method(self, method):
        if passwordsafe.config_manager.get_remember_unlock_method() is True:
            passwordsafe.config_manager.set_unlock_method(method)
