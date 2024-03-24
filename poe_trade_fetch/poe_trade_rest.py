import os
import time
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


class ListingFetcher:
    _trade_url = "https://www.pathofexile.com/api/trade/search/Affliction"
    _header = {"user-agent": str(os.getenv("EMAIL"))}
    _last_query_time = datetime(2024, 1, 1, 00, 00, 00)

    def __init__(self, payload) -> None:
        self.payload = payload

    def fetch_listing(self) -> pd.DataFrame:
        seconds_since_last_query = (datetime.now() - self._last_query_time).seconds

        while seconds_since_last_query < 10:
            time.sleep(10 - seconds_since_last_query)
            seconds_since_last_query = (datetime.now() - self._last_query_time).seconds

        try:
            r = requests.post(
                self._trade_url, headers=self._header, json=self.payload.query
            )
            r.raise_for_status()
            result = r.json().get("result", [])[:10]
            result_id = r.json().get("id", "")
            text_result = ",".join(result)
            fetch_url = f"https://www.pathofexile.com/api/trade/fetch/{text_result}?query={result_id}"
            listings = requests.get(fetch_url, headers=self._header)
            r.raise_for_status()
            listing_results = listings.json().get("result", [])
            ListingFetcher._last_query_time = datetime.now()

            extracted_data = self.extract_data(listing_results)

            return pd.DataFrame(extracted_data)
        except requests.RequestException as e:
            print("Error: ", e)
            return pd.DataFrame()

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

    def extract_data(self, listing_results: list[dict]) -> list[dict]:
        extracted_data = []

        for item in listing_results:
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
        sort_by=None,
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

        sort_field = (
            "price"
            if sort_by
            not in [
                "price",
                "gem_level",
                "quality",
                "indexed",
                "gem_level_progress",
                "lvl",
                "int",
                "str",
                "dex",
            ]
            else sort_by
        )

        filters = {
            "filters": {
                "trade_filters": {"filters": {"price": {"option": "chaos_divine"}}}
            }
        }

        if self.min_quality is not None or self.corrupt is not None:
            filters["filters"]["misc_filters"] = {"filters": {}}

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
        self, name: str, buy_data: pd.DataFrame, sell_data: pd.DataFrame
    ) -> None:

        buy_sell_dict = {}
        self.item_name = name

        if buy_data.empty:
            self.buy_value = None
        else:
            buy_data = buy_data.astype({"Price Amount": float})
            buy_data = self.convert_chaos_to_divine(buy_data)
            self.buy_value = round(buy_data["Price Amount"].mean(), 1)

        if sell_data.empty:
            self.sell_value = None
        else:
            sell_data = sell_data.astype({"Price Amount": float})
            sell_data = self.convert_chaos_to_divine(sell_data)
            self.sell_value = round(sell_data["Price Amount"].mean(), 1)

        if buy_data.empty or sell_data.empty:
            self.profit = None
        else:
            self.profit = round(
                self.calculate_profit(self.sell_value, self.buy_value), 1
            )

        self.update_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def convert_chaos_to_divine(self, data):
        data.loc[data["Currency"] == "chaos", "Price Amount"] = (
            data.loc[data["Currency"] == "chaos", "Price Amount"] / 128
        )
        return data

    def calculate_profit(self, sell_value, buy_value):
        return sell_value - buy_value

    def update_csv(self):
        entry = self.to_dataframe()

        current_working_dir = os.getcwd()
        file_path = os.path.join(
            current_working_dir, "data/profit", "awakened_gems.csv"
        )

        # ensure the directory exists, no error is raised if it does.
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # check if file exists
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col="Item Name")
            # match datatypes of entry_df and file
            entry = entry.astype(df.dtypes)
            # combines per value basis not rows. If new value doesn't exist, keep old value.
            df = entry.combine_first(df)
        else:
            df = entry

        df.to_csv(file_path)

    def to_dataframe(self) -> pd.DataFrame:
        d = {
            "Item Name": self.item_name,
            "Buy": self.buy_value,
            "Sell": self.sell_value,
            "Profit": self.profit,
            "Updated At": self.update_at,
        }
        df = pd.DataFrame(d, index=[0])
        df.set_index("Item Name", inplace=True)

        return df


def fetch_all_listings(listing_item, buy_properties, sell_properties):
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
        buy_fetcher = ListingFetcher(buy_payload)
        sell_fetcher = ListingFetcher(sell_payload)

        buy_data = buy_fetcher.fetch_listing()
        sell_data = sell_fetcher.fetch_listing()

        buy_sell_entry = BuySellEntry(name, buy_data, sell_data)
        buy_sell_entry.update_csv()  # Save profit frame for UI
        # buy_fetcher.save_data()  # Save buy data for potential history
        # sell_fetcher.save_data()  # Save sell data for potential history


def get_oldest_entry(group_name="awakened_gems.csv"):
    current_working_dir = os.getcwd()
    folder_path = os.path.join(current_working_dir, "data/profit")

    file_path = os.path.join(folder_path, group_name)
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path).set_index("Item Name")

    oldest_entry = df["Updated At"].idxmin()

    return oldest_entry


def get_gem_buy_sell_properties():
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

    return {"buy": buy_properties, "sell": sell_properties}


def update_oldest_entry():
    fetch_all_listings(
        [get_oldest_entry()],
        get_gem_buy_sell_properties()["buy"],
        get_gem_buy_sell_properties()["sell"],
    )
