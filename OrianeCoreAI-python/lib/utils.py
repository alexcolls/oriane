import os
import json
import uuid
import errno
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from lib.logs import log


def create_folder(path: str) -> bool:
    """
    Ensures that the directory for the given path exists.
    If the directory does not exist, it is created.
    - Args:
      path (str): The file path where the directory needs to be checked or created.
      It should include a trailing slash if it is meant to be a directory path.
    """
    # Check if the path ends with a slash and handle accordingly
    if not path.endswith("/"):
        path += "/"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return True
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        return False


def fetch_data(url: str) -> dict:
    """
    Fetches data from the given URL or reads from a local file.
    - Args:
      url (str): The URL or file path to fetch data from.
    - Returns:
      dict: The fetched data.
    """
    if os.path.exists(url):
        with open(url, "r") as file:
            return json.load(file)
    else:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


def is_numeric(value: Any) -> bool:
    """
    Determines whether the provided value is numeric.
    - Args:
      value (Any): The value to be checked.
    - Returns:
      bool: True if the value is numeric (int, float, or any NumPy numeric type), otherwise False.
    """
    return isinstance(value, (int, float)) or np.issubdtype(type(value), np.number)


def convert_to_numpy_type(value: Any, data_type: np.dtype) -> Optional[Any]:
    """
    Converts a given value to a specified NumPy data type, safely handling missing values (NaN).
    - Args:
      value (Any): The value to convert.
      data_type (np.dtype): The NumPy data type to which the value should be converted.
    - Returns:
      Optional[Any]: The converted value, or the original value if it is NaN.
    """
    if pd.isna(value):
        return value
    return (np.array([value])).astype(data_type)[0]


def remove_spaces_from_list(item_list: List[str]) -> List[str]:
    """
    Removes spaces and dashes from each string in a given list.
    - Args:
      item_list (List[str]): A list of strings to be processed.
    - Returns:
      List[str]: A list containing the modified strings with spaces and dashes removed.
    """
    return [item.replace(" ", "").replace("-", "") for item in item_list]


def save_to_json_file(data: dict, filename: str, indent=2, logging=True) -> None:
    """
    Save a dictionary to a JSON file.
    - Args:
      data (dict): The dictionary to be saved.
      filename (str): The name of the file to save the dictionary to.
    """
    with open(filename, "w") as file:
        json.dump(data, file, indent=indent)
    if logging:
        log(f"Data saved to {filename}.")


def load_json_file(file_path: str, logging: bool = True) -> Dict[str, Any]:
    """
    Loads a JSON file an returns a dictionary.
    - Args:
      file_path (str): Path to the JSON file containing the standard sizes.
    - Returns:
      Dict[str, int]: Dictionary containing standard sizes.
    """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        if logging:
            log(f"Failed to load json file from {file_path}: {e}", "error")
        return {}


def generate_guid() -> str:
    """Generates a new GUID"""
    return str(uuid.uuid4())


def map_id(old_id: int, id_mapping: Dict[int, str]) -> str:
    """
    Maps an old int ID to a new GUID, creating a new GUID if necessary.
    - Args:
      old_id (int): The old int ID.
    - Returns:
      str: The new GUID.
    """
    if old_id not in id_mapping:
        id_mapping[old_id] = generate_guid()
    return id_mapping[old_id]


def convert_date_format(date_str: str) -> str:
    """
    Converts a date string from 'DD/MM/YYYY' or 'MM/DD/YYYY' to 'YYYY-MM-DD' format.
    - Args:
      date_str (str): The date string to be converted.
    - Returns:
      str: The converted date string in 'YYYY-MM-DD' format.
    """
    try:
        if date_str and isinstance(date_str, str):
            possible_formats = ["%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"]
            for fmt in possible_formats:
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
        return date_str
    except Exception as e:
        log(f"Failed to convert date format for value '{date_str}': {e}", "error")
        return None


def truncate_string(value: str, max_length: int) -> str:
    """
    Truncate the string if it exceeds the maximum allowed length.
    - Args:
      value (str): The string to be truncated.
      max_length (int): The maximum allowed length of the string.
    - Returns:
      str: The truncated string.
    """
    return value[:max_length] if isinstance(value, str) else value


def log_migration_progress(
    migrated_rows: int, total_rows: int, table_name: str
) -> float:
    """
    Logs the migration progress as a percentage with two decimal places.
    - Args:
      migrated_rows (int): The number of rows that have been migrated.
      total_rows (int): The total number of rows to be migrated.
      table_name (str): The name of the table being migrated.
    - Returns:
      float: The migration progress as a percentage with two decimal places.
    """
    progress = (migrated_rows / total_rows) * 100
    progress_rounded = round(progress, 2)
    log(f"Migration progress for {table_name}: {progress_rounded:.2f}%", "info")
    return progress_rounded


def convert_to_int(value: Any) -> int:
    """
    Convert a value to an integer, handling exceptions.
    - Args:
      value (Any): The value to be converted to an integer.
    - Returns:
      int: The converted integer value, or 0 if the conversion fails.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        log(f"Invalid value for conversion to int: {value}. Setting it to 0.", "error")
        return 0


def convert_nparray_to_dictarray(
    data: np.ndarray, column_names: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Converts a numpy array to a list of dictionaries with column name mapping.
    - Args:
      data: The numpy array to convert.
      column_names: An array of column names corresponding to the data.
    - Returns:
      List[Dict[str, Any]]: A list of dictionaries with column names as keys and row values as values.
    """
    return [{col: val for col, val in zip(column_names, row)} for row in data]
