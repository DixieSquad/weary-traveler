# Software Design Document: The Weary Traveler

## Architectural Design

The Weary Traveler is a python application that shows the user various profit making methods for Path of Exile and their up-to-date margins. The app is build up out of three parts: the user interface (UI), the backend code, and the database. The UI can be used to select different groups of profit making strategies, which show up in a list that is sorted by the most profitable method. The backend code uses the official poe.trade api to update the profit margins according to the PoE market. Market values of each profit method are stored in the database by the backend code and are visualized in the UI.

```mermaid
flowchart
ui(User Interface) --> be{{Backend code}}
db[(Database)] --> ui
be <--> db
```

## High-level Design

The user interface displays a table of profit making methods, which can be refreshed automatically. The user is able to toggle the refresh functionality from the UI. With the refresh toggle enabled, the user interface engages two background processes, one to update the data in the database and another to regularly refresh the UI with the new data. The update Data process calls the backend code periodically to update the oldest entry and store the updated entry in the database.

### High-level flow chart

```mermaid
flowchart

subgraph UI[User Interface]
refr_tog --> refr_ui[refresh UI]
refr_tog --> upd_data[update data]
refr_ui -. loop .-> refr_ui
upd_data -. loop .-> upd_data
end

user(user) --> refr_tog[refresh toggle]

upd_old <--> db
db[(Database)] --o refr_ui

subgraph backend[backend code]
upd_data --> upd_old[update oldest entry]
end

%% styling
classDef subgraphstyle margin-left:4cm
class UI subgraphstyle

```
### High-level sequence diagram

``` mermaid
sequenceDiagram

user ->>+ refresh toggle: Toggle On

box rgb(80,80,80) user interface 
participant refresh toggle
participant update data
participant refresh UI
end

box rgb(80,80,80) backend code 
participant update oldest entry
end

refresh toggle ->> update data: Start processes
refresh toggle ->> refresh UI: 
par
    loop
        database ->> refresh UI: Reload data
    end
and
    loop
        update data ->> update oldest entry: Request update from backend
        database ->> update oldest entry: Get oldest entry
        update oldest entry -->> update oldest entry: update entry
        update oldest entry ->> database: Save updated entry
    end
end

user ->> refresh toggle: Toggle Off
refresh toggle ->> update data: Stop processes
refresh toggle ->>- refresh UI: 
```

## Detailed Design

### User Interface

The user interface is a single window containing a dropdown menu, a button, and a table overview. 
* The dropdown menu can be used to select different groups of profit methods from the database. 
* The button can be used to toggle the automatic update background process. 
* The table overview lists the profit methods with the following fields:
  * Item Name
  * Buy price
  * Sell price
  * Profit
  * Time since last update

### Backend code

The backend code consists of three main parts:
* poe_ninja_scraper.py
  * poe.ninja scraper that supplies the initial Item Names for the Gems profit group.
* poe_trade_rest.py
  * poe.trade api handler that makes the REST calls and updates entries in the database.
* main.py
  * Calls the poe.ninja scraper to get the Gems group Item Names and constructs the initial database.

#### poe_ninja_scraper.py

poe.ninja is a website that shows a list of items and there current estimated value in the Path of Exile market. The scraper takes an url of poe.ninja containing pre-defined filtering properties. For example, the following url can be used to get info about level 5, 20% quality, uncorrupted, awakened, skill gems:
>https://poe.ninja/economy/affliction/skill-gems?level=5&quality=20&corrupted=No&gemType=Awakened

The scraper will fetch the following data: Name, Level, Quality, Corrupt, Value, Last 7 days, # Listed. This data can be saved to a comma separated value.

```mermaid
classDiagram
class poe_ninja_scraper{
    +fetch_data(url)
    +save_data(data)
}
```

#### poe_trade_rest.py

The poe.trade api handler interacts with the poe.trade api to update the current market value for items in Path of Exile. The Weary Traveler uses this api handler to update the buy and sell prices for each profit method entry periodically.

#### Class diagram for poe_trade_rest.py

```mermaid
classDiagram
class poe_trade_rest{
    +fetch_all_listings(listing_item, buy_properties, sell_properties)
    +update_oldest_entry()
    +get_oldest_entry(group_name) String
    +get_gem_buy_sell_properties() Dict~buy: buy_properties, sell: sell_properties~
}

class BuySellEntry{
    +ListingFetcher buy_listings
    +ListingFetcher sell_listings
    +update_csv()
    +construct_buy_sell_frame() pd.Series
    +convert_chaos_to_divine(data) pd.DataFrame
    +calculate_profit(sell_value, buy_value) float
}

class Payload{
    +String payload_type
    +String status
    +String item_type
    +String league
    +int min_quality
    +String sort_by
    +bool corrupt
    +int max_gem_level
    +int min_gem_level
    +String sort_order
    +Dict query
}

class ListingFetcher{
    -String trade_url
    -Dict header
    -datetime last_query_time
    +Payload payload
    +fetch_listing() Dict
    +extract_properties(item_properties) List~item_level, item_quality~
    +extract_gem_experience(additional_properties) int
    +extract_data() List~Dict~
    +save_data()
}

BuySellEntry --|> ListingFetcher : Dependency
ListingFetcher --|> Payload : Dependency
```

The calls to the poe.trade api are made by: 
1. Constructing a trade query using the Payload class, which takes the properties of the buy and sell items in question and converts these to poe.trade queries.
2. Create a ListingFetcher from each Payload
3. Create a BuySellEntry from both buy and sell ListingFetchers

### Database

The database is represented as a collection of comma separated value files, each file storing the information of all entries within a profit method group. Each entry corrosponds with one line in the .csv file and consists of the following information:
* (string) Item Name
* (float) Buy price
* (float) Sell price
* (float) Profit
* (datetime as text) Time of last update

The time of last update is stored as text with the following format: 2024-03-20 21:22:29.