# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
from gettext import gettext as _

from gi.repository import Gio

import gsecrets.config_manager as config


class RecentFilesMenu:
    def __init__(self):
        """Recently opened files page menu

        The `menu` attribute contains a GMenuModel to be used on popovers.
        """

        self.menu = Gio.Menu.new()
        self.section = Gio.Menu.new()
        self.is_empty = True

        for path_uri in reversed(config.get_last_opened_list()):
            gfile: Gio.File = Gio.File.new_for_uri(path_uri)
            # TODO Remove the file from config if it does not exist.
            if not gfile.query_exists():
                logging.info("Ignoring nonexistent recent file: %s", gfile.get_path())
                continue  # only work with existing files

            basename = os.path.splitext(gfile.get_basename())[0]
            path = gfile.get_path()
            self.section.append(basename, f"win.open_database::{path}")
            self.is_empty = False

        self.menu.append_section(_("Recent Files"), self.section)
        self.menu.freeze()
