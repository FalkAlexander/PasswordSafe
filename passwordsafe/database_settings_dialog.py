from gi.repository import Gtk
from threading import Timer
import passwordsafe.config_manager
import gi


class DatabaseSettingsDialog():
    unlocked_database = NotImplemented
    database_manager = NotImplemented
    builder = NotImplemented

    def __init__(self, unlocked_database):
        self.unlocked_database = unlocked_database
        self.database_manager = unlocked_database.database_manager
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/database_settings_dialog.ui")

        self.open_dialog()

    def open_dialog(self):
        dialog = self.builder.get_object("database_settings_dialog")   

        save_password_button = self.builder.get_object("save_password_button")
        save_password_button.connect("clicked", self.on_change_password_button_clicked)

        self.builder.get_object("old_password_entry").grab_focus()

        dialog.set_modal(True)
        dialog.set_transient_for(self.unlocked_database.window)
        dialog.present()

    def on_change_password_button_clicked(self, widget):
        old_password_entry = self.builder.get_object("old_password_entry")
        new_password_entry = self.builder.get_object("new_password_entry")
        repeat_new_password_entry = self.builder.get_object("repeat_new_password_entry")

        old_password = old_password_entry.get_text()
        new_password = new_password_entry.get_text()
        repeat_password = repeat_new_password_entry.get_text()

        if new_password != repeat_password:
            old_password_entry.get_style_context().add_class("error")
            new_password_entry.get_style_context().add_class("error")
            repeat_new_password_entry.get_style_context().add_class("error")
            self.show_database_action_revealer("Wrong passwords")
        elif old_password is not "" and new_password is not "" and repeat_password is not "":
            if self.database_manager.password == old_password:
                self.database_manager.change_database_password(new_password)
                old_password_entry.get_style_context().remove_class("error")
                new_password_entry.get_style_context().remove_class("error")
                repeat_new_password_entry.get_style_context().remove_class("error")
                old_password_entry.set_text("")
                new_password_entry.set_text("")
                repeat_new_password_entry.set_text("")
                self.show_database_action_revealer("Database password changed")
            else:
                old_password_entry.get_style_context().add_class("error")
                new_password_entry.get_style_context().add_class("error")
                repeat_new_password_entry.get_style_context().add_class("error")
                self.show_database_action_revealer("Wrong passwords")
        else:
            old_password_entry.get_style_context().add_class("error")
            new_password_entry.get_style_context().add_class("error")
            repeat_new_password_entry.get_style_context().add_class("error")
            self.show_database_action_revealer("Wrong passwords")

    def show_database_action_revealer(self, message):
        database_action_box = self.builder.get_object("database_action_box")
        context = database_action_box.get_style_context()
        context.add_class('NotifyRevealer')

        database_action_label = self.builder.get_object("database_action_label")
        database_action_label.set_text(message)

        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())
        revealer_timer = Timer(3.0, self.hide_database_action_revealer)
        revealer_timer.start()

    def hide_database_action_revealer(self):
        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())
