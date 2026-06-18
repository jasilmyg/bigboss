import os
import base64

file_path = "c:\\Users\\jasil_myg\\Desktop\\BIGBOSS\\server.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace get_sheet()
new_get_sheet = """def get_sheet():
    global _sheet
    if _sheet is not None:
        return _sheet
    try:
        if os.environ.get("GOOGLE_CREDENTIALS_JSON"):
            import json
            creds_info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
            credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        else:
            credentials = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
            
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        _sheet = sheet
        return sheet
    except Exception as e:
        print(f"[Sheets] Could not connect: {e}")
        return None"""

content = content.split("def get_sheet():")[0] + new_get_sheet + content.split("return None", 1)[1][len("return None"):]


# Replace get_drive_service()
new_drive_auth = """def get_drive_service():
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = None
        
        # Load from base64 env var if exists
        import base64
        import tempfile
        import json
        if os.environ.get("TOKEN_PICKLE_B64"):
            creds = pickle.loads(base64.b64decode(os.environ.get("TOKEN_PICKLE_B64")))
        elif os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # If running on Render, we MUST have token in env! Local fallback below.
                if os.environ.get("CLIENT_SECRET_JSON"):
                    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
                        f.write(os.environ.get("CLIENT_SECRET_JSON"))
                        secret_file = f.name
                else:
                    secret_file = 'client_secret.json'
                    
                flow = InstalledAppFlow.from_client_secrets_file(secret_file, scopes)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"[Drive] Auth failed: {e}")
        return None"""

# Remove old get_drive_service blocks
import re
content = re.sub(r"def get_drive_service\(\):.*?return None", "", content, flags=re.DOTALL)

# Insert the new one before upload_to_drive
content = content.replace("def upload_to_drive", new_drive_auth + "\n\ndef upload_to_drive")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

# Now, generate the base64 string for token.pickle
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    with open('render_secrets.txt', 'w', encoding='utf-8') as f:
        f.write("=== TOKEN_PICKLE_B64 ===\n")
        f.write(b64 + "\n\n")

if os.path.exists('credentials.json'):
    with open('credentials.json', 'r', encoding='utf-8') as f:
        j = f.read()
    with open('render_secrets.txt', 'a', encoding='utf-8') as f:
        f.write("=== GOOGLE_CREDENTIALS_JSON ===\n")
        f.write(j + "\n\n")

if os.path.exists('client_secret.json'):
    with open('client_secret.json', 'r', encoding='utf-8') as f:
        c = f.read()
    with open('render_secrets.txt', 'a', encoding='utf-8') as f:
        f.write("=== CLIENT_SECRET_JSON ===\n")
        f.write(c + "\n\n")

print("Patched server.py and generated render_secrets.txt!")
