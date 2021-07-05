# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/search_headerbar.ui")
class SearchHeaderbar(Adw.HeaderBar):

    __gtype_name__ = "SearchHeaderbar"

    search_entry = Gtk.Template.Child()
