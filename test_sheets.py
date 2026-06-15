import gspread
from google.oauth2.service_account import Credentials
import sys

SPREADSHEET_ID = "1bsbCYg1Y2yjlsEPuHbEjJBTb0ycHAPhWxzH1WXKHWw0"
SHEET_NAME = "Registrations"
GOOGLE_SHEETS_CREDENTIALS_FILE = "credentials.json"

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
try:
    creds = Credentials.from_service_account_file(
        GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=scopes
    )
    client = gspread.authorize(creds)
    print("Authorized.")
    
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        print("Opened Spreadsheet.")
    except Exception as e:
        print("FAILED TO OPEN SPREADSHEET:", type(e), e)
        sys.exit(1)
        
    try:
        sheet = sh.worksheet(SHEET_NAME)
        print("Opened Worksheet:", SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print("Worksheet not found. Opening first sheet...")
        sheet = sh.sheet1
        print("Opened first sheet:", sheet.title)
        
except Exception as e:
    print("ERROR:", type(e), e)
