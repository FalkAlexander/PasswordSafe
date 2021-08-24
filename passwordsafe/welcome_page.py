# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gtk

RESOURCE = "/org/gnome/World/Secrets/images/welcome.png"


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/welcome_page.ui")
class WelcomePage(Gtk.Box):
    __gtype_name__ = "WelcomePage"

    _app_logo = Gtk.Template.Child()

    def __init__(self):
        """Welcome Page widget"""
        super().__init__()

        self._app_logo.set_from_resource(RESOURCE)
