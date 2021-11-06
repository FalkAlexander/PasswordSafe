# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from enum import IntEnum

from gi.repository import Adw, GObject, Gtk

from gsecrets.pathbar import Pathbar

if typing.TYPE_CHECKING:
    from gsecrets.unlocked_database import UnlockedDatabase


class PageType(IntEnum):
    GROUP = 0
    ENTRY = 1


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/edit_element_headerbar.ui")
class EditElementHeaderbar(Adw.Bin):

    __gtype_name__ = "EditElementHeaderBar"

    _entry_menu = Gtk.Template.Child()
    _group_menu = Gtk.Template.Child()
    _pathbar_bin = Gtk.Template.Child()
    _secondary_menu_button = Gtk.Template.Child()

    def __init__(self, unlocked_database: UnlockedDatabase, page_type: PageType):
        super().__init__()

        self._pathbar_bin.set_child(Pathbar(unlocked_database))
        self._pathbar_bin.bind_property(
            "visible",
            unlocked_database.action_bar,
            "revealed",
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.INVERT_BOOLEAN
            | GObject.BindingFlags.SYNC_CREATE,
        )
        if page_type == PageType.GROUP:
            self._secondary_menu_button.set_menu_model(self._group_menu)
        else:
            self._secondary_menu_button.set_menu_model(self._entry_menu)
