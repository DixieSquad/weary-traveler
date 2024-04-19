import pytest
from poe_trade_fetch.poe_trade_rest import DataHandler, ItemEntry
from datetime import datetime


@pytest.fixture
def item_entry1() -> ItemEntry:
    item_entry = ItemEntry(
        id=1,
        item_name="test1",
        modifiers={"mod1": 1},
        url="test_url",
        value=12.3,
        number_listed=12,
        updated_at=datetime.now(),
    )
    return item_entry


@pytest.fixture
def item_entry2() -> ItemEntry:
    item_entry = ItemEntry(
        id=1,
        item_name="test2",
        modifiers={"mod1": 2},
        url="test_url",
        value=12.3,
        number_listed=12,
        updated_at=datetime.now(),
    )
    return item_entry


def test_saving_and_loading_json(item_entry1) -> None:
    dataHandler = DataHandler()
    item_entry = item_entry1
    dataHandler.write_item_entry(item_entry=item_entry)
    item_entries = dataHandler.read_all_item_entries()
    assert item_entry1 in item_entries


def test_item_entry_equals(item_entry1) -> None:
    assert item_entry1 == item_entry1


def test_item_entry_not_equals(item_entry1, item_entry2) -> None:
    assert item_entry1 != item_entry2
