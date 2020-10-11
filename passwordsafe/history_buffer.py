from gi.repository import Gtk


class HistoryEntryBuffer(Gtk.EntryBuffer):
    logic = NotImplemented

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
    buffer = NotImplemented
    history = NotImplemented
    index = NotImplemented
    increase = True
    buffer_index = 0

    def __init__(self, buffer, history):
        self.buffer = buffer
        self.history = history

    def on_buffer_changed(self, buffer, position, chars, n_chars):
        if self.increase is True:
            self.index = NotImplemented
            if type(buffer) is HistoryEntryBuffer:
                self.history.append(buffer.get_text())
            elif type(buffer) is HistoryTextBuffer:
                self.history.append(buffer.get_text(
                    buffer.get_start_iter(),
                    buffer.get_end_iter(),
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
        return self.history[self.index - 1]

    def do_redo(self):
        if self.index == len(self.history) or self.index is NotImplemented or self.index + 2 > len(self.history) or self.index + 1 < 0:
            return

        self.increase = False
        self.index += 1
        return self.history[self.index]
