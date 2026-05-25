"""
Garmin Device Scraper

Copies FIT files from a mounted Garmin watch to both a local data store
(for container processing) and a backup directory. Files are compared by
MD5 hash to avoid redundant copies.

Usage:
    Run from the repository root where ./data and ./backups are accessible.
"""

import os
import hashlib
import time
import shutil

# Constants
# Length of the 'GARMIN/' prefix used when parsing mount paths.
GARMIN_STRING_LENGTH = len('GARMIN/')
# Location where the Garmin Watch data is copied to for the docker container.
DATA_STORE_LOCATION = './data/garminvolume/garmin'
# Location where we store FIT files as a safety backup in case the container
# corrupts or loses the data store.
BACKUP_STORE_LOCATION = './backups'


def copy_fit(*, clonePath, fileName, GARMIN_DATA_STORE):
    """Copy a FIT file to both the backup and data store directories."""
    # Back up the original file with a Unix timestamp suffix for versioning.
    shutil.copyfile(
        f'{GARMIN_DATA_STORE}{clonePath}/{fileName}',
        f'{BACKUP_STORE_LOCATION}/{clonePath}/{fileName}-{str(int(time.time()))}',
    )
    # Copy to the data store (lowercased path to match garmindb expectations).
    shutil.copyfile(
        f'{GARMIN_DATA_STORE}{clonePath}/{fileName}',
        f'{DATA_STORE_LOCATION}/{clonePath.lower()}/{fileName}',
    )


def process_fit(path):
    """Placeholder for future FIT file processing logic."""
    pass


def get_watch_path():
    """Detect and return the Garmin watch mount path under /media.

    Walks /media looking for a directory containing 'GARMIN/'. Returns the
    path up to and including the first 'GARMIN/' segment. This is safe even
    if nested GARMIN directories exist because we truncate at the first match.
    """
    directory_tree = os.walk('/media')
    for element in directory_tree:
        if len(element) > 0 and 'GARMIN/' in element[0]:
            # Truncate at the first 'GARMIN/' occurrence. os.walk returns
            # directories in top-down order by default, so the first match
            # is the shallowest (most correct) path.
            return element[0][0:element[0].index('GARMIN/') + GARMIN_STRING_LENGTH] + 'GARMIN/'
    return None


def main():
    """Main entry point: validate environment, detect watch, and sync files."""
    # Sanity checks: ensure required directories are reachable.
    if not os.path.exists(DATA_STORE_LOCATION):
        print("I can't see the local Garmin Data store. Ensure you're running me out of the correct directory!")
        return
    if not os.path.exists(BACKUP_STORE_LOCATION):
        print("I can't see the local Backup Store Directory. Ensure you're running me out of the correct directory!")
        return

    target = get_watch_path()
    if target is None:
        # No watch found, exit the script.
        return 0

    # Walk the watch filesystem and sync each file to local stores.
    # Files are categorized as:
    #   (1) New — copy to both data store and backup.
    #   (2) Changed (different MD5) — replace in data store and back up.
    #   (3) Unchanged — skip.
    for subdir, dirs, files in os.walk(target):
        for file in files:
            full_file_path = os.path.join(subdir, file)
            # Relative path after the watch root, e.g. "/Activity"
            clone_path = subdir[len(target):]
            # If the file lives at the root of GARMIN/, clone_path is empty.
            # Use '.' to avoid double-slash issues in path construction.
            if clone_path == "":
                clone_path = '.'

            # Ensure destination directories exist in both stores.
            # Note: garmindb expects lowercased directory names, so we
            # lowercase the data store path while keeping backup paths intact.
            if not os.path.exists(DATA_STORE_LOCATION + '/' + clone_path.lower()):
                os.makedirs(DATA_STORE_LOCATION + '/' + clone_path.lower())
            if not os.path.exists(BACKUP_STORE_LOCATION + '/' + clone_path):
                os.makedirs(BACKUP_STORE_LOCATION + '/' + clone_path)

            data_store_file = f'{DATA_STORE_LOCATION}/{clone_path.lower()}/{file}'

            if not os.path.exists(data_store_file):
                # New file — import it.
                copy_fit(clonePath=clone_path, fileName=file, GARMIN_DATA_STORE=target)
                print(f'Copying new file: {data_store_file}')
            elif (
                hashlib.md5(open(f'{target}{clone_path}/{file}', 'rb').read()).hexdigest()
                != hashlib.md5(open(data_store_file, 'rb').read()).hexdigest()
            ):
                # File changed — replace existing copy.
                os.remove(data_store_file)
                copy_fit(clonePath=clone_path, fileName=file, GARMIN_DATA_STORE=target)
                print(f'{target}{clone_path}/{file} is different')
            # else: file unchanged, nothing to do.


if __name__ == "__main__":
    main()
