# An example fast API taken straight from the docs for testing the docker container.
import os
from typing import Union
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World1"}

@app.get("/updateDB")
def updateDB():
    os.system('garmindb_cli.py -c --analyze -A ')
    return {"status" : "Ran without returning error"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
