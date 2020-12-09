# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk, GLib
import threading

REVEAL_TIME = 3.0


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/notification.ui")
class Notification(Gtk.Revealer):

    __gtype_name__ = "Notification"

    label = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

    def notify(self, notification: str) -> None:
        self.label.set_label(notification)
        self.set_reveal_child(True)
        reveal_timer = threading.Timer(
            REVEAL_TIME, GLib.idle_add, args=[self.__hide_notification])
        reveal_timer.start()

    def __hide_notification(self) -> None:
        self.set_reveal_child(False)
