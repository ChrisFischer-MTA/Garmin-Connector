import os
import hashlib
import time
import shutil

# Constants
# Location where the Garmin Watch is mounted
GARMIN_STRING_LENGTH = len('GARMIN/') 
# Location where the Garmin Watch data is copied too for the docker container
DATA_STORE_LOCATION = './data/garminvolume'
# Location where we store FIT files in case the container hoses them.
BACKUP_STORE_LOCATION = './backups'

# Helper function for backing up and copying FIT files for processing.
def copy_fit(*, fileName, GARMIN_DATA_STORE):
    # First, we copy to the backup.
    shutil.copyfile(f'{GARMIN_DATA_STORE}{fileName}', f'{BACKUP_STORE_LOCATION}/{fileName}-{str(int(time.time()))}')
    # Next, we copy to the file store
    shutil.copyfile(f'{GARMIN_DATA_STORE}{fileName}', f'{DATA_STORE_LOCATION}/{fileName}')

def process_fit(path):
    pass

# Retrieves the watches' directory path on the host
def get_watch_path():
    # First, let's detect if the watch is plugged in
    directory_tree = os.walk('/media')
    garmin_directory_path = None
    # XXX: Is it a safe assumption that we will always get the upper level directories first?
    # Handling for now by proactively chopping off everything past the first GARMIN.
    for element in directory_tree:
        if(len(element) > 0 and 'GARMIN/' in element[0]):
            # Let's find the first instance of Garmin and chop everything past that off
            return element[0][0:element[0].index('GARMIN/') + GARMIN_STRING_LENGTH] + 'GARMIN/'
    return None
    
def main():
    # First, we should do a sanity check to ensure that we're being run from the correct directory.
    if not os.path.exists(DATA_STORE_LOCATION):
        print("I can't see the local Garmin Data store. Ensure you're running me out of the correct directory!")
        return
    if not os.path.exists(BACKUP_STORE_LOCATION):
        print("I can't see the local Backup Store Directory. Ensure you're running me out of the correct directory!")
        return

    target = get_watch_path()
    if target is None:
        # No watch found, exit the script
        return 0
    # Now, let's diff the directories. Each file should be categorized one of three ways
    # (1) File is new and should be imported
    # (2) File is changed and should be imported with a suffix
    # (3) File is already imported.
    # Additionally, we want a store of FIT files. We will store that in "backup/"
    for subdir, dirs, files in os.walk(target):
        for file in files:
            file_extension = os.path.splitext(os.path.join(subdir, file))[1]
            full_file_path = os.path.join(subdir, file) # Ex: /home/username/projects/garmin-fit/fit-mnt/GARMIN-backup/GARMIN/Records/Records.fit
            clone_path = subdir[len(target):] # all directories after GARMIN/GARMIN Ex: /Records
            # This is a very hacky linux trick. If something's in the root of the watch,
            # clone path is NULL. If clone path is NULL, we double slash later on due to 
            # hardcoding. So, we can just say clone path is equal to . which is equivalent
            if(clone_path == ""):
                cloth_path = '.'
            if file_extension.lower() == '.fit':
                # First, let's create the directories in the data store if they don't exist
                if not os.path.exists(DATA_STORE_LOCATION+'/'+clone_path):
                    os.makedirs(DATA_STORE_LOCATION+'/'+clone_path)
                # Additionally, let's create the directories in the backup store if they don't exist
                if not os.path.exists(BACKUP_STORE_LOCATION+'/'+clone_path):
                    os.makedirs(BACKUP_STORE_LOCATION+'/'+clone_path)
                # If file is new and should be imported
                if not os.path.exists(f'{DATA_STORE_LOCATION}/{clone_path}/{file}'):
                    copy_fit(fileName = f'{clone_path}/{file}', GARMIN_DATA_STORE=target)
                # If file is changed, delete the one in data and replace it.
                elif hashlib.md5(open(f'{target}{clone_path}/{file}','rb').read()).hexdigest() \
                    != hashlib.md5(open(f'{DATA_STORE_LOCATION}/{clone_path}/{file}','rb').read()).hexdigest():
                    os.remove(f'{DATA_STORE_LOCATION}/{clone_path}/{file}')
                    copy_fit(fileName = f'{clone_path}/{file}', GARMIN_DATA_STORE=target)
                    print(f'{target}{clone_path}/{file} is different')
                else:
                    print(f'{target}{clone_path}/{file} is the same')
    

if __name__ == "__main__":
    main()
