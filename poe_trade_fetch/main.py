import poe_ninja_scraper
import poe_trade_rest
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL")

buy_properties = {
    "payload_type": "buy",
    "status": "online",
    "league": "Affliction",
    "min_quality": None,
    "sort_by": "price",
    "corrupt": "false",
    "max_gem_level": 1,
    "sort_order": "asc",
}
sell_properties = {
    "payload_type": "sell",
    "status": "online",
    "league": "Affliction",
    "min_quality": 20,
    "sort_by": "price",
    "corrupt": "false",
    "min_gem_level": 5,
    "sort_order": "asc",
}
gems = ["Awakened Spell Echo Support", "Awakened Multistrike Support"]
trade_url = "https://www.pathofexile.com/api/trade/search/Affliction"
header = {"user-agent": str(EMAIL_ADDRESS)}
poe_ninja_url = "https://poe.ninja/economy/skill-gems"

poe_ninja_df = poe_ninja_scraper.fetch_data(poe_ninja_url)

poe_trade_rest.fetch_all_listings(
    gems, buy_properties, sell_properties, header, trade_url
)
