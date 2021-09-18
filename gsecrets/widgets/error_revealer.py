# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Adw, GLib, Gtk, GObject

DURATION = 3.0


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/error_revealer.ui")
class ErrorRevealer(Adw.Bin):

    __gtype_name__ = "ErrorRevealer"

    _revealer = Gtk.Template.Child()

    label = GObject.Property(type=str, default="")
    _source_id: int | None = None

    def reveal(self, reveal: bool, label: str | None = None) -> None:
        if self._source_id:
            GLib.source_remove(self._source_id)
            self._source_id = None

        if reveal:
            if label:
                self.props.label = label

            self._revealer.props.reveal_child = True
            self._source_id = GLib.timeout_add_seconds(DURATION, self._hide_callback)
        else:
            self._revealer.props.reveal_child = False

    def _hide_callback(self) -> None:
        self.reveal(False)

        return GLib.SOURCE_REMOVE
