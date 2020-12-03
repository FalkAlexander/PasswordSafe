# SPDX-License-Identifier: GPL-3.0-only
from typing import List

from gi.repository import Gtk


class ScrolledPage(Gtk.ScrolledWindow):
    edit_page = False
    is_dirty = False  # Whether the database needs saving

    all_properties_revealed = False
    show_all_properties_button = NotImplemented

    properties_list_box = NotImplemented

    name_property_row = NotImplemented
    name_property_value_entry = NotImplemented

    username_property_row = NotImplemented
    username_property_value_entry = NotImplemented

    password_property_row = NotImplemented

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

    attributes_property_row = NotImplemented
    attributes_key_entry = NotImplemented
    attributes_value_entry = NotImplemented
    attributes_add_button = NotImplemented
    attribute_property_row_list: List[Gtk.ListBoxRow] = []

    attachment_property_row = NotImplemented
    attachment_list_box = NotImplemented

    show_all_row = NotImplemented

    def __init__(self, edit):
        Gtk.ScrolledWindow.__init__(self)
        self.set_name("ScrolledPage")
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.edit_page = edit

    def check_is_edit_page(self):
        return self.edit_page
