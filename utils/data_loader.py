import requests
import os
import tempfile
import zipfile

def download_gtfs(url):
    """
    Download a GTFS file from url and save it locally
    Args:
        url (string): url to download file from
    Returns:
        str: The file path where the GTFS zip was saved

    Raises:
        requests.exceptions.RequestException if download fails
    """
    try:
        # Make HTTP GET request to download the file
        # stream=True downloads in chunks
        response = requests.get(url, stream=True, timeout=30)

        # Check if the request was successful (status code 200)
        response.raise_for_status()

        # Create a temporary file to store the zip
        # delete=False means the file won't be auto-deleted when closed
        # suffix='.zip' gives it the right extension
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')

        # Write the downloaded content to the file in binary mode
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                temp_file.write(chunk)

        # Close the file so other functions can access it
        temp_file.close()

        # Return the path where it was saved
        return temp_file.name

    except requests.exceptions.Timeout:
        raise Exception("Download timed out after 30 seconds for URL: {url}")
    except requests.exceptions.RequestException as e:
        raise Exception("Failed to download GTFS from {url}: {str(e)}")



def extract_gtfs(zip_path):
    """
    Extract a GTFS zip file to a temporary directory.

    Args:
        zip_path (str): Path to the GTFS zip file

    Returns:
        str: Path to the directory containing extracted GTFS files

    Raises:
        zipfile.BadZipFile: If the file is not a valid zip
    """

    temp_dir = tempfile.mkdtemp()

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)
        return temp_dir
    except zipfile.BadZipFile:
        raise Exception(f"Invalid zip file: {zip_path}")
    except Exception as e:
        raise Exception(f"Failed to extract GTFS from {zip_path}: {str(e)}")


def validate_gtfs(directory):
    """
    Check if the extracted directory contains all required GTFS files.

    Args:
        directory (str): Path to directory containing GTFS files

    Returns:
        bool: True if all required files are present

    Raises:
        Exception: If any required GTFS files are missing
    """
    req_files = [
        'agency.txt', 'stops.txt', 'routes.txt',
        'trips.txt', 'stop_times.txt']

    missing_files = []

    for filename in req_files:
        file_path = os.path.join(directory, filename)

        if not os.path.isfile(file_path):
            missing_files.append(filename)

    if missing_files:
        raise Exception(f"Missing required GTFS files: {', '.join(missing_files)}")

    return True

def load_gtfs_from_url(url):
    """
    Complete pipeline: download, extract, and validate GTFS data from a URL.

    Args:
        url (str): URL to GTFS file

    Returns:
        str: Path to the directory containing validated GTFS files

    Raises:
        Exception: If download, extraction, or validation fails
    """
    zip_path = download_gtfs(url)
    gtfs_dir = extract_gtfs(zip_path)
    validate_gtfs(gtfs_dir)
    return gtfs_dir

if __name__ == "__main__":
    url = 'https://www.viainfo.net/BusService/google_transit.zip'

    print("Downloading...")
    zip_path = download_gtfs(url)
    print(f"✓ Downloaded to: {zip_path}")

    print("\nExtracting...")
    gtfs_dir = extract_gtfs(zip_path)
    print(f"✓ Extracted to: {gtfs_dir}")

    print("\nValidating...")
    validate_gtfs(gtfs_dir)
    print("✓ All required files present!")

    # See what files we got
    files = os.listdir(gtfs_dir)
    print(f"\nFiles found: {files}")