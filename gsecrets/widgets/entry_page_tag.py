# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/entry_page_tag.ui")
class EntryPageTag(Gtk.FlowBoxChild):
    __gtype_name__ = "EntryPageTag"

    _label = Gtk.Template.Child()
    remove_button = Gtk.Template.Child()

    def __init__(self, name):
        super().__init__()

        self._label.set_label(name)
