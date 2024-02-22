import requests
import pandas as pd
import time

class ListingFetcher:
    def __init__(self, trade_url, header, payload) -> None:
        self.trade_url = trade_url
        self.header = header
        self.payload = payload

    def fetch_listing(self):
        try:
            r = requests.post(self.trade_url, headers=self.header, json=self.payload.query)
            r.raise_for_status()
            result = r.json().get('result', [])[:10]
            result_id = r.json().get('id', '')
            text_result = ','.join(result)
            fetch_url = f'https://www.pathofexile.com/api/trade/fetch/{text_result}?query={result_id}'
            listings = requests.get(fetch_url, headers=self.header)
            r.raise_for_status()
            result_list = listings.json().get('result', [])
            return result_list
        except requests.RequestException as e:
            print("Error: ", e)
            return []

    def extract_properties(self, item_properties):
        item_level, item_quality = None, None
        for prop in item_properties:
            if prop['name'] == 'Level':
                item_level = prop['values'][0][0]
            elif prop['name'] == 'Quality':
                item_quality = prop['values'][0][0]
            
        return item_level, item_quality

    def extract_gem_experience(self, additional_properties):
        for prop in additional_properties:
            if prop.get('name') == 'Experience':
                return prop.get('values', [])[0][0]
        return None

    def extract_data(self):
            extracted_data = []

            for item in self.fetch_listing():
                listing = item.get('listing', {})
                item_info = item.get('item', {})

                item_name = item_info.get('typeLine', '')
                item_properties = item_info.get('properties', [])
                item_corrupted = item_info.get('corrupted', False) 
                item_level, item_quality = self.extract_properties(item_properties)
                gem_experience = self.extract_gem_experience(item_info.get('additionalProperties', []))

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
                    'Corrupted': item_corrupted,
                    'Experience': gem_experience,
                    'Indexed': indexed,
                    'Stash Name': stash_name,
                    'Account Name': account_name,
                    'Player Status': player_status,
                    'Price Amount': price_amount,
                    'Currency': currency
                }
                
                extracted_data.append(row)

            return extracted_data

    def save_data(self):
        df = pd.DataFrame(self.extract_data())
        item_words=self.payload.item_type.split()
        df.to_csv(f"{'_'.join(item_words)}.csv")

class Payload:
    def __init__(self, status="online", item_type="", league="Affliction", min_quality=None, sort_by="price", corrupt=None, sort_order="asc") -> None:
        self.status = status
        self.item_type = item_type
        self.league = league
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.min_quality = min_quality
        self.corrupt = corrupt

        match sort_by:
            case "price":
                sort_field = "price"
            case "gem_level":
                sort_field = "gem_level"
            case _:
                sort_field = "price"

        filters = {}

        if self.min_quality is not None or self.corrupt is not None:
            filters["filters"] = {"misc_filters": { "filters": {}}}

            if self.min_quality is not None:
                filters["filters"]["misc_filters"]["filters"]["quality"] = {"min": self.min_quality}

            if self.corrupt is not None:
                filters["filters"]["misc_filters"]["filters"]["corrupted"] = {"option": self.corrupt}
                
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

def fetch_all_listings(listing_item, properties, header, trade_url):
    for name in listing_item:
        payload = Payload(item_type=name, status=properties['status'], league=properties['league'], min_quality=properties['min_quality'], sort_by=properties['sort_by'], corrupt=properties['corrupt'], sort_order=properties['sort_order'])
        fetcher = ListingFetcher(trade_url, header, payload)
        fetcher.save_data()
        time.sleep(10)

