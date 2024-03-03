from datetime import datetime

import numpy as np
import pandas as pd
import poe_ninja_scraper

poe_ninja_url = "https://poe.ninja/economy/affliction/skill-gems?level=5&quality=20&corrupted=No&gemType=Awakened"

poe_ninja_scraper.fetch_data(poe_ninja_url)

poe_ninja_df = pd.read_csv("data/ninja/poe_ninja_data.csv")
poe_ninja_ui = pd.DataFrame()
poe_ninja_ui["Item Name"] = poe_ninja_df["Name"]
poe_ninja_ui["Buy"] = np.nan
poe_ninja_ui["Sell"] = np.nan
poe_ninja_ui["Profit"] = np.nan
poe_ninja_ui["Updated At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

poe_ninja_ui.to_csv("data/profit/awakened_gems.csv", index=False)
