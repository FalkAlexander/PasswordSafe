# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk


class HistoryEntryBuffer(Gtk.EntryBuffer):
    logic = NotImplemented

    # TODO Use proper undo and Redo with GTK4
    def __init__(self, history):
        Gtk.EntryBuffer.__init__(self)
        self.logic = Logic(self, history)
        self.connect("inserted-text", self.logic.on_buffer_changed)
        self.connect("deleted-text", self.logic.on_buffer_changed, None)


class HistoryTextBuffer(Gtk.TextBuffer):
    logic = NotImplemented

    def __init__(self, history):
        Gtk.TextBuffer.__init__(self)
        self.logic = Logic(self, history)
        self.connect("changed", self.logic.on_buffer_changed, None, None, None)


class Logic():
    textbuffer = NotImplemented
    history = NotImplemented
    index = NotImplemented
    increase = True
    buffer_index = 0

    def __init__(self, textbuffer, history):
        self.textbuffer = textbuffer
        self.history = history

    def on_buffer_changed(self, textbuffer, _position, _chars, _n_chars):
        if self.increase is True:
            self.index = NotImplemented
            if isinstance(textbuffer, HistoryEntryBuffer):
                self.history.append(textbuffer.get_text())
            elif isinstance(textbuffer, HistoryTextBuffer):
                self.history.append(textbuffer.get_text(
                    textbuffer.get_start_iter(),
                    textbuffer.get_end_iter(),
                    False))
        else:
            self.buffer_index += 1
            if self.buffer_index == 2:
                self.increase = True
                self.buffer_index = 0

    def do_undo(self):
        op = False
        if self.index is NotImplemented:
            self.index = len(self.history) - 1
            op = True

        if self.index <= 0 or self.index > len(self.history):
            return

        self.increase = False
        if op is False:
            self.index -= 1
        self.history.append(self.history[self.index])
        text = self.history[self.index - 1]
        if text is not None:
            self.textbuffer.set_text(text, len(text))

    def do_redo(self):
        if self.index == len(self.history) or self.index is NotImplemented or self.index + 2 > len(self.history) or self.index + 1 < 0:
            return

        self.increase = False
        self.index += 1
        text = self.history[self.index]
        if text is not None:
            self.textbuffer.set_text(text, len(text))
