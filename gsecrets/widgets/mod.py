# SPDX-License-Identifier: GPL-3.0-only
# pylint: skip-file

from gi.repository import GObject

from gsecrets.notification import Notification
from gsecrets.password_generator_popover import PasswordGeneratorPopover
from gsecrets.recent_files_page import RecentFilesPage
from gsecrets.welcome_page import WelcomePage
from gsecrets.widgets.create_database_headerbar import CreateDatabaseHeaderbar
from gsecrets.widgets.error_revealer import ErrorRevealer
from gsecrets.widgets.expiration_date_row import ExpirationDateRow
from gsecrets.widgets.notes_dialog import NotesDialog
from gsecrets.widgets.password_level_bar import PasswordLevelBar
from gsecrets.widgets.preferences_row import PreferencesRow
from gsecrets.widgets.progress_icon import ProgressIcon
from gsecrets.widgets.recent_files_headerbar import RecentFilesHeaderbar
from gsecrets.widgets.unlock_database_headerbar import UnlockDatabaseHeaderbar


def load_widgets():
    GObject.type_ensure(Notification)
    GObject.type_ensure(PasswordGeneratorPopover)
    GObject.type_ensure(RecentFilesPage)
    GObject.type_ensure(WelcomePage)
    GObject.type_ensure(CreateDatabaseHeaderbar)
    GObject.type_ensure(ErrorRevealer)
    GObject.type_ensure(ExpirationDateRow)
    GObject.type_ensure(NotesDialog)
    GObject.type_ensure(PasswordLevelBar)
    GObject.type_ensure(PreferencesRow)
    GObject.type_ensure(ProgressIcon)
    GObject.type_ensure(RecentFilesHeaderbar)
    GObject.type_ensure(UnlockDatabaseHeaderbar)
