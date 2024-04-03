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
### High-level sequence diagram of the UI background process

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

### Current data flow
```mermaid
flowchart LR
db[("`Database 
_BuySellEntries_ 
(UI ready)`")] --> |oldest| get_old[extract buy/sell<br/>properties]

get_old --> |buy| convert_buy[convert to Payload]
get_old --> |sell| convert_sell[convert to Payload]
convert_buy --> construct_buy[construct Fetcher]
convert_sell --> construct_sell[construct Fetcher]
construct_buy --> fetch_buy[fetch]
construct_sell --> fetch_sell[fetch]
fetch_buy --> |buy| combine[combine into BuySellEntry]
fetch_sell --> |sell| combine

combine --> |update| db2[("`Database 
_BuySellEntries_
(UI ready)`")]

```

### Data flow in v0.2.0
```mermaid
flowchart LR
db[("`Database 
_entries_
(buy and sell 
on different lines)`")] --> |oldest| get_old[extract <br/>properties]

get_old --> convert["build query (Payload)"]
convert --> construct[construct Fetcher]
construct --> fetch

fetch --> |update| db2[("`Database 
_entries_
(buy and sell 
on different lines)`")]
```
The above design of the database requires a converter to create usable User Interface input:

```mermaid
flowchart TB
db[("`Database 
_entries_
(buy and sell 
on different lines)`")] --> group[group buy and sell queries by item name]

subgraph converter
    group --> create[create BuySellEntry for each buy/sell combination]
end

create --> db2[("`Database 
_BuySellEntries_
(UI ready)`")]

%% styling
classDef subgraphstyle margin-right:3cm
class converter subgraphstyle
```

### The two databases will have different structures:

'entries' database example for the 'Gems' profit method group:

|Item Name          |Modifiers                                            |Value|# Listed|Last updated       |
|-------------------|-----------------------------------------------------|----:|-------:|-------------------|
|Awakened Spell Echo|{Level: 0,<br>XP: 20m,<br>Quality: 0,<br>Corrupt: No}|6.4  |23      |2024-03-03 22:05:46|
|Awakened Spell Echo|{Level: 0,<br>XP: 20m,<br>Quality: 0,<br>Corrupt: No}|12.3 |12      |2024-03-03 22:05:46|
|...                |...                                                  |...  |...     |...                |

'entries' database example for the 'Flasks' profit method group:

|Item Name          |Modifiers                                        |Value|# Listed|Last updated       |
|-------------------|-------------------------------------------------|----:|-------:|-------------------|
|Ruby Flask         |{ilvl:84,<br>Prefix: None,<br>Suffix: None,<br>Quality: 0,<br>Enchant: None}|0.04 |100      |2024-03-03 22:05:46|
|Ruby Flask         |{ilvl:84,<br>Prefix: 25% Increase Effect,<br>Suffix: 5% life regen,<br>Quality: 0,<br>Enchant: None}|0.8 |9      |2024-03-03 22:05:46|
|...                |...                                              |...  |...     |... |

'BuySellEntries' database example for the 'Gems' profit method group:

|Item Name|Buy mods|Buy price|Sell mods|Sell price|Profit|Last updated|
|--|--|--|--|--|--|--|
|Awakened Spell Echo|lvl:0, Q:0%, Corrupt:No|12.3|lvl:5, Q:20%, Corrupt:No|23.4|11.1|2024-03-03 22:05:46|
|...|...|...|...|...|...|...|


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

## v0.1.x

### Class diagram for poe_trade_rest.py

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

### Sequence to update the oldest entry

The calls to the poe.trade api are made by: 
1. Constructing a trade query using the Payload class, which takes the properties of the buy and sell items in question and converts these to poe.trade queries.
2. Create a ListingFetcher from each Payload.
3. Create a BuySellEntry from both buy and sell ListingFetchers.
4. Calling the update_csv() method of the constructed buysellentry.
5. Constructing a buy_sell_frame.
6. The buy_sell_frame construction calls the extract_data method of the fetcher.
7. The extract_data method calls the fetch_listing method to get the data from poe.trade.
8. All item properties are extracted from the fetched data in extract_data.
9. The extracted data is returned to the buy_sell_frame constructor.
10. The buy_sell_frame constructor converts currencies and calculates the profit.
11. The buy_sell_frame is returned to the update_csv method.
12. The update_csv method saves the new buy_sell_entry to the database.

```mermaid
sequenceDiagram
participant update_oldest_entry
participant fetch_all_listings

box rgb(80,80,80) Payload
participant payload_init as init
end

box rgb(80,80,80) ListingFetcher
participant fetch_init as init
participant fetch_listing
participant extract_data
end

box rgb(80,80,80) BuySellEntry
participant bs_init as init
participant construct_buy_sell_frame
participant update_csv
end

update_oldest_entry ->> fetch_all_listings: oldest_entry,<br/> buy_properties,<br/> sell_properties

loop repeat for buy and sell 
    fetch_all_listings ->> payload_init: oldest_entry, properties
    payload_init ->> fetch_all_listings: payload

    fetch_all_listings ->> fetch_init: payload
    fetch_init ->> fetch_all_listings: fetcher
end

fetch_all_listings ->> bs_init: fetchers
bs_init ->> fetch_all_listings: buysellentry

fetch_all_listings ->> update_csv: buysellentry.update_csv()
update_csv ->> construct_buy_sell_frame: 

construct_buy_sell_frame ->> extract_data: 
extract_data ->> fetch_listing: 
fetch_listing ->> extract_data: 
loop over all returned items
    extract_data ->> extract_data: extract_properties
    extract_data ->> extract_data: extract_gem_experience
end
extract_data ->> construct_buy_sell_frame: extracted_data

construct_buy_sell_frame ->> construct_buy_sell_frame: convert_chaos_to_divine
construct_buy_sell_frame ->> construct_buy_sell_frame: calculate_profit

construct_buy_sell_frame ->> update_csv: buy_sell_frame

update_csv ->> update_csv: update new entry<br/> in database

```

### Sequence to update the oldest entry (v0.1.1)

```mermaid
sequenceDiagram
participant update_oldest_entry
participant update_all_listings

box rgb(80,80,80) Payload
participant payload_init as init
end

box rgb(80,80,80) ListingFetcher
participant fetch_init as init
participant fetch_listing
participant extract_data
end

box rgb(80,80,80) BuySellEntry
participant bs_init as init
participant construct_buy_sell_frame
participant update_csv
end

update_oldest_entry ->> update_all_listings: oldest_entry,<br/> buy_properties,<br/> sell_properties

loop repeat for buy and sell 
    update_all_listings ->> payload_init: oldest_entry, properties
    payload_init ->> update_all_listings: payload

    update_all_listings ->> fetch_init: payload
    fetch_init ->> update_all_listings: fetcher

    update_all_listings ->> fetch_listing: fetch the listing
    fetch_listing ->> extract_data: extract the data

    loop over all returned items
        extract_data ->> extract_data: extract_properties
        extract_data ->> extract_data: extract_gem_experience
    end
    extract_data ->> fetch_listing: listing data
    fetch_listing ->> update_all_listings: 
end

update_all_listings ->> bs_init: listing data<br/>(buy and sell)
bs_init ->> construct_buy_sell_frame: 
construct_buy_sell_frame ->> construct_buy_sell_frame: convert_chaos_to_divine
construct_buy_sell_frame ->> construct_buy_sell_frame: calculate_profit
construct_buy_sell_frame ->> bs_init: buysellentry
bs_init ->> update_all_listings: 

update_all_listings ->> update_csv: buysellentry.update_csv()

update_csv ->> update_csv: update new entry<br/> in database

```

### Database

The database is represented as a collection of comma separated value files, each file storing the information of all entries within a profit method group. Each entry corrosponds with one line in the .csv file and consists of the following information:
* (string) Item Name
* (float) Buy price
* (float) Sell price
* (float) Profit
* (datetime as text) Time of last update

The time of last update is stored as text with the following format: 2024-03-20 21:22:29.

## v0.2.0

### Class diagram for poe_trade_rest

```mermaid
classDiagram
class poe_trade_rest{
    + update_oldest_entry(group: str) None
}
```
### Class diagram for the Database class

```mermaid
classDiagram
class Database{
    <<Singleton>>
    - instance: Database$
    - Database()
    + getInstance() Database$
    - get_oldest_entry(group: str) Entry
    + initialize_from_ninja(group: str) None
    + construct_BuySellCSV(group: str) None
    + construct_BuySellEntry(buy_entry: Entry, sell_entry: Entry) BuySellEntry
    + update_entry(group: str, entry: Entry) None
}
```

### Class diagram for dataclasses

```mermaid
classDiagram
class BuySellEntry{
    <<dataclass>>
    + id: int
    + item_name: str
    + buy_id: int
    + buy_mods: str
    + buy_url: str
    + buy_price: float
    + sell_id: int
    + sell_mods: str
    + sell_url: str
    + sell_price: float
    + profit: float
    + updated_at: datetime
}

class Entry{
    <<dataclass>>
    + id: int
    + item_name: str
    + modifiers: dict[str, Any]
    + url: str
    + value: float
    + nr_listed: int
    + updated_at: datetime
    + get_value_from_trade() None
    + mods_to_str() str
}

class Listing{
    <<dataclass>>
    + price: float
    + currency: str
}
```

### Class diagram for functional classes

```mermaid
classDiagram
class Fetcher{
    - trade_url: str$
    - header: dict$
    - last_query_time: datetime$
    + listings: list[Listing]
    + url: str
    + nr_listed: int
    + Fetcher(item_name: str, modifiers: dict[str, Any])
    - fetch() None
    - extract_listing(listing: json) Listing
    - build_query(item_name: str, modifiers: dict[str, Any]) json
}
```

## Future (v0.3.0+)

### Additional "Item" functionality in the Listing class

```mermaid
classDiagram
class Listing{
    <<dataclass>>
    + price: float
    + currency: str
    + listed_at: datetime
    + Item: Item
}

class Item{
    <<dataclass>>
    + item_name: str
    + ilvl: int
    + identified: bool
    + properties: dict[str, str]
    + requirements: dict[str, str]
    + explicit_mods: list[str]
    + sockets: list[str]
}
```

## Notes/Open Issues

* Remove all unnecessary fields from extract_data/fetch_listing, only keep Price and Currency. These are the only fields that need updates, the query contains all item parameter from input.
  * Be aware that saving intermediate data might still be interesting to improve algorithms 
* Remove fetch_all_listings(), add an update() method to BuySellEntry, or in the future: Entry.
* In the future, with the double database setup, the entries (Entry class) should have the functionality to update themselves.
* Change Payload to QueryBuilder, with subclasses for GemQueryBuilder, FlaskQueryBuilder, etc.
* Create sequence diagram for v0.2.0
* Include gem XP in GemQueryBuilder