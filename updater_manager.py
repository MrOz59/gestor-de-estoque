import os
import requests
import subprocess
import configparser

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
    updater_version = config['config']['updater_version']
    version = config['config']['version']
    return updater_version, version

def download_updater(updater_version, filename):
    """
    Downloads the updater executable.
    """
    updater_url_template = 'https://github.com/MrOz59/Kalymos-Updater/releases/download/{version}/{filename}'
    updater_url = updater_url_template.format(version=updater_version, filename=filename)

    try:
        response = requests.get(updater_url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded {filename}.")
        
    except requests.HTTPError as e:
        print(f"An error occurred while downloading the file: {e}")
        return False

    return True

def ensure_updater(updater_version, skip_update_check=False):
    """
    Ensure the updater executable is present and up-to-date.
    Downloads the updater if it is missing or out-of-date.
    Returns:
        bool: True if an update was needed and executed, False otherwise.
    """
    updater_filename = 'kalymos-updater.exe'

    if os.path.exists(updater_filename):
        if skip_update_check:
            print(f"{updater_filename} found. Skipping update check as per configuration.")
            print("Running the updater...")
            subprocess.run([updater_filename])
            return False  
        else:
            # Check for updates (not implemented)
            print(f"{updater_filename} found. Checking for updates...")
            # Example placeholder for update checking logic
            # Assume checking the latest version from a file or API
            latest_version = 'latest'  # Placeholder value; adjust accordingly
            if updater_version != latest_version:
                print("Update available. Downloading the latest version...")
                download_updater(latest_version, updater_filename)
                print("Running the updated updater...")
                subprocess.run([updater_filename])  # No need for shell=True
                return True
            else:
                print("Updater is up-to-date.")
                return False
    else:
        print(f"{updater_filename} not found. Downloading...")

        # Download the updater for the specified version in config.ini
        if not download_updater(updater_version, updater_filename):
            print("Failed to download the updater.")
            return False

        # Execute the updater
        print("Running the updater...")
        subprocess.run([updater_filename])  # No need for shell=True
        return True

def main():
    """
    Main function to check for updates and handle the updater executable.
    """
    ini_file = 'config.ini'
    updater_version, _ = load_config(ini_file)

    # Ensure the updater is present and up-to-date
    update_needed = ensure_updater(updater_version, skip_update_check=False)
    if update_needed:
        print("Updater was updated and executed.")
    else:
        print("No update needed or an error occurred during update.")

if __name__ == "__main__":
    main()
