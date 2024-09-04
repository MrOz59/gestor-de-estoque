import os
import sys
import winreg
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

def set_registry_value(key, value):
    """
    Sets a string value in the Windows registry.

    Args:
        key (str): The registry key path.
        value (str): The value to be set.

    Raises:
        Exception: If an error occurs while setting the registry value.
    """
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as reg_key:
            winreg.SetValueEx(reg_key, 'Value', 0, winreg.REG_SZ, value)
    except Exception as e:
        logging.error(f"Error setting registry value: {e}")

def get_registry_value(key):
    """
    Retrieves a string value from the Windows registry.

    Args:
        key (str): The registry key path.

    Returns:
        str: The value stored in the registry key, or None if the key does not exist.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_READ) as reg_key:
            value, _ = winreg.QueryValueEx(reg_key, 'Value')
            return value
    except FileNotFoundError:
        return None
    except Exception as e:
        logging.error(f"Error reading registry value: {e}")
        return None

def update_registry(var_name, new_value):
    """
    Updates the registry value if the new value is greater than the current value.

    Args:
        var_name (str): The name of the registry variable to update.
        new_value (str): The new value to be set in the registry.
    """
    registry_key = r"Software\KalymosApp"
    current_value = get_registry_value(f"{registry_key}\\{var_name}")
    
    if current_value is None or version.parse(current_value) < version.parse(new_value):
        set_registry_value(f"{registry_key}\\{var_name}", new_value)
        logging.info(f"{var_name} updated to {new_value}")
    else:
        logging.info(f"{var_name} remains at {current_value}")

def download_updater(updater_version, filename):
    """
    Downloads the updater executable from GitHub.

    Args:
        updater_version (str): The version of the updater to download.
        filename (str): The filename to save the downloaded updater as.

    Returns:
        str: The version of the downloaded updater if successful, otherwise None.
    """
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

def check_for_updates(current_version):
    """
    Checks for the latest version of the updater on GitHub.

    Args:
        owner (str): The GitHub repository owner.
        repo (str): The GitHub repository name.
        current_version (str): The current version of the updater.

    Returns:
        str: The latest version available if there is an update, otherwise None.
    """
    url = f"https://api.github.com/repos/MrOz59/kalymos-updater/releases/latest"
    
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
    """
    Runs a specified executable with administrative privileges.

    Args:
        executable_name (str): The path to the executable to run.
        cmd_line (str, optional): Command-line arguments to pass to the executable.

    Raises:
        SystemExit: If the executable fails to run with administrative privileges.
    """
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
    """
    Ensures the updater executable is present, up-to-date, and runs it if necessary.
    Updates registry values as needed.
    """
    updater_filename = 'kalymos-updater.exe'
    updater_exists = os.path.exists(updater_filename)
    configs = load_config()
    
    skip_update_check = configs.get('SkipUpdate', False)
    updater_version = configs.get('Updater', '0')
    print(f'Updater: {updater_version}')
    repo = configs.get('Repo', '0')
    owner = configs.get('Owner', '0')
    current_version = configs.get('Version', '0')
    executable = configs.get('MainExecutable', '0')
    
    # Set registry values
    registry_key = r"Software\KalymosApp"
    set_registry_value(f"{registry_key}\\Version", current_version)
    set_registry_value(f"{registry_key}\\Owner", owner)
    set_registry_value(f"{registry_key}\\Repo", repo)
    set_registry_value(f"{registry_key}\\MainExecutable", executable)

    # Check and use registered version for updates
    registry_version = get_registry_value(f"{registry_key}\\Updater")
    print(f'Registry: {registry_version}')
    if registry_version and version.parse(registry_version) > version.parse(updater_version):
        updater_version = registry_version

    if updater_exists:
        if skip_update_check:
            logging.info(f"{updater_filename} found. Skipping update check as per configuration.")
        else:
            logging.info(f"{updater_filename} found. Checking for updates...")
            latest_version = check_for_updates(updater_version)
            if latest_version:
                logging.info("Update available. Downloading the latest version...")
                new_version = download_updater(latest_version, updater_filename)
                if new_version:
                    update_registry('Updater', new_version)
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
            version_to_download = check_for_updates(owner, repo, updater_version)
        
        if version_to_download:
            new_version = download_updater(version_to_download, updater_filename)
            if new_version:
                update_registry('Updater', new_version)
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
    """
    Main function to ensure the updater is up-to-date and run it if needed.
    """
    ensure_updater()

if __name__ == "__main__":
    main()