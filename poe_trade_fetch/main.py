import scraper
import poe_trade_rest

properties = {
    "status": "online",
    "league": "Affliction",
    "min_quality": None,
    "sort_by": "price",
    "corrupt": "false",
    "max_gem_level": 1,
    "sort_order": "asc",
}
gems = ["Awakened Spell Echo Support", "Awakened Multistrike Support"]
trade_url = "https://www.pathofexile.com/api/trade/search/Affliction"
header = {"user-agent": "***REMOVED***"}
poe_ninja_url = "https://poe.ninja/economy/skill-gems"

poe_trade_rest.fetch_all_listings(gems, properties, header, trade_url)

# poe_ninja_df = scraper.fetch_data(poe_ninja_url)
# poe_trade_df = poe_trade_rest.fetch_listings(trade_url, payload.query, header)

# poe_ninja_df.to_csv('poe_ninja_data.csv')
# poe_trade_df.to_csv('poe_trade_data.csv')
