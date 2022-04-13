# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/locked_headerbar.ui")
class LockedHeaderBar(Adw.Bin):

    __gtype_name__ = "LockedHeaderBar"
