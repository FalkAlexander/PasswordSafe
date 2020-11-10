# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk, Pango


class ErrorInfoBar(Gtk.InfoBar):

    def __init__(self, main_text, secondary_text):
        """Display an error message as an InfoBar

        :param str main_text:
        :param str secondary_text:
        """
        super().__init__()

        self.props.message_type = Gtk.MessageType.ERROR
        self.props.show_close_button = True

        content = self.get_content_area()
        content.props.orientation = Gtk.Orientation.VERTICAL

        main_label = Gtk.Label(label=main_text)
        main_label.get_style_context().add_class("main")
        main_label.props.xalign = 0.
        main_label.props.ellipsize = Pango.EllipsizeMode.END
        # main_label.props.max_width_chars = 50
        content.add(main_label)

        secondary_label = Gtk.Label(label=secondary_text)
        secondary_label.get_style_context().add_class("secondary")
        secondary_label.props.xalign = 0.
        secondary_label.props.ellipsize = Pango.EllipsizeMode.END
        content.add(secondary_label)

        self.show_all()
