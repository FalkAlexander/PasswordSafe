# SPDX-License-Identifier: GPL-3.0-only
"""Gtk.Button representing a path element in the pathbar"""
from gi.repository import GObject, Gtk

from passwordsafe.safe_element import SafeElement


class PathbarButton(Gtk.Button):
    """Gtk.Button representing a path element in the pathbar

    notable instance variables are:
    .uuid: the UUID of the group or entry
    """

    def __init__(self, element: SafeElement):
        super().__init__()

        assert isinstance(element, SafeElement)

        self.set_name("PathbarButtonDynamic")
        context = self.get_style_context()
        context.add_class("flat")

        self.is_group = element.is_group
        self.element: SafeElement = element

        if element.is_root_group:
            home_button_image = Gtk.Image.new_from_icon_name(
                "go-home-symbolic", Gtk.IconSize.BUTTON
            )
            self.add(home_button_image)
            return

        self.element.bind_property(
            "name", self, "label", GObject.BindingFlags.SYNC_CREATE)

    def set_active_style(self):
        context = self.get_style_context()
        context.add_class('PathbarButtonActive')
