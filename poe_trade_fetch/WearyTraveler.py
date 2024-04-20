import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from tkinter import messagebox

import pandas as pd
from poe_trade_rest import DataHandler, ProfitStrat, ItemEntry
from ttkthemes import ThemedTk


class BackgroundTask(threading.Thread):
    def __init__(self) -> None:
        super().__init__()
        self._stop_event = threading.Event()
        self.datahandler = DataHandler()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            print("Background Task is running...")
            self.datahandler.update_oldest_item_entry()


class DataFrameApp:
    def __init__(self, root: ThemedTk) -> None:
        self.root = root
        self.root.title("Weary Traveler")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.minsize(800, 800)

        self.selected_file = tk.StringVar()
        self.datahandler = DataHandler()
        self.data: list[ProfitStrat] = []

        # Background progress stuff
        self.background_task = None

        # Set style
        style = ttk.Style()
        style.configure(".", font="20", rowheight=30)
        style.configure("TLabel", padding=20)
        style.configure("Treeview", rowheight=60)

        # Create top frame
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.pack(side="top", fill="both", expand=False)

        # Create widgets
        self.label1 = ttk.Label(self.top_frame, text="Select file:")
        self.dropdown = ttk.Combobox(self.top_frame, textvariable=self.selected_file)
        self.dropdown.bind("<<ComboboxSelected>>", lambda event: self.load_data())
        self.button_update = ttk.Button(
            self.top_frame,
            text="auto-update",
            command=self.toggle_background_task,
            takefocus=False,
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
        self.tree_view = ttk.Treeview(self.bottom_frame)
        # Configure tree view
        self.configure_tree_view()
        # Layout tree view
        self.tree_view.pack(side="left", fill="both", expand=True)

        # Adjust row and column weights
        root.grid_rowconfigure(2, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)

        self.load_dropdown_options()

    def configure_tree_view(self) -> None:
        columns = (
            "Buy mods",
            "Sell mods",
            "Buy price",
            "Sell price",
            "Profit",
            "Last updated",
        )
        widths = (
            300,
            300,
            80,
            80,
            80,
            300,
        )
        self.tree_view["columns"] = columns
        self.tree_view.heading("#0", text="Item name", anchor="w")
        self.tree_view.column("#0", width=500)
        for column, width in zip(columns, widths):
            self.tree_view.heading(column=column, text=column, anchor="e")
            self.tree_view.column(column=column, width=width)

    def auto_refresh(self) -> None:
        if self.background_task and self.background_task.is_alive():
            print("refreshed")
            self.load_data()
            self.root.after(10000, self.auto_refresh)
        else:
            print("last refresh, stop refreshing")
            self.load_data()
            self.button_update.config(text="auto-update", state=tk.NORMAL)
            self.label_status.config(text="Paused.")

    def get_relative_time(self, time: str) -> str:
        updated_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        delta = datetime.now() - updated_time
        if delta.seconds <= 120 and delta.days == 0:
            updated = str(delta.seconds) + "s ago"
        elif delta.seconds <= 3600 and delta.days == 0:
            updated = str(round(delta.seconds / 60)) + " min ago"
        elif delta.seconds <= 86400 and delta.days == 0:
            updated = str(round(delta.seconds / 3600)) + " h ago"
        elif delta.days <= 5:
            updated = str(delta.days) + " days ago"
        else:
            updated = "5+ days ago"

        return updated

    def toggle_background_task(self) -> None:
        if self.background_task is None or not self.background_task.is_alive():
            self.start_background_task()
        else:
            self.stop_background_task()

    def start_background_task(self) -> None:
        if self.background_task is None or not self.background_task.is_alive():
            self.background_task = BackgroundTask()
            self.background_task.start()
            self.auto_refresh()
            self.button_update.config(text="Stop")
            self.label_status.config(text="Running updates...")
        else:
            messagebox.showwarning("Warning", "Background task is already running.")

    def stop_background_task(self) -> None:
        if self.background_task and self.background_task.is_alive():
            self.background_task.stop()
            self.button_update.config(text="Stopping...", state=tk.DISABLED)
        else:
            messagebox.showwarning("Warning", "No background task is running.")

    def load_dropdown_options(self) -> None:
        # Load available json files in the 'profit strats' folder
        folder_path = os.path.join(os.getcwd(), "data/profit_strats")
        files = [file for file in os.listdir(folder_path) if file.endswith(".json")]
        self.dropdown["values"] = files

    def load_data(self) -> None:
        self.data = self.datahandler.read_all_profit_strats()
        self.display_data_in_treeview()

    def display_data_in_treeview(self) -> None:
        # Clear existing tree view
        for child in self.tree_view.get_children():
            self.tree_view.delete(child)

        # Add data
        for profit_strat in self.data:
            values = (
                profit_strat.buy_item.mods_to_str(),
                profit_strat.sell_item.mods_to_str(),
                profit_strat.buy_item.value,
                profit_strat.sell_item.value,
                profit_strat.profit,
                profit_strat.sell_item.updated_at,
            )
            self.tree_view.insert(
                "", tk.END, text=profit_strat.item_name, values=values
            )

    def on_close(self) -> None:
        if self.background_task and self.background_task.is_alive():
            print(
                "Gracefully shutting down auto-update, this can take up to 10 seconds..."
            )
            self.stop_background_task()
        self.root.destroy()


if __name__ == "__main__":
    root = ThemedTk(theme="equilux")
    app = DataFrameApp(root)
    root.mainloop()
