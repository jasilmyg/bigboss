from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os
import json
import random
import time
import re
from datetime import datetime, timezone, timedelta
import threading

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
        return build('drive', 'v3', credentials=creds), ""
    except Exception as e:
        return None, f"Auth failed: {str(e)}"

def upload_to_drive(file_path, original_filename):
    service, err = get_drive_service()
    if not service:
        return "", f"Drive auth config error: {err}"
    try:
        file_metadata = {'name': original_filename, 'parents': ['1jGAYXpEs5nz0VsF0qSN0Kw79A7cI_6s2']}
        media = MediaFileUpload(file_path, resumable=True, chunksize=1024*1024*5)
        request = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True)
        
        response = None
        while response is None:
            status, response = request.next_chunk(num_retries=10)
            if status:
                print(f"[Drive] Uploading {original_filename}: {int(status.progress() * 100)}%")
                
        # Make the file publicly accessible so anyone with the link can view
        service.permissions().create(
            fileId=response.get('id'),
            body={'type': 'anyone', 'role': 'reader'},
            supportsAllDrives=True
        ).execute(num_retries=5)
        
        return response.get('webViewLink'), ""
    except Exception as e:
        return "", f"Drive upload failed: {str(e)}"


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
def is_already_registered(phone):
    # 1. Check Google Sheet first (so manual deletions allow re-registration)
    try:
        sheet, err = get_sheet()
        if sheet:
            # Column 3 is 'Contact Number'
            registered_phones = sheet.col_values(3)
            if phone in registered_phones:
                return True
            return False  # If Google Sheet check succeeded and it's not there, they are not registered!
    except Exception as e:
        print(f"Sheet duplicate check error: {e}")

    # 2. Fallback to local JSON only if the Google API is unreachable
    try:
        backup_path = os.path.join(os.path.dirname(__file__), "registrations_backup.json")
        if os.path.exists(backup_path):
            with open(backup_path, "r") as f:
                backups = json.load(f)
                for rec in backups:
                    if rec.get("contactNumber") == phone:
                        return True
    except Exception as e:
        print(f"Duplicate check error: {e}")
    return False

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

    if is_already_registered(phone):
        return jsonify({"success": False, "message": "This mobile number has already been registered."}), 400

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
    if not full_name:
        errors.append("Full Name is required.")
        
    if not contact_number or not contact_number.isdigit() or len(contact_number) != 10:
        errors.append("Enter a valid 10-digit mobile number.")
        
    try:
        if not age or int(age) < 18:
            errors.append("You must be at least 18 years old.")
    except ValueError:
        errors.append("Enter a valid numeric age.")
        
    if not gender:
        errors.append("Gender is required.")
        
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append("Enter a valid email address.")
        
    if not city or not re.match(r"^[A-Za-z\s\-]+$", city):
        errors.append("City must contain text only.")
        
    if not about:
        errors.append("Tell Us About Yourself is required.")
        
    if consent1 != "agree":
        errors.append("You must agree to the participation terms.")
        
    if consent2 not in ("agree", "agree_disability"):
        errors.append("You must agree to the Privacy Notice.")
        
    if "introVideo" not in request.files or not request.files["introVideo"].filename:
        errors.append("An intro video is required.")

    if is_already_registered(contact_number):
        errors.append("This mobile number has already been registered.")

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    # Handle video upload locally
    safe_name = ""
    local_path = ""
    if "introVideo" in request.files:
        video = request.files["introVideo"]
        if video.filename:
            safe_name = f"{contact_number}_{int(time.time())}_{video.filename}"
            local_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            video.save(local_path)

    # Build record
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    record = {
        "timestamp":     datetime.now(ist_offset).strftime('%Y-%m-%d %H:%M:%S'),
        "fullName":      full_name,
        "contactNumber": contact_number,
        "age":           age,
        "gender":        gender,
        "email":         email,
        "city":          city,
        "aboutYourself": about,
        "videoFilename": "",
        "consent1":      consent1,
        "consent2":      consent2,
    }

    def process_upload_in_background(rec, path, name, base_url):
        drive_success = False
        try:
            video_filename = ""
            if path and os.path.exists(path):
                drive_url, drive_err = upload_to_drive(path, name)
                
                if drive_err:
                    print(f"[Drive] Upload error: {drive_err}")
                    # FALLBACK: Provide the direct link to the video on this server
                    video_filename = f"{base_url}uploads/{name}"
                else:
                    drive_success = True
                    video_filename = drive_url
                
            rec["videoFilename"] = video_filename
            
            # Save to Google Sheets
            saved, sheet_err = append_to_sheet(rec)
            if not saved:
                print(f"[Sheets] Append error: {sheet_err}")

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
                backups.append(rec)
                with open(backup_path, "w") as f:
                    json.dump(backups, f, indent=2)
            except Exception as e:
                print(f"[Backup] Failed to save backup: {e}")

            print(f"[Register] Processed entry: {rec['fullName']} | {rec['contactNumber']} | Sheets={saved}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Background upload error: {e}")
        finally:
            if path and os.path.exists(path):
                if drive_success:
                    try:
                        os.remove(path)
                    except:
                        pass
                else:
                    print(f"[Important] Drive upload failed, kept the video locally at: {path}")

    base_url = request.url_root
    # Start the background thread so the HTTP response is sent immediately
    thread = threading.Thread(target=process_upload_in_background, args=(record, local_path, safe_name, base_url))
    thread.start()

    return jsonify({
        "success": True,
        "message": "Registration received successfully! Uploading your video in the background...",
        "saved_to_sheets": True,
    })


# ── Health check ──────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


if __name__ == "__main__":
    print("=" * 55)
    print("  Bigg Boss Agnipareeksha Registration Server")
    print("  http://127.0.0.1:7001")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=7001)
