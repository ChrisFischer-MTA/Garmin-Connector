# Garmin-Connector

A self-hosted pipeline that ingests FIT files from a USB-connected Garmin watch into a local SQLite database and exposes the data via a FastAPI service. Designed to work fully offline — no cloud connection to Garmin's servers required at runtime.

## Architecture

```
--------------    --------------------    -------------------------------------------    ----------------------------
| USB Script | -> | Local Data Store | -> | GarminDB Processing and Local SQLite DB | -> | Custom FastAPI endpoints |
--------------    --------------------    -------------------------------------------    ----------------------------
```

1. **`scrape-device.py`** (runs on the host) — detects a mounted Garmin watch under `/media`, diffs the watch filesystem against the local data store, and copies new or changed FIT files to both a processing volume (`./data/garminvolume/garmin`) and a timestamped backup directory (`./backups`).
2. **GarminDB** — the [GarminDB](https://github.com/tcgoetz/GarminDB) library processes the FIT files and populates a local SQLite database.
3. **`main.py`** (runs inside Docker) — a FastAPI application that queries the SQLite database and serves the data via HTTP endpoints.

## Repository Structure

| File | Description |
|---|---|
| `main.py` | FastAPI application with activity data endpoints |
| `scrape-device.py` | Host-side script to copy FIT files from the watch |
| `Dockerfile` | Container image based on `python:3.13-slim` |
| `compose.yml` | Docker Compose service definition |
| `GarminConnectConfig.json` | GarminDB configuration template |

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Interactive [Folium](https://python-visualization.github.io/folium/) map of all activity GPS locations |
| `GET /getLocations` | JSON object of deduplicated activity GPS coordinates with timestamps |
| `GET /updateDB` | Triggers GarminDB to ingest and analyze any new FIT files in the data store |
| `GET /items/{item_id}` | Sample/test endpoint |

## Setup

### Prerequisites

- Docker and Docker Compose
- A Garmin watch that mounts as a USB mass storage device under `/media`

### Configuration

1. Copy `GarminConnectConfig.json` and update the `credentials` block with your Garmin Connect account details (used by GarminDB for cloud sync features if desired):

    ```json
    "credentials": {
        "user": "your@email.com",
        "password": "yourpassword"
    }
    ```

    The `directories` block is pre-configured to match the Docker volume paths and should not need to change:

    ```json
    "directories": {
        "base_dir":   "/opt/garmin/data/healthdata",
        "mount_dir":  "/opt/garmin/data/garminvolume"
    }
    ```

2. Create the required host-side directories:

    ```bash
    mkdir -p ./data/garminvolume/garmin
    mkdir -p ./backups
    ```

### Running the Container

```bash
docker compose up -d
```

The FastAPI service will be available at `http://localhost:10821`.

### Syncing Data from the Watch

Connect your Garmin watch via USB and run the scrape script from the repository root:

```bash
python scrape-device.py
```

This will copy any new or changed FIT files from the watch to the local data store and backup directory. Once files are copied, trigger ingestion by calling:

```
GET http://localhost:10821/updateDB
```

## Enabled Stats

The following GarminDB stat categories are enabled by default in `GarminConnectConfig.json`:

- Monitoring
- Steps
- Intensity time (`itime`)
- Sleep
- Resting heart rate (`rhr`)
- Weight
- Activities (walking, running, cycling)
