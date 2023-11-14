import os
import pandas as pd
import io
import aiofiles

async def read_file_for_Imeis(file_path):
    """
    Reads a file asynchronously and returns a list of column data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist. Please check the file path and try again.")
    
    file_extension = file_path.split('.')[-1].lower()
    
    if file_extension not in ['csv', 'xlsx']:
        raise ValueError("Invalid file extension")

    try:
        if file_extension == 'csv':
            async with aiofiles.open(file_path, mode='r') as file:
                data = await file.read()
            df = pd.read_csv(io.StringIO(data), header=0)
            imei_column = next((col for col in df.columns if str(col).lower() == 'imei'), 0)
            if imei_column == 0:
                df = pd.read_csv(io.StringIO(data), header=None)
        elif file_extension == 'xlsx':
            # aiofiles does not support xlsx, so we will use standard read
            df = pd.read_excel(file_path, header=0, dtype=str)
            imei_column = next((col for col in df.columns if str(col).lower() == 'imei'), 'IMEI')
        else:
            raise ValueError("Invalid file extension")

        start_index = 1 if imei_column == 'IMEI' else 0
        imei_list = df[imei_column].iloc[start_index:].astype(str).tolist()
        
        return imei_list
    except Exception as e:
        raise ValueError(f"Error processing file: {e}")


async def reading_file_for_IMEI_and_settings(file_path, second_column_index=1):
    """
    Reads a file asynchronously and returns a list of column data for 'IMEI' and a second column.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist. Please check the file path and try again.")
    
    file_extension = file_path.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            async with aiofiles.open(file_path, mode='r') as file:
                data = await file.read()
            df = pd.read_csv(io.StringIO(data), header=0)
            imei_column = next((col for col in df.columns if 'imei' in str(col).lower()), None)
            if imei_column is None:
                df = pd.read_csv(io.StringIO(data), header=None)
                imei_column = df.columns[0]
        elif file_extension == 'xlsx':
            # aiofiles does not support xlsx, so we will use standard read
            df = pd.read_excel(file_path, header=0, dtype=str)
            imei_column = next((col for col in df.columns if 'imei' in str(col).lower()), None)
            if imei_column is None:
                raise ValueError("IMEI column not found")
        else:
            raise ValueError("Invalid file extension")

        if isinstance(second_column_index, int) and second_column_index < len(df.columns):
            second_column = df.columns[second_column_index]
        else:
            raise ValueError("Second column index is out of range or invalid")

        imei_data = df[imei_column].astype(str).tolist()
        second_column_data = df[second_column].astype(str).tolist()

        return imei_data, second_column_data
    except Exception as e:
        raise ValueError(f"Error processing file: {e}")
