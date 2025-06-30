import tkinter as tk
from tkinter import ttk

class JSONTreeView(ttk.Treeview):
    def __init__(self, master):
        super().__init__(master, columns=("type"), show="tree")
        self.bind("<Double-1>", self.on_double_click)
        self.bind("<Button-3>", self.on_right_click)

    def load(self, data):
        self.delete(*self.get_children())
        self._insert_node("", data)

    def _insert_node(self, parent, data, key=None):
        pass

    def on_double_click(self, event):
        pass

    def on_right_click(self, event):
        pass

