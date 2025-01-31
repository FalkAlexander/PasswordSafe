# SPDX-License-Identifier: GPL-3.0-only
import logging
from collections import deque

from gi.repository import Gio, GLib, GObject

from gsecrets.const import APP_ID

MAX_RECENT_ITEMS = 10


class RecentManager(GObject.Object):
    changed = GObject.Signal(arg_types=())

    def __init__(self):
        super().__init__()

        self.settings = Gio.Settings.new(APP_ID)

        self._load_items()
        self.settings.connect("changed::last-opened-list", self._on_settings_changed)

    def __iter__(self):
        return iter(self.recents)

    def __reversed__(self):
        return reversed(self.recents)

    def add_item(self, item: Gio.File) -> None:
        if found := next(
            (f for f in self.recents if f.get_uri() == item.get_uri()), None
        ):
            if bool(self.recents) and found != self.recents[-1]:
                self.recents.remove(found)
            else:
                return

        self.recents.append(item)
        self._save_items()
        self.emit(self.changed)

    def _remove_items(self, items: list[Gio.File]) -> None:
        for item in items:
            self.recents.remove(item)

        if bool(items):
            self._save_items()
            self.emit(self.changed)

    def is_empty(self) -> bool:
        return not bool(self.recents)

    def purge_items(self) -> None:
        if self.is_empty():
            return

        self.recents.clear()
        self._save_items()
        self.emit(self.changed)

    def _save_items(self):
        uris = [item.get_uri() for item in self.recents]
        self.settings.set_strv("last-opened-list", uris)

    def _load_items(self):
        uris = self.settings.get_strv("last-opened-list")
        items = [Gio.File.new_for_uri(uri) for uri in uris]
        self.recents = deque(items, MAX_RECENT_ITEMS)

    def _on_settings_changed(self, _settings, _key):
        self._load_items()
        self.emit(self.changed)

    async def clean_non_existent(self) -> None:
        to_remove = []

        for item in self.recents:
            try:
                await item.query_info_async(
                    Gio.FILE_ATTRIBUTE_STANDARD_TYPE,
                    Gio.FileQueryInfoFlags.NONE,
                    GLib.PRIORITY_DEFAULT,
                    None,
                )
            except GLib.Error as err:
                file_exist = not err.matches(
                    Gio.io_error_quark(), Gio.IOErrorEnum.NOT_FOUND
                )
                if file_exist:
                    logging.exception("Could not get file info")
                else:
                    uri = item.get_uri()
                    logging.info("Ignoring nonexistent recent file: %s", uri)

                to_remove.append(item)

        # We remove items after we are done iterating to avoid undefined
        # behaviour.
        self._remove_items(to_remove)
