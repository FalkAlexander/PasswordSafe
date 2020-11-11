# SPDX-License-Identifier: GPL-3.0-only
import logging
from enum import IntEnum
from gi.repository import GLib, Gio

setting = Gio.Settings.new("org.gnome.PasswordSafe")

CLEAR_CLIPBOARD = "clear-clipboard"
DARK_THEME = "dark-theme"
DB_LOCK_TIMEOUT = "database-lock-timeout"
SHOW_START_SCREEN = "first-start-screen"
LAST_OPENED_DB = "last-opened-database"
SAVE_AUTOMATICALLY = "save-automatically"
SHOW_PASSWORDS = "show-password-fields"
WINDOW_SIZE = "window-size"
SORT_ORDER = "sort-order"
LAST_OPENED_LIST = "last-opened-list"
REMEMBER_COMPOSITE_KEY = "remember-composite-key"
LAST_USED_COMPOSITE_KEY = "last-used-composite-key"
REMEMBER_UNLOCK_METHOD = "remember-unlock-method"
UNLOCK_METHOD = "unlock-method"
DEV_BACKUP_MODE = "development-backup-mode"
FULL_TEXT_SEARCH = "full-text-search"
LOCAL_SEARCH = "local-search"


class UnlockMethod(IntEnum):
    """Enum for database unlock methods"""
    PASSWORD = 0
    KEYFILE = 1
    COMPOSITE = 2


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


def get_full_text_search() -> bool:
    return setting.get_boolean(FULL_TEXT_SEARCH)


def set_full_text_search(value: bool) -> None:
    setting.set_boolean(FULL_TEXT_SEARCH, value)


def get_last_opened_database():
    return setting.get_string(LAST_OPENED_DB)


def set_last_opened_database(value):
    setting.set_string(LAST_OPENED_DB, value)


def get_local_search() -> bool:
    return setting.get_boolean(LOCAL_SEARCH)


def set_local_search(value: bool) -> None:
    setting.set_boolean(LOCAL_SEARCH, value)


def get_save_automatically():
    return setting.get_boolean(SAVE_AUTOMATICALLY)


def set_save_automatically(value):
    setting.set_boolean(SAVE_AUTOMATICALLY, value)


def get_show_password_fields():
    return setting.get_boolean(SHOW_PASSWORDS)


def set_show_password_fields(value):
    setting.set_boolean(SHOW_PASSWORDS, value)


def get_window_size():
    return setting.get_value(WINDOW_SIZE)


def set_window_size(lis):
    g_variant = GLib.Variant('ai', lis)
    setting.set_value(WINDOW_SIZE, g_variant)


def get_sort_order():
    value = setting.get_enum(SORT_ORDER)
    if value == 0:
        return "A-Z"
    if value == 1:
        return "Z-A"
    if value == 2:
        return "last_added"
    logging.warning("Retrieving unknown sort order")
    return None


def set_sort_order(value):
    if value == "A-Z":
        setting.set_enum(SORT_ORDER, 0)
    elif value == "Z-A":
        setting.set_enum(SORT_ORDER, 1)
    elif value == "last_added":
        setting.set_enum(SORT_ORDER, 2)


def get_last_opened_list():
    return setting.get_value(LAST_OPENED_LIST)


def set_last_opened_list(opened_list):
    g_variant = GLib.Variant('as', opened_list)
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


def get_unlock_method():
    """Get unlock method

    :returns: last unlock method used
    :rtype: UnlockMethod
    """
    value = setting.get_enum(UNLOCK_METHOD)
    if value == UnlockMethod.PASSWORD:
        return "password"
    if value == UnlockMethod.KEYFILE:
        return "keyfile"
    if value == UnlockMethod.COMPOSITE:
        return "composite"
    logging.warning("Retrieving unknown unlock method.")
    return None


def set_unlock_method(value):
    """Set Unlock Method

    :param UnlockMethod value: unlock method used
    """
    setting.set_enum(UNLOCK_METHOD, value)


def get_development_backup_mode():
    return setting.get_boolean(DEV_BACKUP_MODE)


def set_development_backup_mode(value):
    setting.set_boolean(DEV_BACKUP_MODE, value)
