import poe_trade_rest as poe

# Test what happens when no item is returned with a search
properties = poe.get_gem_buy_sell_properties()
buy = properties["buy"]
sell = properties["sell"]
buy["min_quality"] = 100
sell["min_quality"] = 100

gem = ["Awakened Added Cold Damage Support"]

poe.fetch_all_listings(gem, buy, sell)
