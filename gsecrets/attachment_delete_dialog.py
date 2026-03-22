# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, Gtk, GObject

if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from gsecrets.database_manager import DatabaseManager
    from gsecrets.unlocked_database import UnlockedDatabase
    from pykeepass.attachment import Attachment


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/attachment_delete_dialog.ui")
class AttachmentDeleteDialog(Adw.AlertDialog):
    __gtype_name__ = "AttachmentDeleteDialog"

    def __init__(
        self,
        unlocked_database: UnlockedDatabase,
        attachment: Attachment,
        on_delete: Callable,
    ) -> None:
        """Dialog to confirm deleting an attachment."""
        super().__init__()

        self.__unlocked_database = unlocked_database
        self.__on_delete = on_delete
        self.__signal_handle = 0

        self.set_body(
            # TRANSLATORS The {filename} is a placeholder, must not be translated
            _(
                "The attachment “{filename}” will be deleted. "
                "This action cannot be undone."
            ).format(filename=attachment.filename)
        )

        self.__setup_signals()

    def __setup_signals(self):
        handle = self.__unlocked_database.database_manager.connect(
            "notify::locked",
            self.__on_locked,
        )
        self.__signal_handle = handle

    @Gtk.Template.Callback()
    def _on_delete(self, _dialog: Adw.AlertDialog, _response: str) -> None:
        self.__on_delete()

    def __on_locked(
        self, database_manager: DatabaseManager, _pspec: GObject.ParamSpec
    ) -> None:
        locked = database_manager.props.locked
        if locked:
            self.close()

    def do_closed(self) -> None:
        self.__unlocked_database.start_database_lock_timer()

        if handle := self.__signal_handle:
            self.__unlocked_database.database_manager.disconnect(handle)
            self.__signal_handle = 0
