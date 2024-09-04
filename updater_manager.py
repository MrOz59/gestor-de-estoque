import os
import sys
import requests
import ctypes
from packaging import version
import logging

logging.basicConfig(level=logging.INFO)

def load_config():
    env_vars = ['Updater', 'SkipUpdate', 'Repo', 'Owner']
    loaded_vars = {}
    
    for var in env_vars:
        value = os.environ.get(var)
        if value is not None:
            if value == 'False':
                value = False
            elif value == 'True':
                value = True
            loaded_vars[var] = value
            logging.info(f"{var} loaded with value: {value}")
        else:
            logging.info(f"{var} is not set.")
    
    return loaded_vars

def update_config(var_name, new_value):
    current_value = os.environ.get(var_name)
    
    if current_value is None or version.parse(current_value) < version.parse(new_value):
        os.environ[var_name] = new_value
        logging.info(f"{var_name} updated to {new_value}")
    else:
        logging.info(f"{var_name} remains at {current_value}")

def download_updater(updater_version, filename):
    updater_url = f'https://github.com/MrOz59/Kalymos-Updater/releases/download/{updater_version}/{filename}'
    
    try:
        response = requests.get(updater_url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info(f"Downloaded {filename}.")
        return updater_version
        
    except requests.HTTPError as e:
        logging.error(f"An error occurred while downloading the file: {e}")
        return None

def check_for_updates(owner, repo, current_version):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        latest_version = response.json()['tag_name']
        if version.parse(latest_version) > version.parse(current_version):
            logging.info(f"New version available: v{latest_version}")
            return latest_version
        else:
            logging.info("You are already using the latest version.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while checking for updates: {e}")
        return None
    except ValueError as e:
        logging.error(f"Error decoding JSON response: {e}")
        return None

def run_as_admin(executable_name, cmd_line=None):
    if cmd_line is None:
        cmd_line = ' '.join(sys.argv[1:])

    try:
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable_name, cmd_line, None, 1)
        if result <= 32:
            logging.error(f"Failed to run {executable_name} as admin. Error code: {result}")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to request admin privileges: {e}")
        sys.exit(1)

def ensure_updater():
    updater_filename = 'kalymos-updater.exe'
    updater_exists = os.path.exists(updater_filename)
    configs = load_config()
    skip_update_check = configs.get('SkipUpdate', False)
    updater_version = configs.get('Updater', '0')
    
    if updater_exists:
        if skip_update_check:
            logging.info(f"{updater_filename} found. Skipping update check as per configuration.")
        else:
            logging.info(f"{updater_filename} found. Checking for updates...")
            latest_version = check_for_updates('MrOz59', 'Kalymos-Updater', updater_version)
            if latest_version:
                logging.info("Update available. Downloading the latest version...")
                new_version = download_updater(latest_version, updater_filename)
                if new_version:
                    update_config('Updater', new_version)
                    logging.info("Running the updated updater...")
                    run_as_admin(updater_filename)
                    return True
                else:
                    logging.error("Failed to download the updater.")
                    return False
            else:
                logging.info("Updater is up-to-date.")
                run_as_admin(updater_filename)
                return False
    else:
        logging.info(f"{updater_filename} not found. Downloading...")
        if not skip_update_check:
            version_to_download = updater_version
        else:
            version_to_download = check_for_updates('MrOz59', 'Kalymos-Updater', updater_version)
        
        if version_to_download:
            new_version = download_updater(version_to_download, updater_filename)
            if new_version:
                update_config('Updater', new_version)
                logging.info("Running the updater...")
                run_as_admin(updater_filename)
                return True
            else:
                logging.error("Failed to download the updater.")
                return False
        else:
            logging.error("No version available for download.")
            return False

def main():
    ensure_updater()

if __name__ == "__main__":
    main()
