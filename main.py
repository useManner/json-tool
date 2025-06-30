import tkinter as tk
from ui.layout import build_gui

def main():
    root = tk.Tk()
    root.title("JSON Tool Pro")
    build_gui(root)
    root.mainloop()

if __name__ == "__main__":
    main()
