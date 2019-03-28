from gi.repository import Gtk


class HistoryEntryBuffer(Gtk.EntryBuffer):
    history = []
    index = NotImplemented
    increase = True
    buffer_index = 0

    def __init__(self):
        Gtk.EntryBuffer.__init__(self)
        self.connect("inserted-text", self.on_buffer_changed)
        self.connect("deleted_text", self.on_buffer_changed, None)

    def on_buffer_changed(self, buffer, position, chars, n_chars):
        if self.increase is True:
            self.index = NotImplemented
            self.history.append(self.get_text())
        else:
            self.buffer_index += 1
            if self.buffer_index == 2:
                self.increase = True
                self.buffer_index = 0

    def do_undo(self):
        if self.index is NotImplemented:
            self.index = len(self.history)-1

        if self.index <= 0 or self.index > len(self.history):
            return

        self.increase = False
        self.index -= 1
        self.history.append(self.history[self.index])
        return self.history[self.index-1]


    def do_redo(self):
        if self.index == len(self.history) or self.index is NotImplemented:
            return

        self.increase = False
        self.index += 1
        self.history.append(self.history[self.index])
        return self.history[self.index]

