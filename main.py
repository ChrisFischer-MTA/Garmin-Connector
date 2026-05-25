"""
Garmin Connector FastAPI Application

Exposes Garmin activity data via a REST API and provides interactive map
visualizations including:
- A clustered marker map with map/satellite tile toggle
- A city-level geofence view that groups activities into regional circles

Approach for City View / Geofencing:
    Activities are grouped into city-level clusters by rounding GPS coordinates
    to 1 decimal place (~11km resolution). For each cluster, a Circle overlay
    is drawn on the map representing the geofenced region. The circle radius
    scales with the number of activities in that region, giving a visual sense
    of where the user has been most active.
"""

import os
import math
import threading
import subprocess
from typing import Union
from collections import defaultdict
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Garmin DB imports
from garmindb import GarminConnectConfigManager
from garmindb.garmindb import (
    GarminDb, Attributes, ActivitiesDb, Activities,
    StepsActivities, ActivityLaps, ActivityRecords,
)
import fitfile
import folium
from folium.plugins import MarkerCluster

# --- Database Initialization ---
# Load configuration and connect to the Garmin SQLite databases.
gc_config = GarminConnectConfigManager()
db_params_dict = gc_config.get_db_params()
garmin_db = GarminDb(db_params_dict)
garmin_act_db = ActivitiesDb(db_params_dict)
measurement_system = Attributes.measurements_type(garmin_db, default='imperial')

# Geofence clustering resolution: 1 decimal place ≈ 11km grid cells.
# Adjusting this value changes how broadly activities are grouped into cities.
CITY_CLUSTER_PRECISION = 1

# Base radius (meters) for city geofence circles; scales with activity count.
CITY_BASE_RADIUS = 3000

app = FastAPI()

# --- Background update state ---
# Prevents concurrent updateDB runs and allows the long-running garmindb
# command to complete even if the HTTP client times out.
_update_lock = threading.Lock()
_update_running = False


def _add_tile_layers(m: folium.Map) -> None:
    """Add map and satellite tile layers with a toggle control.

    Adds OpenStreetMap (default) and Esri World Imagery (satellite) tile layers
    to the given folium Map, along with a LayerControl widget so the user can
    switch between them.
    """
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
    ).add_to(m)
    # The default OpenStreetMap layer is already present; LayerControl exposes it.
    folium.LayerControl().add_to(m)


@app.get("/getLocations")
def getLocations():
    """Return one representative GPS point per activity.

    Iterates all activity records and picks the first valid (non-null) lat/long
    for each unique activity_id. This ensures one marker per workout on the map.
    """
    activities = ActivityRecords.get_all(garmin_act_db)
    returned_item = {}
    seen_activities = set()
    for element in activities:
        if element.position_lat is None or element.position_long is None:
            continue
        if element.activity_id not in seen_activities:
            seen_activities.add(element.activity_id)
            returned_item[element.timestamp] = {
                'activity': element.activity_id,
                'position_lat': element.position_lat,
                'position_long': element.position_long,
                'timestamp': element.timestamp.strftime("%Y-%b-%d %H:%M"),
            }
    return returned_item


@app.get("/updateDB")
def updateDB():
    """Trigger a database refresh by importing and analyzing new Garmin data.

    The garmindb update command can take 5-10 minutes.  To avoid failures when
    the HTTP client times out before the command finishes, the update is run in
    a daemon background thread so it always runs to completion.

    A module-level flag (guarded by a lock) ensures that at most one update
    process runs at a time.  Concurrent calls return immediately with a
    "already in progress" status rather than spawning a second process.
    """
    global _update_running

    with _update_lock:
        if _update_running:
            return {"status": "Update already in progress"}
        _update_running = True

    def _run_update():
        global _update_running
        try:
            subprocess.run(
                ['garmindb_cli.py', '--all', '--download', '--import', '--analyze', '--latest'],
            )
            print('concluded update!')
        finally:
            with _update_lock:
                _update_running = False

    thread = threading.Thread(target=_run_update, daemon=True)
    thread.start()
    return {"status": "Update started"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    """Example endpoint retained for testing/debugging purposes."""
    return {"item_id": item_id, "q": q}


@app.get("/")
def read_root():
    """Render the main map view with clustered markers and tile layer toggle.

    Uses MarkerCluster for zoom-adaptive grouping and provides a toggle
    between the standard map view and satellite imagery.
    """
    m = folium.Map()
    cluster = MarkerCluster().add_to(m)
    activities = getLocations()
    for element in activities:
        activity = activities[element]
        folium.Marker(
            location=[activity['position_lat'], activity['position_long']],
            popup=f"{activity['timestamp']} // {activity['activity']}",
            icon=folium.Icon(),
        ).add_to(cluster)
    _add_tile_layers(m)
    m.save('/tmp/index.html')
    with open('/tmp/index.html') as index_file:
        return HTMLResponse(index_file.read(), status_code=200)


@app.get("/cityview")
def city_view():
    """Render a city-level geofence map showing regions where activities occurred.

    Approach:
        1. Fetch one GPS point per activity via getLocations().
        2. Group activities into grid cells by rounding coordinates to
           CITY_CLUSTER_PRECISION decimal places (~11km cells).
        3. For each cell, compute the centroid (average lat/long of activities
           in that cell) and draw a Circle whose radius grows logarithmically
           with the number of activities — giving a geofence-style boundary
           around each city/region visited.
        4. A popup on each circle shows the activity count for that region.

    The map includes the same tile layer toggle (map vs satellite) as the
    main view.
    """
    activities = getLocations()

    # Group activities into city-level clusters based on rounded coordinates.
    clusters = defaultdict(list)
    for element in activities:
        activity = activities[element]
        lat = activity['position_lat']
        lng = activity['position_long']
        # Round to create grid cell key
        key = (round(lat, CITY_CLUSTER_PRECISION), round(lng, CITY_CLUSTER_PRECISION))
        clusters[key].append((lat, lng))

    m = folium.Map(zoom_start=4)

    for key, points in clusters.items():
        # Compute centroid of all activities in this cluster
        centroid_lat = sum(p[0] for p in points) / len(points)
        centroid_lng = sum(p[1] for p in points) / len(points)
        # Radius grows logarithmically so a city with many activities doesn't
        # become overwhelmingly large on the map.
        radius = CITY_BASE_RADIUS * (1 + math.log(len(points)))
        folium.Circle(
            location=[centroid_lat, centroid_lng],
            radius=radius,
            popup=f"{len(points)} activities in this area",
            color='blue',
            fill=True,
            fill_opacity=0.2,
        ).add_to(m)

    _add_tile_layers(m)
    m.save('/tmp/cityview.html')
    with open('/tmp/cityview.html') as city_file:
        return HTMLResponse(city_file.read(), status_code=200)

