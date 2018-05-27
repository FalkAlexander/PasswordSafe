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
        parent_group = self.keepass_loader.get_parent_group_from_uuid(uuid)
        parent_group_button = NotImplemented
        for button in self.pathbar_buttons:
            if self.keepass_loader.get_group_uuid_from_group_object(parent_group) == button.get_uuid():
                parent_group_button = button

        if parent_group_button is NotImplemented:
            print("sub group of root")
            self.pathbar_buttons = []
            self.pathbar_buttons.append(self.create_pathbar_button(uuid))
            print(self.pathbar_buttons)
            self.rebuild_pathbar()

        else:    
            try:
                if uuid != self.pathbar_buttons[self.pathbar_buttons.index(parent_group_button)+1].get_uuid():
                    index = self.pathbar_buttons.index(parent_group_button)+1
                    for i in range(index, len(self.pathbar_buttons)):
                        self.pathbar_buttons.remove(self.pathbar_buttons[i])
                    self.pathbar_buttons.append(self.create_pathbar_button(uuid))
                    self.rebuild_pathbar()

            except(IndexError):
                print("button should be appended")
                pathbar_button_object = self.create_pathbar_button(uuid) 
                self.add(pathbar_button_object)
                self.add(self.get_seperator_label())
                self.pathbar_buttons.append(self.create_pathbar_button(uuid))
                self.show_all()


    def create_pathbar_button(self, uuid):
        pathbar_button = PathbarButton(uuid)
        pathbar_button.set_label(self.keepass_loader.get_group_name_from_uuid(uuid))
        pathbar_button.set_relief(Gtk.ReliefStyle.NONE)
        pathbar_button.activate()
        pathbar_button.connect("clicked", self.on_pathbar_button_clicked)

        return pathbar_button

    def rebuild_pathbar(self):
        for widget in self.get_children():
            self.remove(widget)

        self.add_home_button()
        self.add(self.get_seperator_label())

        for button in self.pathbar_buttons:
            pathbar_button = self.create_pathbar_button(button.get_uuid())
            self.add(pathbar_button)
            self.add(self.get_seperator_label())
        self.show_all()

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
