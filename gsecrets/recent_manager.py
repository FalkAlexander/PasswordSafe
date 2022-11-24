#!/usr/bin/env python3

import logging
import os

from gi.repository import Gio, GLib, GObject

import gsecrets.config_manager as config
from gsecrets import const

STATE_DIR = os.path.join(GLib.get_user_state_dir(), const.SHORT_NAME)
RECENTS_PATH = os.path.join(STATE_DIR, "recent_files")


class RecentItem:
    def __init__(self, path, keyfile=None):
        self.path = path
        self.keyfile = keyfile
        self.gfile = Gio.File.new_for_path(path)

    def exists(self) -> bool:
        return self.gfile.query_exists()

    @staticmethod
    def from_uri(uri, keyfile_uri=None) -> object:
        gfile = Gio.File.new_for_uri(uri)
        path = gfile.path()
        keyfile_path = None

        if keyfile_uri:
            gfile = Gio.File.new_for_uri(keyfile_uri)
            keyfile_path = gfile.path()

        return RecentItem(path, keyfile_path)

    def uri(self) -> str:
        return self.gfile.get_uri()

    def basename(self) -> str:
        return self.gfile.get_basename()


class RecentManager(GObject.Object):

    __gtype_name__ = "RecentManager"

    items: list[RecentItem] = []
    gfile = Gio.File.new_for_path(RECENTS_PATH)
    is_initialized = False

    changed = GObject.Signal()
    initialized = GObject.Signal()

    def __init__(self):
        super().__init__()

        if self.gfile.query_exists():
            self.load_items()
        else:
            self.create_file()

    def emit_initialized(self) -> None:
        if not self.is_initialized:
            self.is_initialized = True
            self.emit(self.initialized)

    @staticmethod
    def get_default() -> GObject.Object:
        app = Gio.Application.get_default()
        return app.recent_manager

    def get_last_opened(self) -> RecentItem | None:
        if self.items:
            return self.items[-1]

        return None

    def add_item(self, path: str, keyfile: str = None):
        new_items = []
        for item in self.items:
            if item.path != path:
                new_items.append(item)

        new_item = RecentItem(path, keyfile)
        new_items.append(new_item)
        if self.items != new_items:
            self.write_items(new_items)

    def has_item(self, path: str) -> bool:
        return any(item.path == path for item in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def get_items(self) -> list[RecentItem]:
        return self.items

    def remove_items(self, paths: list[str]) -> None:
        new_items = [item for item in self.items if item.path not in paths]

        if self.items != new_items:
            self.write_items(new_items)

    def purge_items(self) -> None:
        if self.items:
            self.write_items([])

    def create_file(self) -> None:
        self.gfile.create_async(
            Gio.FileCreateFlags.NONE, GLib.PRIORITY_DEFAULT, None, self.create_cb
        )

    def create_cb(self, recent, res):
        try:
            stream = recent.create_finish(res)
        except GLib.Error as err:
            logging.error("Could not create recent files file %s", err.message)
            self.emit_initialized()
        else:
            # TODO Do not migrate for 8.0
            items = migrated_items()
            if not items:
                self.emit_initialized()
                return

            items_bytes = items_to_bytes(items)
            gbytes = GLib.Bytes.new_take(items_bytes)
            stream.write_bytes_async(
                gbytes, GLib.PRIORITY_DEFAULT, None, self.write_cb, items
            )

    def write_cb(self, stream, res, items):
        try:
            stream.write_bytes_finish(res)
        except GLib.Error as err:
            logging.error("Could not close write bytes to stream %s", err.message)
            self.emit_initialized()
        else:
            stream.close_async(GLib.PRIORITY_DEFAULT, None, self.close_cb, items)

    def close_cb(self, stream, res, items):
        try:
            stream.close_finish(res)
        except GLib.Error as err:
            logging.error("Could not close recent files stream %s", err.message)
            self.emit_initialized()
        else:
            self.items = items
            self.emit(self.changed)
            self.emit_initialized()

    def write_items(self, items: list[RecentItem]) -> None:
        buff = items_to_bytes(items)

        gbytes = GLib.Bytes.new_take(buff)
        self.gfile.replace_contents_bytes_async(
            gbytes,
            None,
            False,
            Gio.FileCreateFlags.NONE,
            None,
            self.replace_contents_cb,
            items,
        )

    def replace_contents_cb(self, gfile, res, items):
        try:
            gfile.replace_contents_finish(res)
        except GLib.Error as err:
            logging.error("Could not replace contents of recent files %s", err.message)
        else:
            self.items = items
            self.emit(self.changed)

    def load_items(self) -> None:
        self.gfile.load_contents_async(None, self.load_contents_cb)

    def load_contents_cb(self, gfile, res):
        try:
            _b, contents, _etag = gfile.load_contents_finish(res)
        except GLib.Error as err:
            logging.error("Could not load contents of recent files %s", err.message)
            self.emit_initialized()
        else:
            items = bytes_to_items(contents)
            self.items = items
            if items:
                self.emit(self.changed)

            self.emit_initialized()


def migrated_items() -> list[RecentItem]:
    if config_list := config.get_last_opened_list():
        config.set_last_opened_list([])
        config.set_last_opened_database("")
        config.set_last_used_composite_key([])
        return [RecentItem.from_uri(uri) for uri in config_list]

    return []


def items_to_bytes(items: list[RecentItem]) -> bytes:
    buff = b""
    for item in items:
        buff += bytes(item.path, encoding="utf-8")
        if keyfile := item.keyfile:
            buff += b"\t" + bytes(keyfile, encoding="utf-8")

        buff += b"\n"

    return buff


def bytes_to_items(buff: bytes) -> list[RecentItem]:
    items = []
    string = str(buff, encoding="utf-8")
    lines = string.split("\n")
    for line in lines:
        # It can be a trailing new line
        if line in ["\n", "\0", ""]:
            continue

        split = line.split("\t")
        if len(split) == 2:
            item = RecentItem(split[0], split[1])
        else:
            item = RecentItem(split[0])

        items.append(item)

    return items
