# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gtk


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/save_dialog.ui")
class SaveDialog(Gtk.MessageDialog):
    # pylint: disable=too-few-public-methods

    __gtype_name__ = "SaveDialog"

    def __init__(self, window):
        super().__init__()

        self.set_transient_for(window)
