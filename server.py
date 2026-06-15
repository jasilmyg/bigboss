from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os
import json
import random
import time
from datetime import datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import gspread


# ─────────────────────────────────────────────
# Google Sheets integration (plug in your creds
# when ready – just fill the constants below)
# ─────────────────────────────────────────────
GOOGLE_SHEETS_CREDENTIALS_FILE = "credentials.json"   # service-account JSON
SPREADSHEET_ID = "1bsbCYg1Y2yjlsEPuHbEjJBTb0ycHAPhWxzH1WXKHWw0"           # from the sheet URL
SHEET_NAME = "Registrations"
_sheet = None

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    global _sheet
    if _sheet is not None:
        return _sheet, ""
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
        return sheet, ""
    except Exception as e:
        return None, f"Could not connect: {str(e)}"

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

def get_drive_service():
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
        return None

def upload_to_drive(file_path, original_filename):
    service = get_drive_service()
    if not service:
        return ""
    try:
        file_metadata = {'name': original_filename, 'parents': ['1jGAYXpEs5nz0VsF0qSN0Kw79A7cI_6s2']}
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
        
        # Make the file publicly accessible so anyone with the link can view
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'},
            supportsAllDrives=True
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        print(f"[Drive] Upload failed: {e}")
        return ""


def append_to_sheet(data: dict):
    """Append one registration row to the Google Sheet."""
    try:
        sheet, err = get_sheet()
        if sheet is None:
            return False, f"Sheet config error: {err}"

        # Ensure header row exists
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "Timestamp":
            sheet.insert_row(
                [
                    "Timestamp", "Full Name", "Contact Number",
                    "Age", "Gender", "Email", "City",
                    "About Yourself", "Video Filename",
                    "Consent 1", "Consent 2",
                ],
                index=1,
            )

        row = [
            data.get("timestamp", ""),
            data.get("fullName", ""),
            data.get("contactNumber", ""),
            data.get("age", ""),
            data.get("gender", ""),
            data.get("email", ""),
            data.get("city", ""),
            data.get("aboutYourself", ""),
            data.get("videoFilename", ""),
            data.get("consent1", ""),
            data.get("consent2", ""),
        ]
        sheet.append_row(row)
        return True, ""
    except Exception as e:
        return False, f"Append failed: {str(e)}"


# ─────────────────────────────────────────────
# OTP store (in-memory; swap for Redis/DB later)
# ─────────────────────────────────────────────
otp_store = {}   # { phone: { "otp": "123456", "expires": timestamp } }

# ─────────────────────────────────────────────
# Flask app
# ─────────────────────────────────────────────
app = Flask(__name__, static_folder="static", template_folder=".")
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB


@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/")
def landing():
    return send_from_directory(".", "index.html")


@app.route("/register")
def register_page():
    return send_from_directory(".", "register.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


# ── OTP endpoints ─────────────────────────────
@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "").strip()

    if not phone or len(phone) != 10 or not phone.isdigit():
        return jsonify({"success": False, "message": "Enter a valid 10-digit mobile number."}), 400

    otp = str(random.randint(100000, 999999))
    otp_store[phone] = {"otp": otp, "expires": time.time() + 300}  # 5-min TTL

    # TODO: integrate real SMS gateway (Twilio / MSG91 / etc.)
    print(f"[OTP] Phone: {phone}  OTP: {otp}")

    return jsonify({
        "success": True,
        "message": f"OTP sent to {phone}.",
        "dev_otp": otp,          # remove this line in production
    })


@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "").strip()
    otp   = data.get("otp",   "").strip()

    record = otp_store.get(phone)
    if not record:
        return jsonify({"success": False, "message": "No OTP found. Please request a new one."}), 400
    if time.time() > record["expires"]:
        return jsonify({"success": False, "message": "OTP expired. Please request a new one."}), 400
    if record["otp"] != otp:
        return jsonify({"success": False, "message": "Incorrect OTP."}), 400

    return jsonify({"success": True, "message": "Phone verified successfully."})


# ── Registration submission ───────────────────
@app.route("/api/register", methods=["POST"])
def register():
    try:
        return _register_impl()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500

def _register_impl():
    # multipart/form-data (video upload)
    full_name      = request.form.get("fullName", "").strip()
    contact_number = request.form.get("contactNumber", "").strip()
    age            = request.form.get("age", "").strip()
    gender         = request.form.get("gender", "").strip()
    email          = request.form.get("email", "").strip()
    city           = request.form.get("city", "").strip()
    about          = request.form.get("aboutYourself", "").strip()
    consent1       = request.form.get("consent1", "").strip()
    consent2       = request.form.get("consent2", "").strip()

    # Basic validation
    errors = []
    if not full_name:       errors.append("Full Name is required.")
    if not contact_number:  errors.append("Contact Number is required.")
    if not age:             errors.append("Age is required.")
    if not gender:          errors.append("Gender is required.")
    if not email:           errors.append("Email is required.")
    if not city:            errors.append("City is required.")
    if not about:           errors.append("Tell Us About Yourself is required.")
    if consent1 != "agree": errors.append("You must agree to the participation terms.")
    if consent2 not in ("agree", "agree_disability"):
        errors.append("You must agree to the Privacy Notice.")

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    # Handle video upload
    video_filename = ""
    if "introVideo" in request.files:
        video = request.files["introVideo"]
        if video.filename:
            safe_name = f"{contact_number}_{int(time.time())}_{video.filename}"
            local_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            video.save(local_path)
            
            # Upload to Google Drive using OAuth
            drive_url = upload_to_drive(local_path, safe_name)
            video_filename = drive_url if drive_url else safe_name
            
            if drive_url and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except:
                    pass


    # Build record
    record = {
        "timestamp":     datetime.now().isoformat(sep=" ", timespec="seconds"),
        "fullName":      full_name,
        "contactNumber": contact_number,
        "age":           age,
        "gender":        gender,
        "email":         email,
        "city":          city,
        "aboutYourself": about,
        "videoFilename": video_filename,
        "consent1":      consent1,
        "consent2":      consent2,
    }

    # Save to Google Sheets
    saved, sheet_err = append_to_sheet(record)

    # Always save locally as JSON backup
    try:
        backup_path = os.path.join(os.path.dirname(__file__), "registrations_backup.json")
        backups = []
        if os.path.exists(backup_path):
            with open(backup_path, "r") as f:
                try:
                    backups = json.load(f)
                except Exception:
                    backups = []
        backups.append(record)
        with open(backup_path, "w") as f:
            json.dump(backups, f, indent=2)
    except Exception as e:
        print(f"[Backup] Failed to save backup: {e}")

    print(f"[Register] New entry: {full_name} | {contact_number} | Sheets={saved} | LocalVideo={video_filename}")

    if not saved:
        return jsonify({"success": False, "message": f"Google Sheets Error: {sheet_err}"}), 500

    if video_filename and not video_filename.startswith("http"):
         return jsonify({"success": False, "message": "Failed to upload video to Google Drive. Please try again."}), 500

    return jsonify({
        "success": True,
        "message": "Registration successfully saved to Google Sheets and video uploaded to Google Drive!",
        "saved_to_sheets": saved,
    })


# ── Health check ──────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


if __name__ == "__main__":
    print("=" * 55)
    print("  Bigg Boss Agnipareeksha Registration Server")
    print("  http://127.0.0.1:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)
