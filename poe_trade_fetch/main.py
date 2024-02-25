import poe_ninja_scraper
import poe_trade_rest
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL")

working_dir = os.getcwd()
trade_data_path = os.path.join(working_dir, "data/trade")
ninja_data_path = os.path.join(working_dir, "data/ninja")

trade_files = os.listdir(trade_data_path)
ninja_file = os.path.join(ninja_data_path, "poe_ninja_data.csv")
poe_ninja_df = pd.read_csv(ninja_file)

buy_properties = {
    "status": "online",
    "league": "Affliction",
    "min_quality": None,
    "sort_by": "price",
    "corrupt": "false",
    "max_gem_level": 1,
    "sort_order": "asc",
}
sell_properties = {
    "status": "online",
    "league": "Affliction",
    "min_quality": 20,
    "sort_by": "price",
    "corrupt": "false",
    "min_gem_level": 5,
    "sort_order": "asc",
}
gems = ["Awakened Spell Echo Support", "Awakened Multistrike Support"]
trade_url = "https://www.pathofexile.com/api/trade/search/Affliction"
header = {"user-agent": str(EMAIL_ADDRESS)}
poe_ninja_url = "https://poe.ninja/economy/skill-gems"

# poe_trade_rest.fetch_all_listings(gems, buy_properties, header, trade_url)
# poe_trade_rest.fetch_all_listings(gems, sell_properties, header, trade_url)

# poe_ninja_df = poe_ninja_scraper.fetch_data(poe_ninja_url)

# if there is other files than .csv files in the folder:
# csv_files = [file for file in files if file.endswith('.csv')]


def read_gem_files(trade_files):
    dataframes = {}

    for csv_file in trade_files:
        file_path = os.path.join(trade_data_path, csv_file)
        df = pd.read_csv(file_path, index_col=0)
        dataframes[csv_file] = df
    return dataframes


def construct_buy_sell_frame(dataframes):
    items = {}

    for file_name, df in dataframes.items():
        if file_name.endswith("1.csv"):
            if df["Item Name"].iloc[0] in items:
                items[df["Item Name"].iloc[0]]["Buy"] = round(
                    df["Price Amount"].mean(), 2
                )
            else:
                items[df["Item Name"].iloc[0]] = {}
                items[df["Item Name"].iloc[0]]["Buy"] = round(
                    df["Price Amount"].mean(), 2
                )
        elif file_name.endswith("5.csv"):
            if df["Item Name"].iloc[0] in items:
                items[df["Item Name"].iloc[0]]["Sell"] = round(
                    df["Price Amount"].mean(), 2
                )
            else:
                items[df["Item Name"].iloc[0]] = {}
                items[df["Item Name"].iloc[0]]["Sell"] = round(
                    df["Price Amount"].mean(), 2
                )
        else:
            continue
    return items


def calculate_profit(items):
    for _, values in items.items():
        values["Profit"] = round(values["Sell"] - values["Buy"], 2)

    df = pd.DataFrame(items)

    df = df.T  # Transposes Dataframe

    print(df)


gem_files = read_gem_files(trade_files)
buy_sell_frame = construct_buy_sell_frame(gem_files)

calculate_profit(buy_sell_frame)
