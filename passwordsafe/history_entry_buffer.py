from gi.repository import Gtk


class HistoryEntryBuffer(Gtk.EntryBuffer):
    history = []
    index = 0

    def __init__(self):
        Gtk.EntryBuffer.__init__(self)
        self.connect("inserted-text", self.on_buffer_changed)
        self.connect("deleted_text", self.on_buffer_changed, None)

    def on_buffer_changed(self, buffer, position, chars, n_chars):
        print("Change!")
        self.history.append(self.get_text())
        self.index += 1

    def on_undo(self):
        self.history.append(self.history[index-1])
        self.index += 1
        return self.history[self.index]

    def on_redo(self):
        if self.index < len(self.history):
            return

        self.history.append(self.history[index+1])
        self.index += 1
        return self.history[self.index]

