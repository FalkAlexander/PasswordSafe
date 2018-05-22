import pathbar_button
from pathbar_button import PathbarButton
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Pathbar(Gtk.HBox):
    database_open_gui = NotImplemented
    keepass_loader = NotImplemented
    path = NotImplemented
    headerbar = NotImplemented
    builder = NotImplemented

    pathbar_buttons = []

    def __init__(self, database_open_gui, keepass_loader, path, headerbar):
        Gtk.HBox.__init__(self)
        self.set_name("Pathbar")
        self.database_open_gui = database_open_gui
        self.keepass_loader = keepass_loader
        self.path = path
        self.headerbar = headerbar

        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/entries_listbox.ui")

        self.assemble_pathbar()

    #
    # Build Pathbar
    #

    def assemble_pathbar(self):
        self.add_home_button()
        self.add(self.get_seperator_label())
        self.show_all()

        self.headerbar.add(self)

    def add_home_button(self):
        home_button = self.builder.get_object("home_button")
        home_button.connect("clicked", self.on_home_button_clicked)
        self.add(home_button)

    def get_seperator_label(self):
        seperator_label = Gtk.Label()
        seperator_label.set_markup("<span color=\"#999999\">/</span>")
        return seperator_label

    #
    # Pathbar Modifications
    #

    def add_pathbar_button_to_pathbar(self, uuid):
        self.pack_end(self.get_seperator_label(), True, True, 0)
        self.pack_end(self.create_pathbar_button(uuid), True, True, 0)
        self.show_all()

    def create_pathbar_button(self, uuid):
        pathbar_button = PathbarButton(uuid)
        pathbar_button.set_label(self.keepass_loader.get_group_name_from_uuid(uuid))
        pathbar_button.set_relief(Gtk.ReliefStyle.NONE)
        pathbar_button.connect("clicked", self.on_pathbar_button_clicked)

        self.pathbar_buttons.append(pathbar_button)

        return pathbar_button

    #
    # Events
    #

    def on_home_button_clicked(self, widget):
        #self.database_open_gui.stack.remove(self.keepass_loader.get_group_uuid_from_group_object(self.database_open_gui.current_group))
        self.database_open_gui.set_current_group(self.keepass_loader.get_root_group())
        self.database_open_gui.switch_stack_page()

    def on_pathbar_button_clicked(self, pathbar_button):
        if pathbar_button.get_is_group():
            self.database_open_gui.set_current_group(self.keepass_loader.get_group_object_from_uuid(pathbar_button.get_uuid()))
            self.database_open_gui.switch_stack_page()
        else:
            print("Entry pathbar button clicked, do nothing")
