# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from enum import Enum

from gi.repository import Gtk


class SaveDialogResponse(Enum):
    DISCARD = 0
    CANCEL = 1
    SAVE = 2


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/save_dialog.ui")
class SaveDialog(Gtk.MessageDialog):
    # pylint: disable=too-few-public-methods

    __gtype_name__ = "SaveDialog"

    def __init__(self, window):
        super().__init__()

        self.set_transient_for(window)

    def start(self) -> SaveDialogResponse:
        """Show the save confirmation dialog.

        :returns: The appropiate response from the dialog
        """
        response = self.run()
        self.destroy()

        if response in (
            Gtk.ResponseType.CANCEL,
            Gtk.ResponseType.NONE,
            Gtk.ResponseType.DELETE_EVENT,
        ):
            # Cancel everything, don't quit.
            # Also activated when pressing escape.
            return SaveDialogResponse.CANCEL

        if response == Gtk.ResponseType.NO:
            # clicked 'Discard'. Close, but don't save.
            return SaveDialogResponse.DISCARD

        if response == Gtk.ResponseType.YES:
            # "clicked save". Save changes.
            return SaveDialogResponse.SAVE

        logging.warning("This should be unreachable!")
        return SaveDialogResponse.CANCEL
