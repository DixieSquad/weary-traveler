import scraper
import poe_trade_rest

gem_names = ["Awakened Spell Echo Support", "Awakened Multistrike Support"]
trade_url = 'https://www.pathofexile.com/api/trade/search/Affliction'
header = {'user-agent':'***REMOVED***'}
poe_ninja_url = 'https://poe.ninja/economy/skill-gems'

poe_trade_rest.fetch_all_listings(gem_names, header, trade_url)

# poe_ninja_df = scraper.fetch_data(poe_ninja_url)
# poe_trade_df = poe_trade_rest.fetch_listings(trade_url, payload.query, header)

# poe_ninja_df.to_csv('poe_ninja_data.csv')
# poe_trade_df.to_csv('poe_trade_data.csv')

