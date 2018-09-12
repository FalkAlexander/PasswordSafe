from gi.repository import Gtk
import gi


class ScrolledPage(Gtk.ScrolledWindow):
    edit_page = False
    made_database_changes = False
    
    add_button_disabled = False

    properties_list_box = NotImplemented

    name_property_row = NotImplemented
    name_property_value_entry = NotImplemented

    username_property_row = NotImplemented
    username_property_value_entry = NotImplemented

    password_property_row = NotImplemented
    password_property_value_entry = NotImplemented
    show_password_button = NotImplemented
    generate_password_button = NotImplemented
    password_level_bar = NotImplemented

    url_property_row = NotImplemented
    url_property_value_entry = NotImplemented

    notes_property_row = NotImplemented
    notes_property_value_entry = NotImplemented

    icon_property_row = NotImplemented
    mail_icon_button = NotImplemented
    profile_icon_button = NotImplemented
    network_profile_button = NotImplemented
    key_button = NotImplemented
    terminal_icon_button = NotImplemented
    setting_icon_button = NotImplemented
    folder_icon_button = NotImplemented
    harddrive_icon_button = NotImplemented
    wifi_icon_button = NotImplemented
    desktop_icon_button = NotImplemented

    color_property_row = NotImplemented
    none_button = NotImplemented
    orange_button = NotImplemented
    green_button = NotImplemented
    blue_button = NotImplemented
    red_button = NotImplemented
    purple_button = NotImplemented
    brown_button = NotImplemented

    attributes_property_row = NotImplemented
    attributes_key_entry = NotImplemented
    attributes_value_entry = NotImplemented
    attributes_add_button = NotImplemented
    attribute_property_row_list = []

    def __init__(self, edit):
        Gtk.ScrolledWindow.__init__(self)
        self.set_name("ScrolledPage")
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.edit_page = edit

    def check_is_edit_page(self):
        return self.edit_page

    def get_made_database_changes(self):
        return self.made_database_changes

    def set_made_database_changes(self, bool):
        self.made_database_changes = bool
