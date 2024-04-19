import pytest
from poe_trade_fetch.poe_trade_rest import DataHandler, ItemEntry
from datetime import datetime, timedelta
import os
import shutil


@pytest.fixture()
def prep_and_clean_data():
    data_folder = "data"
    item_folder = "data/item_entries"
    profit_folder = "data/profit_strats"
    filename = "awakened_gems.json"

    print("Setting up test data folders")
    os.mkdir(data_folder)
    os.mkdir(item_folder)
    os.mkdir(profit_folder)
    yield
    print("Removing test data folders")
    shutil.rmtree("data")


@pytest.fixture
def item_entry() -> ItemEntry:
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


class TestItemEntry:
    def test_item_entry_equals(self, item_entry) -> None:
        assert item_entry == item_entry

    def test_item_entry_not_equals(self, item_entry) -> None:
        item_entry2 = ItemEntry(**item_entry.__dict__)
        item_entry2.item_name = "test2"
        item_entry2.modifiers = {"mod1": 2}
        print(item_entry)
        assert item_entry != item_entry2


class TestDataHandler:
    @pytest.fixture
    def datahandler(self, prep_and_clean_data) -> DataHandler:
        return DataHandler()

    def test_saving_and_loading_json(self, item_entry, datahandler) -> None:
        item_entry = item_entry
        datahandler.write_item_entry(item_entry=item_entry)
        item_entries = datahandler.read_all_item_entries()
        assert item_entry in item_entries

    def test_get_oldest_entry_last(self, item_entry, datahandler) -> None:
        item_entry1 = ItemEntry(**item_entry.__dict__)
        item_entry2 = ItemEntry(**item_entry.__dict__)
        item_entry2.item_name = "test2"
        item_entry2.updated_at = datetime.now() - timedelta(days=1)
        datahandler.write_item_entry(item_entry1)
        datahandler.write_item_entry(item_entry2)

        item = datahandler.get_oldest_entry()
        assert item == item_entry2 and item != item_entry1

    def test_get_oldest_entry_first(self, item_entry, datahandler) -> None:
        item_entry1 = ItemEntry(**item_entry.__dict__)
        item_entry2 = ItemEntry(**item_entry.__dict__)
        item_entry1.item_name = "test2"
        item_entry1.updated_at = datetime.now() - timedelta(days=1)
        datahandler.write_item_entry(item_entry1)
        datahandler.write_item_entry(item_entry2)

        item = datahandler.get_oldest_entry()
        assert item == item_entry1 and item != item_entry2
