# An example fast API taken straight from the docs for testing the docker container.
import os
from typing import Union
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Garmin DB imports
from garmindb import GarminConnectConfigManager
from garmindb.garmindb import GarminDb, Attributes, ActivitiesDb, Activities, StepsActivities, ActivityLaps, ActivityRecords
import fitfile
import folium
from folium.plugins import MarkerCluster


# Set up the DB we're interacting with
gc_config = GarminConnectConfigManager()
db_params_dict = gc_config.get_db_params()
garmin_db = GarminDb(db_params_dict)
garmin_act_db = ActivitiesDb(db_params_dict)
measurement_system = Attributes.measurements_type(garmin_db, default='imperial')
# unit_strings = fitfile.units.unit_strings[measurement_system]




app = FastAPI()


@app.get("/getLocations")
def getLocations():
    activities = ActivityRecords.get_all(garmin_act_db)
    returned_item = {}
    seen_activities = set()
    for element in activities:
        if element.position_lat is None or element.position_long is None:
            continue
        if element.activity_id not in seen_activities:
            seen_activities.add(element.activity_id)
            returned_item[element.timestamp] = {'activity' : element.activity_id, 'position_lat' : element.position_lat, 'position_long' : element.position_long, 'timestamp' : element.timestamp.strftime("%Y-%b-%d %H:%M") }
    return returned_item

@app.get("/updateDB")
def updateDB():
    os.system('garmindb_cli.py -i -a ')
    os.system('garmindb_cli.py -c --analyze -A ')
    return {"status" : "Ran without returning error"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/")
def read_root():
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
    m.save('/tmp/index.html')
    with open('/tmp/index.html') as index_file:
        return HTMLResponse(index_file.read(), status_code=200)

