# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _

from gi.repository import Adw

from gsecrets.widgets.saving_conflict_dialog import SavingConflictDialog


class QuitConflictDialog(SavingConflictDialog):
    __gtype_name__ = "QuitConflictDialog"

    def __init__(self, window, db_manager, save_callback):
        super().__init__(window, db_manager, save_callback)

        # TRANSLATORS Dialog header for when there is a conflict.
        self.props.heading = _("Unsaved Changes Conflict")

        self.set_response_label("save", _("Save and Quit"))
        self.set_response_label("backup", _("Back up, Save, and Quit"))
        self.set_response_label("cancel", _("Don't Quit"))

        self.add_response("discard", _("_Quit Without Saving"))
        self.set_response_appearance(
            "discard", Adw.ResponseAppearance.DESTRUCTIVE
        )
        self.connect("response::discard", self._on_response_discard)

    def _on_response_discard(self, _dialog, _response):
        self.window.force_close()
