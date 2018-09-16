from gi.repository import GLib, Gio

setting = Gio.Settings.new("org.gnome.PasswordSafe")

clear_clipboard = "clear-clipboard"
dark_theme = "dark-theme"
database_lock_timeout = "database-lock-timeout"
first_start_screen = "first-start-screen"
last_opened_database = "last-opened-database"
save_automatically = "save-automatically"
show_password_fields = "show-password-fields"
window_size = "window-size"
sort_order = "sort-order"
last_opened_list = "last-opened-list"
remember_composite_key = "remember-composite-key"
last_used_composite_key = "last-used-composite-key"
remember_unlock_method = "remember-unlock-method"
unlock_method = "unlock-method"
development_backup_mode = "development-backup-mode"


def get_clear_clipboard():
    return setting.get_int(clear_clipboard)

def set_clear_clipboard(value):
    setting.set_int(clear_clipboard, value)

def get_dark_theme():
    return setting.get_boolean(dark_theme)

def set_dark_theme(value):
    setting.set_boolean(dark_theme, value)

def get_database_lock_timeout():
    return setting.get_int(database_lock_timeout)

def set_database_lock_timeout(value):
    setting.set_int(database_lock_timeout, value)

def get_first_start_screen():
    return setting.get_boolean(first_start_screen)

def set_first_start_screen(value):
    setting.set_boolean(first_start_screen, value)

def get_last_opened_database():
    return setting.get_string(last_opened_database)

def set_last_opened_database(value):
    setting.set_string(last_opened_database, value)

def get_save_automatically():
    return setting.get_boolean(save_automatically)

def set_save_automatically(value):
    setting.set_boolean(save_automatically, value)

def get_show_password_fields():
    return setting.get_boolean(show_password_fields)

def set_show_password_fields(value):
    setting.set_boolean(show_password_fields, value)

def get_window_size():
    return setting.get_value(window_size)

def set_window_size(list):
    g_variant = GLib.Variant('ai', list)
    setting.set_value(window_size, g_variant)

def get_sort_order():
    value = setting.get_enum(sort_order)
    if value == 0:
        return "A-Z"
    elif value == 1:
        return "Z-A"
    elif value == 2:
        return "last_added"

def set_sort_order(value):
    if value == "A-Z":
        setting.set_enum(sort_order, 0)
    elif value == "Z-A":
        setting.set_enum(sort_order, 1)
    elif value == "last_added":
        setting.set_enum(sort_order, 2)

def get_last_opened_list():
    return setting.get_value(last_opened_list)

def set_last_opened_list(list):
    g_variant = GLib.Variant('as', list)
    setting.set_value(last_opened_list, g_variant)

def get_remember_composite_key():
    return setting.get_boolean(remember_composite_key)

def set_remember_composite_key(value):
    setting.set_boolean(remember_composite_key, value)

def get_last_used_composite_key():
    return setting.get_value(last_used_composite_key)

def set_last_used_composite_key(list):
    g_variant = GLib.Variant('aas', list)
    setting.set_value(last_used_composite_key, g_variant)

def get_remember_unlock_method():
    return setting.get_boolean(remember_unlock_method)

def set_remember_unlock_method(value):
    setting.set_boolean(remember_unlock_method, value)

def get_unlock_method():
    value = setting.get_enum(unlock_method)
    if value == 0:
        return "password"
    elif value == 1:
        return "keyfile"
    elif value == 2:
        return "composite"

def set_unlock_method(value):
    if value == "password":
        setting.set_enum(unlock_method, 0)
    elif value == "keyfile":
        setting.set_enum(unlock_method, 1)
    elif value == "composite":
        setting.set_enum(unlock_method, 2)

def get_development_backup_mode():
    return setting.get_boolean(development_backup_mode)

def set_development_backup_mode(value):
    setting.set_boolean(development_backup_mode, value)

