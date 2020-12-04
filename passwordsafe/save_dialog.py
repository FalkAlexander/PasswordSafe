# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from enum import Enum

from gi.repository import Gtk


class SaveDialogResponse(Enum):
    DISCARD = 0
    CANCEL = 1
    SAVE = 2


class SaveDialog():

    def __init__(self, window):
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/save_dialog.ui")
        self.dialog = builder.get_object("save_dialog")
        self.dialog.set_transient_for(window)

    def run(self) -> SaveDialogResponse:
        """Show the save confirmation dialog.

        :returns: The appropiate response from the dialog
        """
        response = self.dialog.run()
        self.dialog.destroy()

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
        elif response == Gtk.ResponseType.YES:
            # "clicked save". Save changes.
            return SaveDialogResponse.SAVE
        else:
            logging.warn("This should be unreachable!")
            return SaveDialogResponse.CANCEL
