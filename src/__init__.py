from gi.repository import GLib
from os.path import exists, join, dirname, realpath
import os

HOME = os.getenv("HOME")
CONFIG_PATH = join(HOME, '.config/keepassgtk')
CONFIG_FILE = join(CONFIG_PATH, 'config.conf')

if not exists(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)

if not exists(CONFIG_FILE):
    cfg = GLib.KeyFile()
    cfg.set_string('settings', 'theme-variant', 'white')
    cfg.save_to_file(CONFIG_FILE)
    cfg.unref()