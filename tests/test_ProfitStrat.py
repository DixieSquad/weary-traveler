from typing import Any
import pytest
from weary_traveler.poe_trade_rest import DataHandler, ItemEntry, ProfitStrat


class ItemEntryFactory:
    def get(self, mods: dict[str, Any] = {}, value: float = 0) -> ItemEntry:
        item_entry = ItemEntry(item_name="test_item", modifiers=mods, value=value)
        return item_entry


@pytest.fixture
def item_entry() -> ItemEntryFactory:
    return ItemEntryFactory()


def test_ProfitStrat_valid(item_entry) -> None:
    buy_entry: ItemEntry = item_entry.get(value=1, mods={"test": 1})
    sell_entry: ItemEntry = item_entry.get(value=2, mods={"test": 1})
    profit_strat = ProfitStrat(
        buy_entry.item_name, buy_item=buy_entry, sell_item=sell_entry
    )
    assert profit_strat.isvalid() == True


def test_ProfitStrat_invalid_value(item_entry) -> None:
    buy_entry: ItemEntry = item_entry.get(value=2, mods={"test": 2})
    sell_entry: ItemEntry = item_entry.get(value=1, mods={"test": 3})
    profit_strat = ProfitStrat(
        buy_entry.item_name, buy_item=buy_entry, sell_item=sell_entry
    )
    assert profit_strat.isvalid() == False


def test_ProfitStrat_invalid_mods(item_entry) -> None:
    mods = {"test1": 1, "test2": 2}
    buy_entry: ItemEntry = item_entry.get(mods=mods)
    sell_entry: ItemEntry = item_entry.get(mods=mods)
    profit_strat = ProfitStrat(
        buy_entry.item_name, buy_item=buy_entry, sell_item=sell_entry
    )
    assert profit_strat.isvalid() == False


def test_ProfitStrat_invalid_corrupt(item_entry) -> None:
    buy_entry: ItemEntry = item_entry.get(mods={"corrupted": "true"})
    sell_entry: ItemEntry = item_entry.get(mods={"corrupted": "false"})
    profit_strat = ProfitStrat(
        buy_entry.item_name, buy_item=buy_entry, sell_item=sell_entry
    )
    assert profit_strat.isvalid() == False


def test_ProfitStrat_valid_corrupt(item_entry) -> None:
    buy_entry: ItemEntry = item_entry.get(value=1, mods={"corrupted": "false"})
    sell_entry: ItemEntry = item_entry.get(value=2, mods={"corrupted": "true"})
    profit_strat = ProfitStrat(
        buy_entry.item_name, buy_item=buy_entry, sell_item=sell_entry
    )
    assert profit_strat.isvalid() == True
