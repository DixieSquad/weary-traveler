import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import pandas as pd
import os
import time
import threading


class BackgroundTask(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            print("Background Task is running...")
            time.sleep(1)


class DataFrameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weary Traveler")
        root.minsize(800, 800)

        self.selected_file = tk.StringVar()
        self.dataframe = None

        # Background progress stuff
        self.running = False
        self.background_task = None

        # Set style
        style = ttk.Style()
        style.configure(".", font="20", rowheight=30)
        style.configure("TLabel", padding=20)

        # Create top frame
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.pack(side="top", fill="both", expand=False)

        # Create widgets
        self.label1 = ttk.Label(self.top_frame, text="Select CSV file:")
        self.dropdown = ttk.Combobox(self.top_frame, textvariable=self.selected_file)
        self.dropdown.bind("<<ComboboxSelected>>", lambda event: self.load_dataframe())
        self.button_update = ttk.Button(
            self.top_frame, text="auto-update", command=self.toggle_background_task
        )
        self.label_status = ttk.Label(self.top_frame, text="Paused.")

        # Layout widgets
        self.label1.pack(side="left", expand=False)
        self.dropdown.pack(side="left", expand=False)
        self.label_status.pack(side="right", expand=False)
        self.button_update.pack(side="right", expand=False)

        # Create bottom frame
        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.pack(side="bottom", fill="both", expand=True)

        # Create tree view
        self.tree_view = ttk.Treeview(self.bottom_frame, show="headings")

        # Layout tree view
        self.tree_view.pack(side="left", fill="both", expand=True)

        # Configure tree view
        self.tree_view["columns"] = ()

        # Adjust row and column weights
        root.grid_rowconfigure(2, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)

        self.load_dropdown_options()

    def toggle_background_task(self):
        if not self.running:
            self.start_background_task()
        else:
            self.stop_background_task()

    def start_background_task(self):
        if self.background_task is None or not self.background_task.is_alive():
            self.background_task = BackgroundTask()
            self.background_task.start()
            self.running = True
            self.button_update.config(text="Stop")
            self.label_status.config(text="Running updates...")
        else:
            ttk.messagebox.showwarning("Warning", "Background task is already running.")

    def stop_background_task(self):
        if self.background_task and self.background_task.is_alive():
            self.background_task.stop()
            self.background_task.join()
            self.running = False
            self.button_update.config(text="auto-update")
            self.label_status.config(text="Paused.")
        else:
            ttk.messagebox.showwarning("Warning", "No background task is running.")

    def load_dropdown_options(self):
        # Load available CSV files in the 'Output' folder
        folder_path = os.path.join(os.getcwd(), "data/profit")
        files = [file for file in os.listdir(folder_path) if file.endswith(".csv")]
        self.dropdown["values"] = files

    def load_dataframe(self):
        # Load selected CSV file and display its contents in tree view
        filename = self.selected_file.get()
        if filename:
            try:
                folder_path = os.path.join(os.getcwd(), "data/profit")
                file_path = os.path.join(folder_path, filename)
                self.dataframe = pd.read_csv(file_path)
                self.display_dataframe_in_treeview()
            except Exception as e:
                ttk.messagebox.showerror("Error", f"Failed to load DataFrame: {e}")

    def display_dataframe_in_treeview(self):
        # Clear existing tree view
        for child in self.tree_view.get_children():
            self.tree_view.delete(child)

        self.tree_view["columns"] = list(self.dataframe.columns[1:])
        # Format first column
        self.tree_view.heading(
            self.dataframe.columns[1], text=self.dataframe.columns[1]
        )
        self.tree_view.column(
            self.dataframe.columns[1], anchor="w", minwidth=350, width=350
        )
        # Format other columns
        for column in self.dataframe.columns[2:]:
            self.tree_view.heading(column, text=column)
            self.tree_view.column(column, anchor="e", width=50, minwidth=50)

        # Add data
        for index, row in self.dataframe.iterrows():
            self.tree_view.insert("", "end", values=list(row)[1:])


if __name__ == "__main__":
    root = ThemedTk(theme="equilux")
    app = DataFrameApp(root)
    root.mainloop()
