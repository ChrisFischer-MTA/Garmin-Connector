# Garmin-Connector
This repository is a pipeline that allows me to digest data from my garmin watch into a local SQL-lite database, parse it, and expose it via API for Django Webapps and Home Automations. I utlizie this repository because my internet at home is unstable and I often can't connect to the internet for hours/days, rending the app useless.


--------------    --------------------    -------------------------------------------    ----------------------------
| USB Script | -> | Local Data Store | -> | GarminDB Processing and Local SQLite DB | -> | Custom FastAPI endpoints |
--------------    --------------------    -------------------------------------------    ----------------------------

I use the GarminDB project to handle the processing of the FIT files. First, I have a python script that copies the data off of the watch into a data store that is accessible to the container and also to a backup folder. Periodically, an endpoint is called that results in the ingestion of new data. This puts the data into a SQLite database and allows me to interact with it in python. I then can call it from the fastAPI code and pass the data off in JSON that is needed.

My intention is to use this stack to ingest data into my journal (Sleep, Stress, Workout hours) to give a more holisitc summary of every day. Additionally, I want to make a dashboard that shows me every place I've ever ran. 
