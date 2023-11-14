import pandas as pd

def read_imeis(file_path):
    # Check the file extension
    if file_path.lower().endswith('.xlsx'):
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            return f"Error: {e}"
    elif file_path.lower().endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return f"Error: {e}"
    else:
        return "Error: Unsupported file format. Only .xlsx and .csv files are supported."

    # Check if there is an "IMEI" or "imei" column in the header
    if 'IMEI' in df.columns or 'imei' in df.columns:
        imei_column = df['IMEI'] if 'IMEI' in df.columns else df['imei']
        imeis = imei_column.astype(str).str.extract(r'(\d{15})')
        return [imei for imei_list in imeis.dropna().values.tolist() for imei in imei_list]

    # If there's no header, check for a column with 15-digit numbers
    for col in df.columns:
        imeis = df[col].astype(str).str.extract(r'(\d{15})')
        if not imeis.dropna().empty:
            return [imei for imei_list in imeis.dropna().values.tolist() for imei in imei_list]

    # If no suitable column is found, return an error
    return "Error: No IMEI column or 15-digit number column found."


def read_imei_and_setting(file_path):
    # Check the file extension
    if file_path.lower().endswith('.xlsx'):
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            return f"Error: {e}"
    elif file_path.lower().endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return f"Error: {e}"
    else:
        return "Error: Unsupported file format. Only .xlsx and .csv files are supported."

    # Check if there is an "IMEI" or "imei" column in the header
    if 'IMEI' in df.columns or 'imei' in df.columns:
        imei_column = df['IMEI'] if 'IMEI' in df.columns else df['imei']
        setting_column = df.columns[df.columns != 'IMEI' if 'IMEI' in df.columns else 'imei'][0]
    else:
        # If there's no header, check for a column with 15-digit numbers
        imeis_found = False
        setting_column = None
        for col in df.columns:
            imeis = df[col].astype(str).str.extract(r'(\d{15})')
            if not imeis.dropna().empty:
                imei_column = df[col]
                imeis_found = True
                setting_column = df.columns[df.columns != col][0]

        if not imeis_found:
            return "Error: No IMEI column with 15-digit numbers found."

        if setting_column is None:
            return "Error: No second column found for the setting string."

    # Convert the IMEI and setting columns to lists
    imeis = imei_column.astype(str).str.extract(r'(\d{15})')
    imeis = [imei for imei_list in imeis.dropna().values.tolist() for imei in imei_list]
    settings = df[setting_column].tolist()

    return imeis, settings


