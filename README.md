# Garmin-Connector
This repository is a pipeline that allows me to digest data from my garmin watch into a local SQL-lite database, parse it, and expose it via API for Django Webapps and Home Automations. I utlizie this repository because my internet at home is unstable and I often can't connect to the internet for hours/days, rending the app useless.


```
--------------    --------------------    -------------------------------------------    ----------------------------
| USB Script | -> | Local Data Store | -> | GarminDB Processing and Local SQLite DB | -> | Custom FastAPI endpoints |
--------------    --------------------    -------------------------------------------    ----------------------------
```

I use the GarminDB project to handle the processing of the FIT files. First, I have a python script that copies the data off of the watch into a data store that is accessible to the container and also to a backup folder. Periodically, an endpoint is called that results in the ingestion of new data. This puts the data into a SQLite database and allows me to interact with it in python. I then can call it from the fastAPI code and pass the data off in JSON that is needed.

My intention is to use this stack to ingest data into my journal (Sleep, Stress, Workout hours) to give a more holisitc summary of every day. Additionally, I want to make a dashboard that shows me every place I've ever ran. 

## Map Views

### Main View (`/`)

The root endpoint renders an interactive map with zoom-adaptive marker clustering (via Leaflet MarkerCluster). Each workout is represented by a single marker placed at its first recorded GPS coordinate. As you zoom out, markers merge into numbered clusters; zooming in reveals individual markers.

A **layer control** in the top-right corner lets you toggle between:
- **OpenStreetMap** — the default street/terrain view.
- **Satellite** — Esri World Imagery aerial/satellite tiles.

### City View (`/cityview`)

The `/cityview` endpoint provides a higher-level "where have I been" visualization using geofenced circles:

1. All activity starting-points are grouped into grid cells by rounding their latitude and longitude to 1 decimal place (~11 km resolution). Each cell roughly corresponds to a city or region.
2. For each cell, the centroid (average lat/long) is computed.
3. A `folium.Circle` is drawn at the centroid with a radius that grows **logarithmically** with the number of activities in that cell (`base_radius × (1 + ln(count))`). This prevents regions with many activities from overwhelming the map while still communicating relative density.
4. Clicking a circle shows the activity count for that region.

The same map/satellite tile toggle is available on this view.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Interactive clustered marker map with tile toggle |
| `GET /cityview` | City-level geofence map |
| `GET /getLocations` | JSON of one GPS point per activity |
| `GET /updateDB` | Trigger Garmin data import and analysis |
| `GET /items/{item_id}` | Example/test endpoint |

