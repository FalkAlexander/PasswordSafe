# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import GObject, Gtk

import passwordsafe.password_generator as password_generator


class PasswordLevelBar(Gtk.LevelBar):

    __gtype_name__ = "PasswordLevelBar"

    _entry: Gtk.Editable | None = None
    _password: str = ""

    def __init__(self) -> None:
        super().__init__()

        self.props.max_value = 5.0
        self.props.mode = Gtk.LevelBarMode.DISCRETE

        # Values in a discrete mode are rounded
        # instead of using a floor function.
        self.add_offset_value("insecure", 1.49)
        self.add_offset_value("weak", 2.49)
        self.add_offset_value("medium", 3.49)
        self.add_offset_value("strong", 4.49)
        self.add_offset_value("secure", 5.0)

    @GObject.Property(type=Gtk.Editable, flags=GObject.ParamFlags.READWRITE)
    def entry(self) -> Gtk.Editable:
        return self._entry

    @entry.setter  # type: ignore
    def entry(self, entry: Gtk.Editable) -> None:
        self._entry = entry
        entry.bind_property("text", self, "password", GObject.BindingFlags.SYNC_CREATE)

    @GObject.Property(type=str, flags=GObject.ParamFlags.READWRITE)
    def password(self) -> str:
        return self._password

    @password.setter  # type: ignore
    def password(self, password: str) -> None:
        self._password = password
        self.props.value = password_generator.strength(password)
