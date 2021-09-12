# SPDX-License-Identifier: GPL-3.0-only
# pylint: skip-file

from gi.repository import GObject

from passwordsafe.notification import Notification
from passwordsafe.password_generator_popover import PasswordGeneratorPopover
from passwordsafe.recent_files_page import RecentFilesPage
from passwordsafe.welcome_page import WelcomePage
from passwordsafe.widgets.create_database_headerbar import CreateDatabaseHeaderbar
from passwordsafe.widgets.error_revealer import ErrorRevealer
from passwordsafe.widgets.expiration_date_row import ExpirationDateRow
from passwordsafe.widgets.notes_dialog import NotesDialog
from passwordsafe.widgets.password_level_bar import PasswordLevelBar
from passwordsafe.widgets.preferences_row import PreferencesRow
from passwordsafe.widgets.progress_icon import ProgressIcon
from passwordsafe.widgets.recent_files_headerbar import RecentFilesHeaderbar
from passwordsafe.widgets.unlock_database_headerbar import UnlockDatabaseHeaderbar


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
