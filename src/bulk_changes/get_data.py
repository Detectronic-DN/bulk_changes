import re
from io import StringIO
from typing import Tuple, List, Union

import aiofiles
import asyncio
import pandas as pd

from src.logger.logger import Logger

logger = Logger(__name__)


async def read_file(file_path: str) -> pd.DataFrame:
    """
    Reads an Excel or CSV file and returns the content as a pandas DataFrame.

    :param file_path: The path to the input file. Must be either .xlsx or .csv format.
    :return: A pandas DataFrame containing the file's content.
    :raises ValueError: If the file format is unsupported.
    :raises FileNotFoundError: If the specified file does not exist.
    :raises pd.errors.EmptyDataError: If the file is empty.
    """
    if file_path.lower().endswith(".xlsx"):
        return await asyncio.__all__.to_thread(pd.read_excel, file_path, header=None)
    elif file_path.lower().endswith(".csv"):
        async with aiofiles.open(file_path, mode="r") as f:
            content = await f.read()
        return pd.read_csv(StringIO(content), header=None)
    else:
        raise ValueError(
            "Unsupported file format. Only .xlsx and .csv files are supported."
        )


async def deduplicate_imeis(imei_list: List[str], settings_list: List[str]) -> Tuple[List[str], List[str]]:
    """
    Removes duplicate IMEI numbers from the provided list while maintaining correspondence with settings.

    :param imei_list: A list containing IMEI numbers, possibly with duplicates.
    :param settings_list: A list containing settings corresponding to the IMEI numbers.
    :return: A tuple containing two lists: unique IMEIs and their corresponding settings.
    """
    original_length = len(imei_list)
    unique_imeis = []
    unique_settings = []
    seen = set()

    for imei, setting in zip(imei_list, settings_list):
        if imei not in seen:
            seen.add(imei)
            unique_imeis.append(imei)
            unique_settings.append(setting)

    duplicates_removed = original_length - len(unique_imeis)
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate IMEI numbers.")

    return unique_imeis, unique_settings


async def read_imei_and_setting(file_path: str) -> Tuple[List[str], List[str]]:
    """
    Reads IMEI numbers and settings from an Excel or CSV file.

    :param file_path: The path to the input file. Must be either .xlsx or .csv format.
    :return: A tuple containing two lists:
             - The first list contains unique IMEI numbers.
             - The second list contains corresponding settings (as strings).
    :raises ValueError: If the file format is unsupported or if no IMEI column is found.
    :raises FileNotFoundError: If the specified file does not exist.
    :raises pd.errors.EmptyDataError: If the file is empty.
    """
    df: pd.DataFrame = await read_file(file_path)

    if df.empty:
        raise ValueError("The file contains no data.")

    def is_imei(value: Union[str, int]) -> bool:
        return bool(re.match(r"^\d{15}$", str(value)))

    # Identify IMEI column
    imei_col: Union[int, str, None] = None
    header_present = False

    for col in df.columns:
        if df[col].astype(str).str.lower().eq("imei").any():
            imei_col = col
            header_present = True
            break
        elif df[col].apply(is_imei).any():
            imei_col = col
            break

    if imei_col is None:
        raise ValueError(
            "No IMEI column found. Ensure the file contains a column with 15-digit numbers or a header 'IMEI'."
        )

    # Identify setting column (first non-IMEI column)
    setting_col: Union[int, str, None] = None
    for col in df.columns:
        if col != imei_col:
            setting_col = col
            break

    if setting_col is None:
        raise ValueError(
            "No setting column found. Ensure the file contains at least two columns."
        )

    # Handle header if present
    if header_present:
        header_row = df[df[imei_col].astype(str).str.lower() == "imei"].index[0]
        df.columns = df.iloc[header_row]
        df = df.drop(df.index[:header_row + 1])
        df = df.reset_index(drop=True)

        # Find the new column names for IMEI and settings
        imei_col = next((col for col in df.columns if 'imei' in str(col).lower()), None)
        if imei_col is None:
            raise ValueError("IMEI column not found after processing header.")

        setting_col = next((col for col in df.columns if col != imei_col), None)
        if setting_col is None:
            raise ValueError("Setting column not found after processing header.")

    # Extract IMEIs and settings
    imei_settings = df[[imei_col, setting_col]].dropna()
    ids = imei_settings[imei_col].astype(str).str.extract(r'(\d{15})')[0].dropna().tolist()
    settings = imei_settings[setting_col].dropna().tolist()

    # Deduplicate IMEIs while maintaining correspondence with settings
    unique_ids, unique_settings = await deduplicate_imeis(ids, settings)

    return unique_ids, unique_settings


async def read_imei_only(file_path: str) -> List[str]:
    """
    Reads only IMEI numbers from an Excel or CSV file.

    :param file_path: The path to the input file. Must be either .xlsx or .csv format.
    :return: A list containing unique IMEI numbers.
    :raises ValueError: If the file format is unsupported or if no IMEI column is found.
    :raises FileNotFoundError: If the specified file does not exist.
    :raises pd.errors.EmptyDataError: If the file is empty.
    """
    df: pd.DataFrame = await read_file(file_path)

    if df.empty:
        raise ValueError("The file contains no data.")

    def is_imei(value: Union[str, int]) -> bool:
        return bool(re.match(r"^\d{15}$", str(value)))

    # Identify IMEI column
    imei_col: Union[int, str, None] = None
    header_present = False

    for col in df.columns:
        if df[col].astype(str).str.lower().eq("imei").any():
            imei_col = col
            header_present = True
            break
        elif df[col].apply(is_imei).any():
            imei_col = col
            break

    if imei_col is None:
        raise ValueError(
            "No IMEI column found. Ensure the file contains a column with 15-digit numbers or a header 'IMEI'."
        )

    # Handle header if present
    if header_present:
        header_row = df[df[imei_col].astype(str).str.lower() == "imei"].index[0]
        df.columns = df.iloc[header_row]
        df = df.drop(df.index[:header_row + 1])
        df = df.reset_index(drop=True)

        # Find the new column name for IMEI
        imei_col = next((col for col in df.columns if 'imei' in str(col).lower()), None)
        if imei_col is None:
            raise ValueError("IMEI column not found after processing header.")

    # Extract IMEIs
    imei_list: List[str] = df[imei_col].astype(str).str.extract(r'(\d{15})')[0].dropna().tolist()

    if not imei_list:
        raise ValueError("No valid IMEI numbers found in the file.")

    # Deduplicate IMEIs
    unique_imeis, _ = await deduplicate_imeis(imei_list, imei_list)  # Use imei_list as dummy settings

    return unique_imeis
