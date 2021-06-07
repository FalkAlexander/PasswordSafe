# SPDX-License-Identifier: GPL-3.0-only
import math

from gi.repository import GObject, Gtk


class ProgressIcon(Gtk.DrawingArea):

    __gtype_name__ = "ProgressIcon"

    _progress: float = 0.0
    SIZE = 16

    def __init__(self):
        super().__init__()

        self.set_content_width(self.SIZE)
        self.set_content_height(self.SIZE)
        self.set_draw_func(self.draw)

    def draw(self, area, cr, width, height):
        context = area.get_style_context()
        color = Gtk.StyleContext.get_color(context)

        color.alpha = 0.15
        cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)

        cr.arc(width / 2, height / 2, width / 2, 0.0, 2 * math.pi)
        cr.fill()

        if self.progress > 0.0:
            color.alpha = 1.0
            cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)
            cr.arc(
                width / 2,
                height / 2,
                width / 2,
                -0.5 * math.pi,
                2 * self.progress * math.pi - 0.5 * math.pi,
            )
            if self.progress != 1.0:
                cr.line_to(width / 2, height / 2)
                cr.line_to(width / 2, 0)

            cr.fill()

    @GObject.Property(type=float, default=0.0, flags=GObject.ParamFlags.READWRITE)
    def progress(self) -> float:
        return self._progress

    @progress.setter  # type: ignore
    def progress(self, progress: float) -> None:
        if self._progress != progress:
            self._progress = max(min(progress, 1.0), 0.0)
            self.queue_draw()
