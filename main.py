# An example fast API taken straight from the docs for testing the docker container.
import os
from typing import Union
from fastapi import FastAPI

# Garmin DB imports
import fitfile
from garmindb import GarminConnectConfigManager
from garmindb.garmindb import GarminDb, Attributes, ActivitiesDb, Activities, StepsActivities, ActivityLaps, ActivityRecords


# Set up the DB we're interacting with
gc_config = GarminConnectConfigManager()
db_params_dict = gc_config.get_db_params()
garmin_db = GarminDb(db_params_dict)
garmin_act_db = ActivitiesDb(db_params_dict)
measurement_system = Attributes.measurements_type(garmin_db)
unit_strings = fitfile.units.unit_strings[measurement_system]




app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World1"}

@app.get("/getLocations")
def getLocations():
    activities = ActivityRecords.get_all(garmin_act_db)
    returned_item = {}
    for element in activities:
        if element.position_lat is None or element.position_long is None:
            continue
        returned_item[element.activity_id] = {'timestamp' : element.timestamp, 'position_lat' : element.position_lat, 'position_long' : element.position_long }
    return returned_item

@app.get("/updateDB")
def updateDB():
    os.system('garmindb_cli.py -c --analyze -A ')
    return {"status" : "Ran without returning error"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
