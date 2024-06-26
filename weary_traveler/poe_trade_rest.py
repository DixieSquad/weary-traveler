import dataclasses
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import poe_ninja_scraper as poe_ninja_scraper
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
        self.number_listed = 0
        self.result_id = ""

    @staticmethod
    def build_query(item_name, modifiers):

        filters = {
            "filters": {
                "trade_filters": {"filters": {"price": {"option": "chaos_divine"}}}
            }
        }

        if "min_quality" in modifiers or "corrupted" in modifiers:
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
            Fetcher._last_query_time = datetime.now()
            r = requests.post(self._trade_url, headers=self._header, json=self.query)
            r.raise_for_status()
            self.number_listed: int = r.json().get("total", 0)
            result = r.json().get("result", [])[:10]
            self.result_id = r.json().get("id", "")
            text_result = ",".join(result)
            fetch_url = f"https://www.pathofexile.com/api/trade/fetch/{text_result}?query={self.result_id}"
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
    item_name: str
    modifiers: dict[str, Any]
    url: str = ""
    value: float = 0
    number_listed: int = 0
    updated_at: datetime = datetime(1, 1, 1, 0, 0, 0, 1)

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

        self.value = round(price_mean, 1)
        self.updated_at = datetime.now()
        self.number_listed = fetcher.number_listed
        self.url = f"https://www.pathofexile.com/trade/search/Necropolis/{fetcher.result_id}"


@dataclass
class ProfitStrat:
    item_name: str
    buy_item: ItemEntry
    sell_item: ItemEntry
    profit: float = 0

    def __post_init__(self) -> None:
        if isinstance(self.buy_item, dict):
            self.buy_item = ItemEntry(**self.buy_item)
        if isinstance(self.sell_item, dict):
            self.sell_item = ItemEntry(**self.sell_item)

        if self.sell_item.value > 0 and self.buy_item.value > 0:
            self.profit = round(self.sell_item.value - self.buy_item.value, 1)
        else:
            self.profit = 0

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ProfitStrat)
            and self.buy_item == other.buy_item
            and self.sell_item == other.sell_item
        )


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class DataHandler:
    def __init__(self) -> None:
        current_working_dir = os.getcwd()
        item_folder_path = os.path.join(current_working_dir, "data/item_entries")
        self.item_entry_file = os.path.join(item_folder_path, "awakened_gems.json")

        profit_folder_path = os.path.join(current_working_dir, "data/profit_strats")
        self.profit_strat_file = os.path.join(profit_folder_path, "awakened_gems.json")

        # ensure the directory exists, no error is raised if it does.
        os.makedirs(item_folder_path, exist_ok=True)
        os.makedirs(profit_folder_path, exist_ok=True)

        # check if item entry file exists
        if not os.path.exists(self.item_entry_file):
            with open(self.item_entry_file, "w") as json_file:
                json.dump({}, json_file)
        # check if profit strat file exists
        if not os.path.exists(self.profit_strat_file):
            with open(self.profit_strat_file, "w") as json_file:
                json.dump({}, json_file)

    def write_profit_strat(self, profit_strat: ProfitStrat) -> None:
        strats = []
        # The rest is basically the same as write_item_entry
        with open(self.profit_strat_file, "r") as f:
            data = json.load(f)
            for s in data:
                strat = ProfitStrat(**s)
                strats.append(strat)

        if profit_strat in strats:
            strats[strats.index(profit_strat)] = profit_strat
        else:
            strats.append(profit_strat)

        with open(self.profit_strat_file, "w") as f:
            strats = [strat.__dict__ for strat in strats]
            json.dump(strats, f, cls=EnhancedJSONEncoder)

    def write_item_entry(self, item_entry: ItemEntry) -> None:
        items = self.read_all_item_entries()

        if item_entry in items:
            items[items.index(item_entry)] = item_entry
        else:
            items.append(item_entry)

        with open(self.item_entry_file, "w") as f:
            items = [item.__dict__ for item in items]
            json.dump(items, f, default=str)

    def read_all_item_entries(self) -> list[ItemEntry]:
        items = []
        with open(self.item_entry_file, "r") as f:
            data = json.load(f)
            for i in data:
                item = ItemEntry(**i)
                items.append(item)
        return items

    def get_item_entries_by_item_name(self, item_name: str) -> list[ItemEntry]:
        items = self.read_all_item_entries()
        items = [item for item in items if item.item_name == item_name]
        return items

    def read_all_profit_strats(self) -> list[ProfitStrat]:
        strats: list[ProfitStrat] = []
        with open(self.profit_strat_file, "r") as f:
            data = json.load(f)
            for i in data:
                strat = ProfitStrat(**i)
                strats.append(strat)
        return strats

    def get_profit_strats_by_item_name(self, item_name: str) -> list[ProfitStrat]:
        strats = self.read_all_profit_strats()
        strats = [strat for strat in strats if strat.buy_item.item_name == item_name]
        return strats

    def get_oldest_item_entry(self) -> ItemEntry:
        items = self.read_all_item_entries()
        oldest = items.pop()
        for item in items:
            if item.updated_at < oldest.updated_at:
                oldest = item
        return oldest

    def update_oldest_item_entry(self) -> None:
        item = self.get_oldest_item_entry()
        item.get_value_from_trade()
        self.write_item_entry(item)
        self.update_profit_strats(item.item_name)

    def initialize_item_entries(
        self, item_names: list[str], modifiers_list: list[dict[str, Any]]
    ) -> None:
        for item_name in item_names:
            for modifiers in modifiers_list:
                item_entry = ItemEntry(item_name=item_name, modifiers=modifiers)
                self.write_item_entry(item_entry)

    def update_profit_strats(self, item_name: str) -> None:
        item_entries = self.get_item_entries_by_item_name(item_name=item_name)
        for buy in item_entries:
            for sell in item_entries:
                if sell.value >= buy.value and sell.modifiers != buy.modifiers:
                    profit_strat = ProfitStrat(item_name, buy_item=buy, sell_item=sell)
                    self.write_profit_strat(profit_strat)

    def initialize_from_ninja(self, group: str) -> None:
        if group == "Awakened Gems":
            poe_ninja_url = "https://poe.ninja/economy/affliction/skill-gems?level=5&quality=20&corrupted=No&gemType=Awakened"
            modifiers = [
                {"max_gem_level": 1, "corrupted": "false"},
                {"min_gem_level": 5, "corrupted": "false", "min_quality": 20},
            ]
        else:
             raise NotImplementedError(f"This group: '{group}' is not implemented yet")

        item_names = poe_ninja_scraper.fetch_data(poe_ninja_url)

        self.initialize_item_entries(item_names=item_names, modifiers_list=modifiers)

        for item_name in item_names:
            self.update_profit_strats(item_name)
