# SPDX-License-Identifier: GPL-3.0-only
from typing import cast

from gi.repository import Gio, GLib

from gsecrets import const
from gsecrets.sorting import SortingHat

setting = Gio.Settings.new(const.APP_ID)

CLEAR_CLIPBOARD = "clear-clipboard"
DARK_THEME = "dark-theme"
DB_LOCK_TIMEOUT = "database-lock-timeout"
SHOW_START_SCREEN = "first-start-screen"
LAST_OPENED_DB = "last-opened-database"
SAVE_AUTOMATICALLY = "save-automatically"
WINDOW_SIZE = "window-size"
SORT_ORDER = "sort-order"
LAST_OPENED_LIST = "last-opened-list"
REMEMBER_COMPOSITE_KEY = "remember-composite-key"
LAST_USED_COMPOSITE_KEY = "last-used-composite-key"
REMEMBER_UNLOCK_METHOD = "remember-unlock-method"
UNLOCK_METHOD = "unlock-method"
DEV_BACKUP_MODE = "development-backup-mode"
GENERATOR_USE_UPPERCASE = "generator-use-uppercase"
GENERATOR_USE_LOWERCASE = "generator-use-lowercase"
GENERATOR_USE_NUMBERS = "generator-use-numbers"
GENERATOR_USE_SYMBOLS = "generator-use-symbols"
GENERATOR_LENGTH = "generator-length"
GENERATOR_WORDS = "generator-words"
GENERATOR_SEPARATOR = "generator-separator"


def get_generator_use_uppercase() -> bool:
    return setting.get_boolean(GENERATOR_USE_UPPERCASE)


def set_generator_use_uppercase(value: bool) -> None:
    setting.set_boolean(GENERATOR_USE_UPPERCASE, value)


def get_generator_use_lowercase() -> bool:
    return setting.get_boolean(GENERATOR_USE_LOWERCASE)


def set_generator_use_lowercase(value: bool) -> None:
    setting.set_boolean(GENERATOR_USE_LOWERCASE, value)


def get_generator_use_numbers() -> bool:
    return setting.get_boolean(GENERATOR_USE_NUMBERS)


def set_generator_use_numbers(value: bool) -> None:
    setting.set_boolean(GENERATOR_USE_NUMBERS, value)


def get_generator_use_symbols() -> bool:
    return setting.get_boolean(GENERATOR_USE_SYMBOLS)


def set_generator_use_symbols(value: bool) -> None:
    setting.set_boolean(GENERATOR_USE_SYMBOLS, value)


def get_generator_length() -> int:
    return setting.get_int(GENERATOR_LENGTH)


def set_generator_length(value: int) -> None:
    setting.set_int(GENERATOR_LENGTH, value)


def get_generator_words() -> int:
    return setting.get_int(GENERATOR_WORDS)


def set_generator_words(value: int) -> None:
    setting.set_int(GENERATOR_WORDS, value)


def get_generator_separator() -> str:
    return setting.get_string(GENERATOR_SEPARATOR)


def set_generator_separator(value: str) -> None:
    setting.set_string(GENERATOR_SEPARATOR, value)


def get_clear_clipboard():
    return setting.get_int(CLEAR_CLIPBOARD)


def set_clear_clipboard(value):
    setting.set_int(CLEAR_CLIPBOARD, value)


def get_dark_theme():
    return setting.get_boolean(DARK_THEME)


def set_dark_theme(value):
    setting.set_boolean(DARK_THEME, value)


def get_database_lock_timeout():
    return setting.get_int(DB_LOCK_TIMEOUT)


def set_database_lock_timeout(value):
    setting.set_int(DB_LOCK_TIMEOUT, value)


def get_first_start_screen():
    return setting.get_boolean(SHOW_START_SCREEN)


def set_first_start_screen(value):
    setting.set_boolean(SHOW_START_SCREEN, value)


def get_last_opened_database():
    return setting.get_string(LAST_OPENED_DB)


def set_last_opened_database(value):
    setting.set_string(LAST_OPENED_DB, value)


def get_save_automatically():
    return setting.get_boolean(SAVE_AUTOMATICALLY)


def set_save_automatically(value):
    setting.set_boolean(SAVE_AUTOMATICALLY, value)


def get_window_size():
    return setting.get_value(WINDOW_SIZE)


def set_window_size(lis):
    g_variant = GLib.Variant("ai", lis)
    setting.set_value(WINDOW_SIZE, g_variant)


def get_sort_order() -> SortingHat.SortOrder:
    """Returns the sort order as Enum of type SortingHat.SortOrder"""
    value = cast(SortingHat.SortOrder, setting.get_enum(SORT_ORDER))
    return value


def get_last_opened_list():
    return setting.get_value(LAST_OPENED_LIST)


def set_last_opened_list(opened_list):
    g_variant = GLib.Variant("as", opened_list)
    setting.set_value(LAST_OPENED_LIST, g_variant)


def get_remember_composite_key():
    return setting.get_boolean(REMEMBER_COMPOSITE_KEY)


def set_remember_composite_key(value):
    setting.set_boolean(REMEMBER_COMPOSITE_KEY, value)


def get_last_used_composite_key():
    return setting.get_value(LAST_USED_COMPOSITE_KEY)


def set_last_used_composite_key(composite_list):
    g_variant = GLib.Variant("aas", composite_list)
    setting.set_value(LAST_USED_COMPOSITE_KEY, g_variant)


def get_remember_unlock_method():
    return setting.get_boolean(REMEMBER_UNLOCK_METHOD)


def set_remember_unlock_method(value):
    setting.set_boolean(REMEMBER_UNLOCK_METHOD, value)


def get_development_backup_mode():
    return setting.get_boolean(DEV_BACKUP_MODE)


def set_development_backup_mode(value):
    setting.set_boolean(DEV_BACKUP_MODE, value)
