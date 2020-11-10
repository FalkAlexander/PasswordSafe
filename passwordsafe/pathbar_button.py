# SPDX-License-Identifier: GPL-3.0-only
"""Gtk.Button representing a path element in the pathbar"""
from uuid import UUID
from gi.repository import Gtk


class PathbarButton(Gtk.Button):
    """Gtk.Button representing a path element in the pathbar

    notable instance variables are:
    .uuid: the UUID of the group or entry
    """

    def __init__(self, uuid: UUID, is_group: bool = False):
        Gtk.Button.__init__(self)
        self.set_name("PathbarButtonDynamic")
        self.is_group = is_group
        self.uuid: UUID = uuid

    def set_is_group(self):
        """Mark this button corresponding to a `Group` element"""
        self.is_group = True

    def set_is_entry(self):
        """Mark this button corresponding to a `Entry` element (default)"""
        self.is_group = False

    def get_is_group(self) -> bool:
        """Whether we represent a `Group` element, false implies `Entry`"""
        return self.is_group
