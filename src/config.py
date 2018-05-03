import os
import gi
from os.path import exists, join, dirname, realpath
from gi.repository import GLib

cfg = GLib.KeyFile()

def configure():
    HOME = os.getenv("HOME")
    CONFIG_PATH = join(HOME, '.config/keepassgtk')
    CONFIG_FILE = join(CONFIG_PATH, 'config.conf')

    if not exists(CONFIG_PATH):
        create_config_dir(CONFIG_PATH)

    if not exists(CONFIG_FILE):
        create_config_file(CONFIG_FILE)

def create_config_dir(path):
    os.mkdir(path)

def create_config_file(filename):
    create_config_entry('settings', 'theme-variant', 'white')
    cfg.save_to_file(filename)
    cfg.unref()

def create_config_entry(header, option, value):
    cfg.set_string(header, option, value)
    


