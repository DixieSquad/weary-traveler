import pytest
from poe_trade_fetch.poe_trade_rest import DataHandler, ItemEntry, ProfitStrat
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
        item_name="test1",
        modifiers={"mod1": 1},
        url="test_url",
        value=12.3,
        number_listed=12,
        updated_at=datetime.now(),
    )
    return item_entry


@pytest.fixture
def profit_strat(item_entry) -> ProfitStrat:
    buy_entry = ItemEntry(**item_entry.__dict__)
    sell_entry = ItemEntry(**item_entry.__dict__)
    sell_entry.modifiers = {"mod1": 100}
    sell_entry.value = 100
    profit_strat = ProfitStrat(buy_entry.item_name, buy_entry, sell_entry)
    return profit_strat


class TestItemEntry:
    def test_item_entry_equals(self, item_entry: ItemEntry) -> None:
        assert item_entry == item_entry

    def test_item_entry_not_equals(self, item_entry: ItemEntry) -> None:
        item_entry2 = ItemEntry(**item_entry.__dict__)
        item_entry2.item_name = "test2"
        item_entry2.modifiers = {"mod1": 2}
        print(item_entry)
        assert item_entry != item_entry2


class TestDataHandler:
    @pytest.fixture
    def datahandler(self, prep_and_clean_data: None) -> DataHandler:
        return DataHandler()

    @pytest.fixture
    def setup_entries(
        self, datahandler: DataHandler, profit_strat: ProfitStrat
    ) -> None:
        datahandler.write_item_entry(profit_strat.buy_item)
        datahandler.write_item_entry(profit_strat.sell_item)

    def test_saving_and_loading_json(
        self, item_entry: ItemEntry, datahandler: DataHandler
    ) -> None:
        item_entry = item_entry
        datahandler.write_item_entry(item_entry=item_entry)
        item_entries = datahandler.read_all_item_entries()
        assert item_entry in item_entries

    def test_get_oldest_entry_last(
        self, item_entry: ItemEntry, datahandler: DataHandler
    ) -> None:
        item_entry1 = ItemEntry(**item_entry.__dict__)
        item_entry2 = ItemEntry(**item_entry.__dict__)
        item_entry2.item_name = "test2"
        item_entry2.updated_at = datetime.now() - timedelta(days=1)
        datahandler.write_item_entry(item_entry1)
        datahandler.write_item_entry(item_entry2)

        item = datahandler.get_oldest_entry()
        assert item == item_entry2 and item != item_entry1

    def test_get_oldest_entry_first(
        self, item_entry: ItemEntry, datahandler: DataHandler
    ) -> None:
        item_entry1 = ItemEntry(**item_entry.__dict__)
        item_entry2 = ItemEntry(**item_entry.__dict__)
        item_entry1.item_name = "test2"
        item_entry1.updated_at = datetime.now() - timedelta(days=1)
        datahandler.write_item_entry(item_entry1)
        datahandler.write_item_entry(item_entry2)

        item = datahandler.get_oldest_entry()
        assert item == item_entry1 and item != item_entry2

    def test_initialize_single_item_entry(
        self, item_entry: ItemEntry, datahandler: DataHandler
    ) -> None:
        item_name = item_entry.item_name
        modifiers = item_entry.modifiers
        datahandler.initialize_item_entries(
            item_names=[item_name], modifiers_list=[modifiers]
        )
        item_entries = datahandler.read_all_item_entries()
        assert item_entry in item_entries

    def test_initialize_multiple_item_entries(
        self, item_entry: ItemEntry, datahandler: DataHandler
    ) -> None:
        item_entry1 = ItemEntry(**item_entry.__dict__)
        item_entry2 = ItemEntry(**item_entry.__dict__)
        item_entry2.item_name = "test2"
        item_names = [item_entry1.item_name, item_entry2.item_name]
        modifiers = [item_entry1.modifiers, item_entry2.modifiers]
        datahandler.initialize_item_entries(
            item_names=item_names, modifiers_list=modifiers
        )
        item_entries = datahandler.read_all_item_entries()
        assert item_entry1 in item_entries and item_entry2 in item_entries

    def test_update_profit_strats(
        self, setup_entries, datahandler: DataHandler, profit_strat: ProfitStrat
    ):
        datahandler.update_profit_strats(profit_strat.buy_item.item_name)
        profit_strats = datahandler.read_profit_strats(profit_strat.buy_item.item_name)
        assert profit_strat in profit_strats
