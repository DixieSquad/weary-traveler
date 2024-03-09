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
        update data ->> update oldest entry: Request update
        database ->> update oldest entry: Get oldest entry
        update oldest entry ->> database: Save updated entry
    end
end

user ->> refresh toggle: Toggle Off
refresh toggle ->> update data: Stop processes
refresh toggle ->>- refresh UI: 
```

## Detailed Design