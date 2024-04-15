# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, GObject, Gtk


class OsdProgressBar(Adw.Bin):
    __gtype_name__ = "OsdProgressBar"

    def __init__(self):
        super().__init__()

        progress = Gtk.ProgressBar(
            visible=False,
            halign=Gtk.Align.FILL,
            valign=Gtk.Align.START,
            pulse_step=0.01,
        )
        progress.add_css_class("osd")

        overlay = Gtk.Overlay()
        overlay.add_overlay(progress)

        self.props.child = overlay

        self._progress = progress
        self._overlay = overlay

        def callback(_value: float) -> None:
            self._progress.pulse()

        target = Adw.CallbackAnimationTarget.new(callback)
        animation = Adw.TimedAnimation.new(
            self,
            0.0,
            0.0,
            Adw.DURATION_INFINITE,
            target,
        )

        self._animation = animation

    def start_pulse(self) -> None:
        self._progress.set_visible(True)
        self._animation.play()

    def end_pulse(self) -> None:
        self._progress.set_visible(False)
        self._animation.pause()
        self._animation.reset()

    @GObject.Property(type=Gtk.Widget)
    def content(self):
        return self._overlay.props.child

    @content.setter  # type: ignore
    def content(self, content):
        self._overlay.props.child = content
