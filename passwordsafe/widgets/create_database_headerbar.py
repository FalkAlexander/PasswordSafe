# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/create_database_headerbar.ui")
class CreateDatabaseHeaderbar(Adw.Bin):

    __gtype_name__ = "CreateDatabaseHeaderbar"

    back_button = Gtk.Template.Child()
