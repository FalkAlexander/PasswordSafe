# SPDX-License-Identifier: GPL-3.0-only
"""Gtk.Button representing a path element in the pathbar"""
from gettext import gettext as _

from gi.repository import GObject, Gtk

from gsecrets.safe_element import SafeElement


class PathbarButton(Gtk.Button):
    """Gtk.Button representing a path element in the pathbar

    notable instance variables are:
    .uuid: the UUID of the group or entry
    """

    def __init__(self, element: SafeElement):
        super().__init__()

        assert isinstance(element, SafeElement)

        self.add_css_class("pathbar-button")
        self.add_css_class("flat")

        self.is_group = element.is_group
        self.element: SafeElement = element

        if element.is_root_group:
            self.set_icon_name("go-home-symbolic")
            self.props.tooltip_text = _("Root Group")
            return

        self.element.bind_property(
            "name", self, "label", GObject.BindingFlags.SYNC_CREATE
        )

    def set_active_style(self):
        self.add_css_class("pathbar-button-active")
