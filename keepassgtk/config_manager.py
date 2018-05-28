import os
from os.path import exists, join
from gi.repository import GLib

cfg = GLib.KeyFile()

HOME = os.getenv("HOME")
CONFIG_PATH = join(HOME, '.config/keepassgtk')
CONFIG_FILE = join(CONFIG_PATH, 'config.conf')

#
# Create Config (First Run)
#


def configure():
    if not exists(CONFIG_PATH):
        create_config_dir(CONFIG_PATH)

    if not exists(CONFIG_FILE):
        create_config_file(CONFIG_FILE)


def create_config_dir(path):
    os.mkdir(path)


def create_config_file(filename):
    create_config_entry_string('settings', 'theme-variant', 'white')
    cfg.save_to_file(filename)

#
# Write Into Config
#


def create_config_entry_string(group, key, string):
    cfg.set_string(group, key, string)


def create_config_entry_integer(group, key, integer):
    cfg.set_integer(group, key, integer)


def create_config_entry_double(group, key, double):
    cfg.set_double(group, key, double)


def create_config_entry_boolean(group, key, boolean):
    cfg.set_boolean(group, key, boolean)

#
# Checks
#


def has_group(group):
    cfg.load_from_file(CONFIG_FILE, GLib.KeyFileFlags.KEEP_COMMENTS)
    return cfg.has_group(group)


# def has_key(key, group):
#     config_file = cfg.load_from_file(CONFIG_FILE, GLib.KeyFileFlags.KEEP_COMMENTS)
#     group = cfg.
#     return cfg.has_key(group, key)


def get_string(key, group):
    cfg.load_from_file(CONFIG_FILE, GLib.KeyFileFlags.KEEP_COMMENTS)
    return cfg.get_string(key, group)

#
# Save Config
#


def save_config():
    cfg.save_to_file(CONFIG_FILE)


def unref_config():
    cfg.unref()
