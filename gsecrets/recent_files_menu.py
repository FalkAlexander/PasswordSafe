# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from gettext import gettext as _

from gi.repository import Gio, GLib, Gtk


class RecentFilesMenu:
    def __init__(self):
        """Recently opened files page menu

        The `menu` attribute contains a GMenuModel to be used on popovers.
        """

        self.menu = Gio.Menu.new()
        self.section = Gio.Menu.new()
        self.is_empty = True

        recents = Gtk.RecentManager.get_default()
        to_remove = []

        for item in reversed(recents.get_items()):
            if not item.exists():
                uri = item.get_uri()
                logging.info("Ignoring nonexistent recent file: %s", uri)
                to_remove.append(uri)
                continue

            basename = item.get_display_name()
            path = item.get_uri_display()
            self.section.append(basename, f"win.open_database::{path}")
            self.is_empty = False

        # We remove items after we are done iterating to avoid undefined
        # behaviour.
        for uri in to_remove:
            try:
                recents.remove_item(uri)
            except GLib.Error as err:
                logging.error("Failed to remove %s from recent files: %s", uri, err)

        self.menu.append_section(_("Recent Files"), self.section)
        self.menu.freeze()
