# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import json
from typing import cast

from gi.repository import Gio

from gsecrets import const
from gsecrets.sorting import SortingHat

setting = Gio.Settings.new(const.APP_ID)

CLEAR_CLIPBOARD = "clear-clipboard"
DB_LOCK_TIMEOUT = "database-lock-timeout"
SHOW_START_SCREEN = "first-start-screen"
SAVE_AUTOMATICALLY = "save-automatically"
SORT_ORDER = "sort-order"
REMEMBER_COMPOSITE_KEY = "remember-composite-key"
LAST_USED_KEY_PROVIDER = "last-used-key-provider"
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
LOCK_ON_SESSION_LOCK = "lock-on-session-lock"
FINGERPRINT_QUICK_UNLOCK = "fingerprint-quick-unlock"
QUICK_UNLOCK = "quick-unlock"


def get_lock_on_session_lock() -> bool:
    return setting.get_boolean(LOCK_ON_SESSION_LOCK)


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


def get_database_lock_timeout():
    return setting.get_int(DB_LOCK_TIMEOUT)


def set_database_lock_timeout(value):
    setting.set_int(DB_LOCK_TIMEOUT, value)


def get_first_start_screen():
    return setting.get_boolean(SHOW_START_SCREEN)


def set_first_start_screen(value):
    setting.set_boolean(SHOW_START_SCREEN, value)


def get_save_automatically():
    return setting.get_boolean(SAVE_AUTOMATICALLY)


def set_save_automatically(value):
    setting.set_boolean(SAVE_AUTOMATICALLY, value)


def get_sort_order() -> SortingHat.SortOrder:
    """Return the sort order as Enum of type SortingHat.SortOrder."""
    return cast(SortingHat.SortOrder, setting.get_enum(SORT_ORDER))


def get_remember_composite_key():
    return setting.get_boolean(REMEMBER_COMPOSITE_KEY)


def set_remember_composite_key(value):
    setting.set_boolean(REMEMBER_COMPOSITE_KEY, value)


def get_provider_config(db_path: str, name: str) -> dict | None:
    providers = get_last_used_key_provider()
    uri = Gio.File.new_for_path(db_path).get_uri()

    if uri in providers and name in providers[uri]:
        data = json.loads(providers[uri])
        return data[name]

    return None


def get_last_used_key_provider() -> dict:
    """Get the history dict for previously opened databases with key providers."""
    last_used_key_provider = setting.get_string(LAST_USED_KEY_PROVIDER)
    return json.loads(last_used_key_provider)


def set_last_used_key_provider(provider_list: dict) -> None:
    """Set the history dict of key provider."""
    setting.set_string(LAST_USED_KEY_PROVIDER, json.dumps(provider_list))


def get_remember_unlock_method():
    return setting.get_boolean(REMEMBER_UNLOCK_METHOD)


def set_remember_unlock_method(value):
    setting.set_boolean(REMEMBER_UNLOCK_METHOD, value)


def get_development_backup_mode():
    return setting.get_boolean(DEV_BACKUP_MODE)


def set_development_backup_mode(value):
    setting.set_boolean(DEV_BACKUP_MODE, value)


def get_fingerprint_quick_unlock():
    return setting.get_boolean(FINGERPRINT_QUICK_UNLOCK)


def set_fingerprint_quick_unlock(value: bool) -> None:
    setting.set_boolean(FINGERPRINT_QUICK_UNLOCK, value)


def get_quick_unlock():
    return setting.get_boolean(QUICK_UNLOCK)


def set_quick_unlock(value: bool) -> None:
    setting.set_boolean(QUICK_UNLOCK, value)
