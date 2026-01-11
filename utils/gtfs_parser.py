import pandas as pd
import os
from datetime import datetime


def load_gtfs_tables(directory):
    """
    Load all GTFS .txt files into a dictionary of DataFrames.

    Args:
        directory (str): Path to directory containing GTFS files

    Returns:
        dict: Dictionary with table names as keys and DataFrames as values
              Example: {'stops': DataFrame, 'routes': DataFrame, ...}
    """
    req_files = ['agency.txt', 'stops.txt', 'routes.txt', 'trips.txt',
                 'stop_times.txt']
    optional_files = ['calendar.txt', 'calendar_dates.txt',
                      'shapes.txt', 'frequencies.txt', 'transfers.txt']

    gtfs_data = {}

    for file in (req_files + optional_files):
        file_path = os.path.join(directory, file)

        if os.path.isfile(file_path):
            # Remove .txt to get table name
            table_name = file.replace('.txt', '')

            # Load CSV and strip whitespace from column names
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()

            gtfs_data[table_name] = df

    return gtfs_data


def get_active_service(gtfs_data, date):
    """
    Determine which service_ids are active on a specific date.

    Args:
        gtfs_data (dict): Dictionary of GTFS DataFrames
        date (str or datetime): Date to check (format: 'YYYY-MM-DD' if string)

    Returns:
        list: List of active service_ids for that date
    """
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')

    day_name = date.strftime('%A').lower()
    active_services = set()

    # check regular calendar
    if 'calendar' in gtfs_data:
        calendar = gtfs_data['calendar'].copy()

        # Convert GTFS date strings to datetime
        calendar['start_date'] = pd.to_datetime(calendar['start_date'], format='%Y%m%d')
        calendar['end_date'] = pd.to_datetime(calendar['end_date'], format='%Y%m%d')

        # Filter for services active on this date and day of week
        mask = (calendar['start_date'] <= date) & \
               (calendar['end_date'] >= date) & \
               (calendar[day_name] == 1)

        active_calendar = calendar[mask]
        active_services = active_calendar['service_id'].tolist()

        # Check exceptions in calendar_dates
        if 'calendar_dates' in gtfs_data:
            calendar_dates = gtfs_data['calendar_dates'].copy()

            # Convert date column
            calendar_dates['date'] = pd.to_datetime(calendar_dates['date'], format='%Y%m%d')

            # Filter for this specific date
            exceptions = calendar_dates[calendar_dates['date'] == date]

            # Apply exceptions
            for _, row in exceptions.iterrows():
                if row['exception_type'] == 1:
                    active_services.add(row['service_id'])
                elif row['exception_type'] == 2:
                    active_services.discard(row['service_id'])

    return list(active_services)


if __name__ == "__main__":
    from data_loader import load_gtfs_from_url

    url = 'https://www.viainfo.net/BusService/google_transit.zip'
    gtfs_dir = load_gtfs_from_url(url)
    gtfs_data = load_gtfs_tables(gtfs_dir)

    # Test with today's date
    active = get_active_service(gtfs_data, '2025-12-22')
    print(f"Active service_ids on 2025-12-22: {active}")
    print(f"Total: {len(active)} services")