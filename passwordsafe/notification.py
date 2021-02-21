# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import GLib, Gtk

REVEAL_TIME = 3.0


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/notification.ui")
class Notification(Gtk.Revealer):

    __gtype_name__ = "Notification"

    event_id = None
    label = Gtk.Template.Child()

    def send_notification(self, notification: str) -> None:
        self.label.set_label(notification)
        if self.event_id is not None:
            GLib.source_remove(self.event_id)
            self.event_id = None

        self.set_reveal_child(True)
        self.event_id = GLib.timeout_add_seconds(
            REVEAL_TIME, self.__hide_notification)

    def __hide_notification(self) -> None:
        self.event_id = None
        self.set_reveal_child(False)
