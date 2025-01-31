# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
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
        to_remove = []

        attribute = Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE
        for item in reversed(recents):
            if not item.query_exists():
                uri = item.get_uri()
                logging.info("Ignoring nonexistent recent file: %s", uri)
                to_remove.append(item)
                continue

            file_info = item.query_info(
                attribute,
                Gio.FileQueryInfoFlags.NONE,
                None,
            )
            if content_type := file_info.get_attribute_as_string(attribute):
                mime_type = Gio.content_type_get_mime_type(content_type)
            else:
                mime_type = "application/octet-stream"

            if mime_type != "application/x-keepass2":
                continue

            basename = item.get_basename()
            path = item.get_path()
            self.section.append(basename, f"win.open_database::{path}")
            self.is_empty = False

        # We remove items after we are done iterating to avoid undefined
        # behaviour.
        for item in to_remove:
            recents.remove_item(item)

        self.menu.append_section(_("Recent Files"), self.section)
        self.menu.freeze()
