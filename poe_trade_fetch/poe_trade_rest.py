import requests
import pandas as pd
import time

def fetch_listings(trade_url, payload, header):
    df = pd.DataFrame()
    try:
        r = requests.post(trade_url, headers=header, json=payload)
        if r.status_code == 200:
            result = r.json().get('result', [])[:10]
            result_id = r.json().get('id', '')
            text_result = ','.join(result)
            fetch_url = f'https://www.pathofexile.com/api/trade/fetch/{text_result}?query={result_id}'
            listings = requests.get(fetch_url, headers=header)
            result_list = listings.json().get('result', [])

            extracted_data = []

            for item in result_list:
                listing = item.get('listing', {})
                item_info = item.get('item', {})

                item_name = item_info.get('typeLine', '')
                item_properties = item_info.get('properties', [])

                item_level = None
                item_quality = None
                for prop in item_properties:
                    if prop['name'] == 'Level':
                        item_level = prop['values'][0][0]
                    if prop['name'] == 'Quality':
                        item_quality = prop['values'][0][0]

                gem_experience = None
                additional_properties = item_info.get('additionalProperties', [])
                if additional_properties:
                    for prop in additional_properties:
                        if prop.get('name') == 'Experience':
                            gem_experience = prop.get('values', [])[0][0]
                            break

                indexed = listing.get('indexed', '')
                stash_name = listing.get('stash',{}).get('name', '')
                account_name = listing.get('account', {}).get('name', '')
                player_status = listing.get('account', {}).get('online', {}).get('status', '')
                price_amount = listing.get('price', {}).get('amount', '')
                currency = listing.get('price', {}).get('currency', '')

                row = {
                    'Item Name': item_name,
                    'Item Level': item_level,
                    'Item Quality': item_quality,
                    'Experience': gem_experience,
                    'Indexed': indexed,
                    'Stash Name': stash_name,
                    'Account Name': account_name,
                    'Player Status': player_status,
                    'Price Amount': price_amount,
                    'Currency': currency
                }
                
                extracted_data.append(row)

            df = pd.DataFrame(extracted_data)


        else:
            print(f"Error: Failed to fetch listings. Status Code: {r.status_code}")
    except Exception as e:
        print("Error:", e)

    return df

class Payload:
    def __init__(self, status="online", item_type="", league="Affliction", max_quality=None, sort_by="price", sort_order="asc") -> None:
        self.status = status
        self.item_type = item_type
        self.league = league
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.max_quality = max_quality

        match sort_by:
            case "price":
                sort_field = "price"
            case "gem_level":
                sort_field = "gem_level"
            case _:
                sort_field = "price"

        filters = {}
        if self.max_quality is not None:
            filters = {"filters":{"misc_filters":{"filters":{"quality":{"max": self.max_quality}}}}}

        self.query = {
            "query": {
                "status": {"option": self.status},
                "type": self.item_type,
                "stats":[{"type":"and","filters":[]}],
                **filters
            },
            "sort":{sort_field: self.sort_order}
        }

# payload = Payload(item_type="Awakened Spell Echo Support")
def fetch_all_listings(item_names, header, trade_url, max_quality, sort_by):
    for item in item_names:
        payload = Payload(item_type=item, max_quality=max_quality, sort_by=sort_by)
        item_words = item.split()
        listing = fetch_listings(trade_url, payload.query, header)
        listing.to_csv(f"{'_'.join(item_words)}.csv")
        time.sleep(10)

# poe_trade_df = poe_trade_rest.fetch_listings(trade_url, payload.query, header)

