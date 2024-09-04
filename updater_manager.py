import os
import sys
import requests
import subprocess
import configparser
import ctypes

def load_config(ini_file):
    """
    Loads the configuration from the ini file.
    Returns:
        tuple: (updater_version, version)
    """
    if not os.path.exists(ini_file):
        raise FileNotFoundError(f"Configuration file '{ini_file}' not found.")
    
    config = configparser.ConfigParser()
    config.read(ini_file)
    updater_version = config['config']['updater_version'].lstrip('v')
    version = config['config']['version']
    return updater_version, version

def update_config(ini_file, updater_version):
    """
    Updates the updater_version in the config file.
    """
    config = configparser.ConfigParser()
    config.read(ini_file)
    config['config']['updater_version'] = 'v' + updater_version  # Re-add 'v' to match format

    with open(ini_file, 'w') as configfile:
        config.write(configfile)
    print(f"Updated config file with new updater version: v{updater_version}")

def download_updater(updater_version, filename):
    """
    Downloads the updater executable.
    """
    updater_url_template = 'https://github.com/MrOz59/Kalymos-Updater/releases/download/v{version}/{filename}'
    updater_url = updater_url_template.format(version=updater_version, filename=filename)

    try:
        response = requests.get(updater_url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded {filename}.")
        
        return updater_version
        
    except requests.HTTPError as e:
        print(f"An error occurred while downloading the file: {e}")
        return None

def check_for_updates(owner, repo, current_version):
    """
    Checks the GitHub repository for a new release using the GitHub API.

    Args:
        owner (str): The GitHub repository owner.
        repo (str): The GitHub repository name.
        current_version (str): The current version of the application.

    Returns:
        str: The latest version available, or None if there is no update.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        latest_version = response.json()['tag_name'].lstrip('v')  # Remove 'v' if present
        # Compare versions
        if compare_versions(latest_version, current_version):
            print(f"New version available: v{latest_version}")
            return latest_version
        else:
            print("You are already using the latest version.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking for updates: {e}")
        return None
    except ValueError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def compare_versions(version1, version2):
    """
    Compare two version strings.

    Args:
        version1 (str): The first version string.
        version2 (str): The second version string.

    Returns:
        bool: True if version1 is newer than version2, False otherwise.
    """
    version1_parts = list(map(int, version1.split('.')))
    version2_parts = list(map(int, version2.split('.')))
    
    # Pad the shorter version with zeros
    while len(version1_parts) < len(version2_parts):
        version1_parts.append(0)
    while len(version2_parts) < len(version1_parts):
        version2_parts.append(0)
    
    return version1_parts > version2_parts

def run_as_admin(executable_name, cmd_line=None):
    """
    Re-run the specified executable as an administrator.
    
    :param executable_name: The name of the executable to run as administrator.
    :param cmd_line: The command line arguments to pass to the executable.
    """
    if cmd_line is None:
        cmd_line = ' '.join(sys.argv[1:])  # Skip the script name

    try:
        # Request administrator privileges to run the specified executable
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable_name, cmd_line, None, 1)
    except Exception as e:
        print(f"Failed to request admin privileges: {e}")
        sys.exit(1)

def ensure_updater(updater_version, skip_update_check):
    """
    Ensure the updater executable is present and up-to-date.
    Downloads the updater if it is missing or out-of-date.
    Returns:
        bool: True if an update was needed and executed, False otherwise.
    """
    updater_filename = 'kalymos-updater.exe'

    updater_exists = os.path.exists(updater_filename)
    
    if updater_exists:
        if skip_update_check:
            print(f"{updater_filename} found. Skipping update check as per configuration.")
            print("Running the updater...")
            run_as_admin(f"{updater_filename}")
            return False
        else:
            print(f"{updater_filename} found. Checking for updates...")
            latest_version = check_for_updates('MrOz59', 'Kalymos-Updater', updater_version)
            if latest_version:
                print("Update available. Downloading the latest version...")
                new_version = download_updater(latest_version, updater_filename)
                if new_version:
                    update_config('config.ini', new_version)
                    print("Running the updated updater...")
                    run_as_admin(f"{updater_filename}")
                    return
                else:
                    print("Failed to download the updater.")
                    return
            else:
                print("Updater is up-to-date.")
                run_as_admin(f"{updater_filename}")
    else:
        print(f"{updater_filename} not found. Downloading...")
        if skip_update_check == False:
            version_to_download = updater_version
            print('1')
        else:
            print('1')
            version_to_download = check_for_updates('MrOz59', 'Kalymos-Updater', updater_version)
        print(version_to_download)
        if version_to_download:
            new_version = download_updater(version_to_download, updater_filename)
            if new_version:
                update_config('config.ini', new_version)
                print("Running the updater...")
                run_as_admin(f"{updater_filename}")

            else:
                print("Failed to download the updater.")
                run_as_admin(f"{updater_filename}")

        else:
            print("No version available for download.")
            run_as_admin(f"{updater_filename}")

