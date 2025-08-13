import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_URL = "https://docs.google.com/spreadsheets/d/1UlJrQKXtduUPm6Da109S06uSdRX4d_VILQksfl4m3uw"
SHEET_NAME = "dab_converter_historical_dataset"

def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('dab-467520-64ee0ccc8d49.json', scope)
    client = gspread.authorize(creds)
    return client

def load_sheets_data():
    client = get_gspread_client()
    sheet = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    # Ensure boolean
    if 'ZVS_status' in df.columns:
        df['ZVS_status'] = df['ZVS_status'].apply(lambda x: str(x).lower() in ['true', '1'])
    return df


def append_row_to_sheet(row):
    client = get_gspread_client()
    sheet = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)
    sheet.append_row(row, value_input_option="USER_ENTERED")
