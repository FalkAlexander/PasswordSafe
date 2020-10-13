from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf
import passwordsafe.config_manager


class SettingsDialog():
    window = NotImplemented
    builder = NotImplemented

    def __init__(self, window):
        self.window = window
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/settings_dialog.ui")

    def on_settings_menu_clicked(self, _action, _param):
        settings_dialog = self.builder.get_object("settings_dialog")

        settings_dialog.set_modal(True)
        settings_dialog.set_transient_for(self.window)
        settings_dialog.present()

        self.set_config_values()

    def set_config_values(self):
        settings_theme_switch = self.builder.get_object("settings_theme_switch")
        settings_theme_switch.connect("notify::active", self.on_settings_theme_switch_switched)
        settings_theme_switch_value = passwordsafe.config_manager.get_dark_theme()
        settings_theme_switch.set_active(settings_theme_switch_value)

        settings_fstart_switch = self.builder.get_object("settings_fstart_switch")
        settings_fstart_switch.connect("notify::active", self.on_settings_fstart_switch_switched)
        settings_fstart_switch_value = passwordsafe.config_manager.get_first_start_screen()
        settings_fstart_switch.set_active(settings_fstart_switch_value)

        settings_save_switch = self.builder.get_object("settings_save_switch")
        settings_save_switch.connect("notify::active", self.on_settings_save_switch_switched)
        settings_save_switch_value = passwordsafe.config_manager.get_save_automatically()
        settings_save_switch.set_active(settings_save_switch_value)

        settings_lockdb_spin_button = self.builder.get_object("settings_lockdb_spin_button")
        settings_lockdb_spin_button.connect("value-changed", self.on_settings_lockdb_spin_button_changed)
        settings_lockdb_spin_button_value = passwordsafe.config_manager.get_database_lock_timeout()
        lockdb_adjustment = Gtk.Adjustment(settings_lockdb_spin_button_value, 0, 60, 1, 5)
        settings_lockdb_spin_button.set_adjustment(lockdb_adjustment)

        settings_clearcb_spin_button = self.builder.get_object("settings_clearcb_spin_button")
        settings_clearcb_spin_button.connect("value-changed", self.on_settings_clearcb_spin_button_changed)
        settings_clearcb_spin_button_value = passwordsafe.config_manager.get_clear_clipboard()
        clearcb_adjustment = Gtk.Adjustment(settings_clearcb_spin_button_value, 0, 300, 1, 5)
        settings_clearcb_spin_button.set_adjustment(clearcb_adjustment)

        settings_showpw_switch = self.builder.get_object("settings_showpw_switch")
        settings_showpw_switch.connect("notify::active", self.on_settings_showpw_switch_switched)
        settings_showpw_switch_value = passwordsafe.config_manager.get_show_password_fields()
        settings_showpw_switch.set_active(settings_showpw_switch_value)

        settings_clear_button = self.builder.get_object("settings_clear_button")
        settings_clear_button.connect("clicked", self.on_settings_clear_recents_clicked)

        if passwordsafe.config_manager.get_last_opened_list():
            settings_clear_button.set_sensitive(False)

        settings_remember_switch = self.builder.get_object("settings_remember_switch")
        settings_remember_switch.connect("notify::active", self.on_settings_remember_switch_switched)
        settings_remember_switch_value = passwordsafe.config_manager.get_remember_composite_key()
        settings_remember_switch.set_active(settings_remember_switch_value)

        settings_remember_method_switch = self.builder.get_object("settings_remember_method_switch")
        settings_remember_method_switch.connect("notify::active", self.on_settings_remember_method_switch_switched)
        settings_remember_method_switch_value = passwordsafe.config_manager.get_remember_unlock_method()
        settings_remember_method_switch.set_active(settings_remember_method_switch_value)

    def on_settings_theme_switch_switched(self, switch_button, _gparam):
        gtk_settings = Gtk.Settings.get_default()

        if switch_button.get_active():
            passwordsafe.config_manager.set_dark_theme(True)
            gtk_settings.set_property("gtk-application-prefer-dark-theme", True)
        else:
            passwordsafe.config_manager.set_dark_theme(False)
            gtk_settings.set_property("gtk-application-prefer-dark-theme", False)

    def on_settings_fstart_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            passwordsafe.config_manager.set_first_start_screen(True)
        else:
            passwordsafe.config_manager.set_first_start_screen(False)

    def on_settings_save_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            passwordsafe.config_manager.set_save_automatically(True)
        else:
            passwordsafe.config_manager.set_save_automatically(False)

    def on_settings_lockdb_spin_button_changed(self, spin_button):
        passwordsafe.config_manager.set_database_lock_timeout(spin_button.get_value())
        for db in self.window.opened_databases:
            db.start_database_lock_timer()

    def on_settings_clearcb_spin_button_changed(self, spin_button):
        passwordsafe.config_manager.set_clear_clipboard(spin_button.get_value())

    def on_settings_showpw_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            passwordsafe.config_manager.set_show_password_fields(True)
        else:
            passwordsafe.config_manager.set_show_password_fields(False)

    def on_settings_clear_recents_clicked(self, widget):
        passwordsafe.config_manager.set_last_opened_list([])
        if self.window.container is NotImplemented or not self.window.container.get_n_pages():
            builder = Gtk.Builder()
            builder.add_from_resource(
                "/org/gnome/PasswordSafe/main_window.ui")

            self.window.remove(self.window.first_start_grid)

            pix = Pixbuf.new_from_resource_at_scale("/org/gnome/PasswordSafe/images/welcome.png", 256, 256, True)
            app_logo = builder.get_object("app_logo")
            app_logo.set_from_pixbuf(pix)
            self.window.first_start_grid = builder.get_object("first_start_grid")
            self.window.add(self.window.first_start_grid)
        widget.set_sensitive(False)

    def on_settings_remember_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            passwordsafe.config_manager.set_remember_composite_key(True)
        else:
            passwordsafe.config_manager.set_remember_composite_key(False)
            passwordsafe.config_manager.set_last_used_composite_key("")

    def on_settings_remember_method_switch_switched(self, switch_button, _gparam):
        if switch_button.get_active():
            passwordsafe.config_manager.set_remember_unlock_method(True)
        else:
            passwordsafe.config_manager.set_remember_unlock_method(False)
            passwordsafe.config_manager.set_unlock_method("password")
