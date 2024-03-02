import os
import time
from datetime import datetime

import pandas as pd
import requests


class ListingFetcher:
    def __init__(self, trade_url, header, payload) -> None:
        self.trade_url = trade_url
        self.header = header
        self.payload = payload

    def fetch_listing(self):
        try:
            r = requests.post(
                self.trade_url, headers=self.header, json=self.payload.query
            )
            r.raise_for_status()
            time.sleep(2)
            result = r.json().get("result", [])[:10]
            result_id = r.json().get("id", "")
            text_result = ",".join(result)
            fetch_url = f"https://www.pathofexile.com/api/trade/fetch/{text_result}?query={result_id}"
            listings = requests.get(fetch_url, headers=self.header)
            r.raise_for_status()
            time.sleep(5)
            result_list = listings.json().get("result", [])
            return result_list
        except requests.RequestException as e:
            print("Error: ", e)
            return []

    def extract_properties(self, item_properties):
        item_level, item_quality = None, None
        for prop in item_properties:
            if prop["name"] == "Level":
                item_level = prop["values"][0][0]
            elif prop["name"] == "Quality":
                item_quality = prop["values"][0][0]

        return item_level, item_quality

    def extract_gem_experience(self, additional_properties):
        for prop in additional_properties:
            if prop.get("name") == "Experience":
                return prop.get("values", [])[0][0]
        return None

    def extract_data(self):
        extracted_data = []

        for item in self.fetch_listing():
            listing = item.get("listing", {})
            item_info = item.get("item", {})

            item_name = item_info.get("typeLine", "")
            item_properties = item_info.get("properties", [])
            item_corrupted = item_info.get("corrupted", False)
            item_level, item_quality = self.extract_properties(item_properties)
            gem_experience = self.extract_gem_experience(
                item_info.get("additionalProperties", [])
            )

            indexed = listing.get("indexed", "")
            stash_name = listing.get("stash", {}).get("name", "")
            account_name = listing.get("account", {}).get("name", "")
            player_status = (
                listing.get("account", {}).get("online", {}).get("status", "")
            )
            price_amount = listing.get("price", {}).get("amount", "")
            currency = listing.get("price", {}).get("currency", "")

            row = {
                "Item Name": item_name,
                "Item Level": item_level,
                "Item Quality": item_quality,
                "Corrupted": item_corrupted,
                "Experience": gem_experience,
                "Indexed": indexed,
                "Stash Name": stash_name,
                "Account Name": account_name,
                "Player Status": player_status,
                "Price Amount": price_amount,
                "Currency": currency,
                "Updated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            extracted_data.append(row)

        return extracted_data

    def save_data(self):
        df = pd.DataFrame(self.extract_data())
        item_words = self.payload.item_type.split()
        current_working_dir = os.getcwd()
        folder_path = os.path.join(current_working_dir, "data/trade")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(
            folder_path,
            f"{'_'.join(item_words)}_{self.payload.payload_type}.csv",
        )
        df.to_csv(file_path)


class Payload:
    def __init__(
        self,
        payload_type=None,
        status="online",
        item_type="",
        league="Affliction",
        min_quality=None,
        sort_by="price",
        corrupt=None,
        max_gem_level=None,
        min_gem_level=None,
        sort_order="asc",
    ) -> None:
        self.status = status
        self.item_type = item_type
        self.league = league
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.min_quality = min_quality
        self.corrupt = corrupt
        self.max_gem_level = max_gem_level
        self.min_gem_level = min_gem_level
        self.payload_type = payload_type

        match sort_by:
            case "price":
                sort_field = "price"
            case "gem_level":
                sort_field = "gem_level"
            case _:
                sort_field = "price"

        filters = {}

        if self.min_quality is not None or self.corrupt is not None:
            filters["filters"] = {"misc_filters": {"filters": {}}}

            if self.min_quality is not None:
                filters["filters"]["misc_filters"]["filters"]["quality"] = {
                    "min": self.min_quality,
                }

            if self.corrupt is not None:
                filters["filters"]["misc_filters"]["filters"]["corrupted"] = {
                    "option": self.corrupt,
                }

            if self.max_gem_level is not None and self.min_gem_level is not None:
                filters["filters"]["misc_filters"]["filters"]["gem_level"] = {
                    "min": self.min_gem_level,
                    "max": self.max_gem_level,
                }

            if self.max_gem_level is not None:
                filters["filters"]["misc_filters"]["filters"]["gem_level"] = {
                    "max": self.max_gem_level,
                }

            if self.min_gem_level is not None:
                filters["filters"]["misc_filters"]["filters"]["gem_level"] = {
                    "min": self.min_gem_level,
                }

        self.query = {
            "query": {
                "status": {"option": self.status},
                "type": self.item_type,
                "stats": [{"type": "and", "filters": []}],
                **filters,
            },
            "sort": {sort_field: self.sort_order},
        }


class BuySellEntry:

    def __init__(
        self, buy_listings: ListingFetcher, sell_listings: ListingFetcher
    ) -> None:
        self.buy_listings = buy_listings
        self.sell_listings = sell_listings

    def construct_buy_sell_frame(self):

        buy_sell_dict = {}

        buy_data = pd.DataFrame(self.buy_listings.extract_data())
        sell_data = pd.DataFrame(self.sell_listings.extract_data())
        buy_sell_dict["Item Name"] = self.buy_listings.payload.item_type
        buy_sell_dict["Buy"] = buy_data["Price Amount"].mean()
        buy_sell_dict["Sell"] = sell_data["Price Amount"].mean()
        buy_sell_dict["Profit"] = self.calculate_profit(
            buy_sell_dict["Sell"], buy_sell_dict["Buy"]
        )
        buy_sell_dict["Updated At"] = buy_data["Updated At"].max()
        return pd.Series(buy_sell_dict)

    def calculate_profit(self, sell_value, buy_value):
        return sell_value - buy_value

    def save_data(self):

        series = self.construct_buy_sell_frame()
        item_words = self.buy_listings.payload.item_type.split()
        current_working_dir = os.getcwd()
        folder_path = os.path.join(current_working_dir, "data/profit")

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, f"{'_'.join(item_words)}_UI_input.csv")
        series.to_csv(file_path)


def fetch_all_listings(
    listing_item, buy_properties, sell_properties, header, trade_url
):
    entries = []
    for name in listing_item:
        buy_payload = Payload(
            payload_type=buy_properties["payload_type"],
            item_type=name,
            status=buy_properties["status"],
            league=buy_properties["league"],
            min_quality=buy_properties["min_quality"],
            sort_by=buy_properties["sort_by"],
            corrupt=buy_properties["corrupt"],
            max_gem_level=buy_properties["max_gem_level"],
            sort_order=buy_properties["sort_order"],
        )
        sell_payload = Payload(
            payload_type=sell_properties["payload_type"],
            item_type=name,
            status=sell_properties["status"],
            league=sell_properties["league"],
            min_quality=sell_properties["min_quality"],
            sort_by=sell_properties["sort_by"],
            corrupt=sell_properties["corrupt"],
            min_gem_level=sell_properties["min_gem_level"],
            sort_order=sell_properties["sort_order"],
        )
        buy_fetcher = ListingFetcher(trade_url, header, buy_payload)
        sell_fetcher = ListingFetcher(trade_url, header, sell_payload)

        buy_sell_entry = BuySellEntry(
            buy_listings=buy_fetcher, sell_listings=sell_fetcher
        )

        entries.append(buy_sell_entry.construct_buy_sell_frame())

        buy_sell_entry.save_data()  # Save profit frame for UI
        buy_fetcher.save_data()  # Save buy data for potential history
        sell_fetcher.save_data()  # Save sell data for potential history

    print(pd.DataFrame(entries))


def get_oldest_entry(group_name="awakened_gems.csv"):
    current_working_dir = os.getcwd()
    folder_path = os.path.join(current_working_dir, "data/profit")

    file_path = os.path.join(folder_path, group_name)
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path).set_index("Item Name")
    oldest_entry = df["Updated At"].idxmin()

    return oldest_entry
