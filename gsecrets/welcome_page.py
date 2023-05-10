# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Adw, Gtk

from gsecrets import const


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/welcome_page.ui")
class WelcomePage(Adw.Bin):
    __gtype_name__ = "WelcomePage"

    _status_page = Gtk.Template.Child()

    def __init__(self):
        """Welcome Page widget"""
        super().__init__()

        self._status_page.set_icon_name(const.APP_ID)
