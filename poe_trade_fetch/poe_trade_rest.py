import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self

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
    def extract_listings(response: requests.Response) -> list[Listing]:
        results = response.json().get("result", [])
        listings = []
        for result in results:
            price_info = result.get("listing", {}).get("price", {})
            price_amount = price_info.get("amount", "")
            currency = price_info.get("currency", "")
            listings.append(Listing(price=price_amount, currency=currency))
        return listings


@dataclass
class ItemEntry:
    id: int
    item_name: str
    modifiers: dict[str, Any]
    url: str
    value: float
    number_listed: int
    updated_at: datetime

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ItemEntry)
            and self.item_name == other.item_name
            and self.modifiers == other.modifiers
        )

    def mods_to_str(self) -> str:
        mod_str = ""
        for key, value in self.modifiers.items():
            line = f"{key}: {value}"
            if mod_str == "":
                mod_str = line
            else:
                mod_str = "\n".join([mod_str, line])

        return mod_str

    def get_value_from_trade(self) -> None:
        fetcher = Fetcher(self.item_name, self.modifiers)
        fetcher.fetch()

        if fetcher.listings == []:
            return

        price_sum = 0.0
        for listing in fetcher.listings:
            price_sum += listing.price

        price_mean = price_sum / len(fetcher.listings)

        self.value = price_mean
        self.updated_at = datetime.now()


@dataclass
class ProfitStrat:
    id: int
    item_name: str
    buy_item: ItemEntry
    sell_item: ItemEntry
    profit: float

    def __post_init__(self):
        self.profit = self.sell_item.value - self.buy_item.value


class DataHandler:
    def __init__(self) -> None:
        current_working_dir = os.getcwd()
        folder_path = os.path.join(current_working_dir, "data/item_entries")
        self.item_entry_file = os.path.join(folder_path, "awakened_gems.json")

        # ensure the directory exists, no error is raised if it does.
        os.makedirs(folder_path, exist_ok=True)

        # check if file exists
        if not os.path.exists(self.item_entry_file):
            with open(self.item_entry_file, "w") as json_file:
                json.dump({}, json_file)

    def write_profit_strat(self, buy: ItemEntry, sell: ItemEntry):
        pass

    def write_item_entry(self, item_entry: ItemEntry):
        items = []
        with open(self.item_entry_file, "r") as f:
            data = json.load(f)
            for i in data:
                item = ItemEntry(**i)
                items.append(item)

        if item_entry in items:
            items[items.index(item_entry)] = item_entry
        else:
            items.append(item_entry)

        with open(self.item_entry_file, "w") as f:
            json.dump(items, f, default=str)

    def read_profit_entry(self, item_name: str, modifiers: dict[str, Any]):
        pass


def get_oldest_entry(group_name="awakened_gems.csv"):
    current_working_dir = os.getcwd()
    folder_path = os.path.join(current_working_dir, "data/profit")

    file_path = os.path.join(folder_path, group_name)
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path).set_index("Item Name")

    oldest_entry = df["Updated At"].idxmin()

    return oldest_entry
