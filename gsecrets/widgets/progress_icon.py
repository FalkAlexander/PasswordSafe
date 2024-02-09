# SPDX-License-Identifier: GPL-3.0-only
import math

from gi.repository import GObject, Gdk, Gtk, Graphene


class ProgressIcon(GObject.Object, Gdk.Paintable, Gtk.SymbolicPaintable):
    __gtype_name__ = "ProgressIcon"

    _progress: float = 0.0

    def do_snapshot_symbolic(self, snapshot, width, height, colors, _n_colors):
        color = colors[Gtk.SymbolicColor.FOREGROUND]
        color.alpha = 0.15

        rect = Graphene.Rect().alloc()
        rect.init(0, 0, width, height)

        ctx = snapshot.append_cairo(rect)
        ctx.set_source_rgba(color.red, color.green, color.blue, color.alpha)

        ctx.arc(width / 2, height / 2, width / 2, 0.0, 2 * math.pi)
        ctx.fill()

        if self.props.progress > 0.0:
            color.alpha = 1.0
            ctx.set_source_rgba(color.red, color.green, color.blue, color.alpha)
            ctx.arc(
                width / 2,
                height / 2,
                width / 2,
                -0.5 * math.pi,
                2 * self.props.progress * math.pi - 0.5 * math.pi,
            )
            if self.props.progress != 1.0:
                ctx.line_to(width / 2, height / 2)
                ctx.line_to(width / 2, 0)

            ctx.fill()

    @GObject.Property(type=float, default=0.0)
    def progress(self) -> float:
        return self._progress

    @progress.setter  # type: ignore
    def progress(self, progress: float) -> None:
        progress = max(min(progress, 1.0), 0.0)
        if self._progress != progress:
            self._progress = progress
            self.invalidate_contents()
