# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from gettext import gettext as _

from gi.repository import Gio, GLib, Gtk

from gsecrets.recent_manager import RecentManager


class RecentFilesMenu:
    def __init__(self):
        """Recently opened files page menu

        The `menu` attribute contains a GMenuModel to be used on popovers.
        """

        self.menu = Gio.Menu.new()
        self.section = Gio.Menu.new()
        self.is_empty = True

        recents = RecentManager.get_default()
        to_remove = []

        for item in reversed(recents.get_items()):
            if not item.exists():
                path = item.path
                logging.info("Ignoring nonexistent recent file: %s", path)
                to_remove.append(path)
                continue

            basename = item.basename()
            path = item.path
            self.section.append(basename, f"win.open_database::{path}")
            self.is_empty = False

        # We remove items after we are done iterating to avoid undefined
        # behaviour.
        recents.remove_items(to_remove)

        self.menu.append_section(_("Recent Files"), self.section)
        self.menu.freeze()
