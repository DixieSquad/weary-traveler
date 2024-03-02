import os

import poe_ninja_scraper
import poe_trade_rest

# gems = ["Awakened Spell Echo Support", "Awakened Multistrike Support"]
gems = ["Awakened Spell Echo Support", "Awakened Added Cold Damage Support"]
poe_ninja_url = "https://poe.ninja/economy/skill-gems"

# poe_ninja_df = poe_ninja_scraper.fetch_data(poe_ninja_url)

properties = poe_trade_rest.get_gem_buy_sell_properties()

poe_trade_rest.fetch_all_listings(
    gems,
    properties["buy"],
    properties["sell"],
)
