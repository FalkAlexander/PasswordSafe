from gi.repository import Gtk
from keepassgtk.pathbar_button import PathbarButton
from keepassgtk.logging_manager import LoggingManager
import gi
gi.require_version('Gtk', '3.0')


class Pathbar(Gtk.HBox):
    database_open_gui = NotImplemented
    database_manager = NotImplemented
    path = NotImplemented
    headerbar = NotImplemented
    builder = NotImplemented
    logging_manager = LoggingManager(True)

    pathbar_buttons = []

    def __init__(self, database_open_gui, dbm, path, headerbar):
        Gtk.HBox.__init__(self)
        self.set_name("Pathbar")
        self.database_open_gui = database_open_gui
        self.database_manager = dbm
        self.path = path
        self.headerbar = headerbar

        self.builder = Gtk.Builder()
        self.builder.add_from_resource(
            "/run/terminal/KeepassGtk/unlocked_database.ui")

        self.assemble_pathbar()

    #
    # Build Pathbar
    #

    def assemble_pathbar(self):
        self.first_appearance()
        self.show_all()

        self.headerbar.add(self)

    def first_appearance(self):
        home_button = self.builder.get_object("home_button")
        home_button.connect("clicked", self.on_home_button_clicked)
        self.set_active_style(home_button)
        self.pack_start(home_button, True, True, 0)

        seperator_label = Gtk.Label()
        seperator_label.set_markup("<span color=\"#999999\">/</span>")
        self.pack_end(seperator_label, True, True, 0)

    def add_home_button(self):
        home_button = self.builder.get_object("home_button")
        home_button.connect("clicked", self.on_home_button_clicked)
        self.pack_end(home_button, True, True, 0)

    def add_seperator_label(self):
        seperator_label = Gtk.Label()
        seperator_label.set_markup("<span color=\"#999999\">/</span>")
        self.pack_end(seperator_label, True, True, 0)

    #
    # Pathbar Modifications
    #

    def add_pathbar_button_to_pathbar(self, uuid):
        self.clear_pathbar()

        pathbar_button_active = self.create_pathbar_button(uuid)

        self.remove_active_style()
        self.set_active_style(pathbar_button_active)
        self.pack_end(pathbar_button_active, True, True, 0)

        self.add_seperator_label()
        parent_group = self.database_manager.get_parent_group_from_uuid(uuid)

        while not parent_group.is_root_group:
            self.pack_end(self.create_pathbar_button(
                self.database_manager.get_group_uuid_from_group_object(
                    parent_group)),
                    True, True, 0)
            self.add_seperator_label()
            parent_group = self.database_manager.get_parent_group_from_uuid(
                self.database_manager.get_group_uuid_from_group_object(
                    parent_group))

        self.add_home_button()
        self.show_all()

    def create_pathbar_button(self, uuid):
        pathbar_button = PathbarButton(uuid)
        pathbar_button.set_label(
            self.database_manager.get_group_name_from_uuid(uuid))
        pathbar_button.set_relief(Gtk.ReliefStyle.NONE)
        pathbar_button.activate()
        pathbar_button.connect("clicked", self.on_pathbar_button_clicked)

        return pathbar_button

    def clear_pathbar(self):
        self.remove_active_style()
        for widget in self.get_children():
            self.remove(widget)

    def set_active_style(self, pathbar_button):
        context = pathbar_button.get_style_context()
        context.add_class('PathbarButtonActive')

    def remove_active_style(self):
        for pathbar_button in self.get_children():
            context = pathbar_button.get_style_context()
            context.remove_class('PathbarButtonActive')

    #
    # Events
    #

    def on_home_button_clicked(self, widget):
        self.remove_active_style()
        self.set_active_style(widget)

        self.database_open_gui.set_current_group(
            self.database_manager.get_root_group())
        self.database_open_gui.switch_stack_page()

    def on_pathbar_button_clicked(self, pathbar_button):
        if pathbar_button.get_is_group():
            self.remove_active_style()
            self.set_active_style(pathbar_button)
            self.database_open_gui.set_current_group(
                self.database_manager.get_group_object_from_uuid(
                    pathbar_button.get_uuid()))
            self.database_open_gui.switch_stack_page()
        else:
            self.logging_manager.log_info("Functionality of showing details about entries when clicked still to be implemented")
