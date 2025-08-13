from src.sheets_loader import load_sheets_data

SHEET_URL = "https://docs.google.com/spreadsheets/d/1UlJrQKXtduUPm6Da109S06uSdRX4d_VILQksfl4m3uw"
SHEET_NAME = "dab_converter_historical_dataset"

def load_data():
    df = load_sheets_data(SHEET_URL, SHEET_NAME)
    # ...optional: enrich/validate/convert data...
    return df