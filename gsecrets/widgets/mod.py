# SPDX-License-Identifier: GPL-3.0-only
# pylint: skip-file

from gi.repository import GObject

from gsecrets.password_generator_popover import PasswordGeneratorPopover
from gsecrets.unlocked_headerbar import UnlockedHeaderBar
from gsecrets.welcome_page import WelcomePage
from gsecrets.widgets.add_list_box import AddListBox
from gsecrets.widgets.credentials_group import CredentialsGroup
from gsecrets.widgets.error_revealer import ErrorRevealer
from gsecrets.widgets.expiration_date_row import ExpirationDateRow
from gsecrets.widgets.history_row import HistoryRow
from gsecrets.widgets.history_window import HistoryWindow
from gsecrets.widgets.locked_headerbar import LockedHeaderBar
from gsecrets.widgets.notes_dialog import NotesDialog
from gsecrets.widgets.password_level_bar import PasswordLevelBar
from gsecrets.widgets.progress_icon import ProgressIcon
from gsecrets.widgets.selection_mode_headerbar import SelectionModeHeaderbar


def load_widgets():
    GObject.type_ensure(CredentialsGroup)
    GObject.type_ensure(PasswordGeneratorPopover)
    GObject.type_ensure(UnlockedHeaderBar)
    GObject.type_ensure(WelcomePage)
    GObject.type_ensure(AddListBox)
    GObject.type_ensure(ErrorRevealer)
    GObject.type_ensure(ExpirationDateRow)
    GObject.type_ensure(HistoryRow)
    GObject.type_ensure(HistoryWindow)
    GObject.type_ensure(LockedHeaderBar)
    GObject.type_ensure(NotesDialog)
    GObject.type_ensure(PasswordLevelBar)
    GObject.type_ensure(ProgressIcon)
    GObject.type_ensure(SelectionModeHeaderbar)
