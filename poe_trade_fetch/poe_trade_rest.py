import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Listing:
    price: float
    currency: str

    def __post_init__(self) -> None:
        if self.currency == "chaos":
            self.price = self.price / 120.0
            self.currency = "divine"


class Fetcher:
    _trade_url = "https://www.pathofexile.com/api/trade/search/Necropolis"
    _header = {"user-agent": str(os.getenv("EMAIL"))}
    _last_query_time = datetime(2024, 1, 1, 00, 00, 00)

    def __init__(self, item_name: str, modifiers: dict[str, Any]) -> None:
        self.item_name = item_name
        self.modifiers = modifiers
        self.query = Fetcher.build_query(item_name, modifiers)
        self.listings = []
        self.number_listed = None

    @staticmethod
    def build_query(item_name, modifiers):

        filters = {
            "filters": {
                "trade_filters": {"filters": {"price": {"option": "chaos_divine"}}}
            }
        }

        if "min_quality" in modifiers or "corrupt" in modifiers:
            filters["filters"]["misc_filters"] = {"filters": {}}

            if "min_quality" in modifiers:
                filters["filters"]["misc_filters"]["filters"]["quality"] = {
                    "min": modifiers["min_quality"],
                }

            if "corrupted" in modifiers:
                filters["filters"]["misc_filters"]["filters"]["corrupted"] = {
                    "option": modifiers["corrupted"],
                }

            if "max_gem_level" in modifiers and "min_gem_level" in modifiers:
                filters["filters"]["misc_filters"]["filters"]["gem_level"] = {
                    "min": modifiers["min_gem_level"],
                    "max": modifiers["max_gem_level"],
                }

            if "max_gem_level" in modifiers:
                filters["filters"]["misc_filters"]["filters"]["gem_level"] = {
                    "max": modifiers["max_gem_level"],
                }

            if "min_gem_level" in modifiers:
                filters["filters"]["misc_filters"]["filters"]["gem_level"] = {
                    "min": modifiers["min_gem_level"],
                }

        query = {
            "query": {
                "status": {"option": "online"},
                "type": item_name,
                "stats": [{"type": "and", "filters": []}],
                **filters,
            },
            "sort": {"price": "asc"},
        }

        return query

    def fetch(self) -> None:
        seconds_since_last_query = (datetime.now() - self._last_query_time).seconds
        while seconds_since_last_query < 10:
            time.sleep(10 - seconds_since_last_query)
            seconds_since_last_query = (datetime.now() - self._last_query_time).seconds

        try:
            r = requests.post(self._trade_url, headers=self._header, json=self.query)
            r.raise_for_status()
            self.number_listed = r.json().get("total", 0)
            result = r.json().get("result", [])[:10]
            result_id = r.json().get("id", "")
            text_result = ",".join(result)
            fetch_url = f"https://www.pathofexile.com/api/trade/fetch/{text_result}?query={result_id}"
            response = requests.get(fetch_url, headers=self._header)
            response.raise_for_status()

            self.listings = self.extract_listings(response)

        except requests.RequestException as e:
            print("Error: ", e)

    @staticmethod
    def extract_listings(response: requests.Response) -> List[Listing]:
        results = response.json().get("result", [])
        listings = []
        for result in results:
            price_info = result.get("listing", {}).get("price", {})
            price_amount = price_info.get("amount", "")
            currency = price_info.get("currency", "")
            listings.append(Listing(price=price_amount, currency=currency))
        return listings


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


def update_all_listings(listing_item, buy_properties, sell_properties):
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
        "league": "Necropolis",
        "min_quality": None,
        "sort_by": "price",
        "corrupt": "false",
        "max_gem_level": 1,
        "sort_order": "asc",
    }
    sell_properties = {
        "payload_type": "sell",
        "status": "online",
        "league": "Necropolis",
        "min_quality": 20,
        "sort_by": "price",
        "corrupt": "false",
        "min_gem_level": 5,
        "sort_order": "asc",
    }

    return {"buy": buy_properties, "sell": sell_properties}


def update_oldest_entry():
    update_all_listings(
        [get_oldest_entry()],
        get_gem_buy_sell_properties()["buy"],
        get_gem_buy_sell_properties()["sell"],
    )
