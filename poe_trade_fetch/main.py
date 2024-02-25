import poe_ninja_scraper
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

poe_ninja_df = poe_ninja_scraper.fetch_data(poe_ninja_url)
