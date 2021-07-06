# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/entry_page_icon.ui")
class EntryPageIcon(Gtk.FlowBoxChild):

    __gtype_name__ = "EntryPageIcon"

    image = Gtk.Template.Child()

    def __init__(self, icon_name, icon_number):
        super().__init__()

        self.image.props.icon_name = icon_name
        self.set_name(icon_number)
