# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _

from gi.repository import Gio

from gsecrets.recent_manager import RecentManager


class RecentFilesMenu:
    def __init__(self):
        """Recently opened files page menu.

        The `menu` attribute contains a GMenuModel to be used on popovers.
        """
        self.menu = Gio.Menu.new()
        self.section = Gio.Menu.new()
        self.is_empty = True

        recents = RecentManager()

        for item in reversed(recents):
            basename = item.get_basename()
            path = item.get_path()
            self.section.append(basename, f"win.open_database::{path}")
            self.is_empty = False

        self.menu.append_section(_("Recent Files"), self.section)
        self.menu.freeze()
