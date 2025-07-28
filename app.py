from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
from flask_cors import CORS
from PIL import Image
import imagehash
import base64
import io
import os
import json
import csv
from datetime import datetime, timezone
import logging

app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app, supports_credentials=True)

# In-memory DB
fingerprints = {}
metadata = {}

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secure123"

# Logging setup
logging.basicConfig(level=logging.INFO)

# ✅ Log every scan attempt to JSON
def log_scan(uid, status, msg, device_id, location):
    log_entry = {
        "uid": uid,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "message": msg,
        "device_id": device_id,
        "location": location
    }

    try:
        if os.path.exists("scan_history.json"):
            with open("scan_history.json", "r") as f:
                history = json.load(f)
        else:
            history = []

        history.append(log_entry)

        with open("scan_history.json", "w") as f:
            json.dump(history, f, indent=4)

    except Exception as e:
        print(f"[ERROR LOGGING] {e}")

# ✅ Homepage Route
@app.route('/')
def home():
    return render_template('login.html')  # Or use 'verify.html' as default

# ✅ Verification Endpoint
@app.route('/api/verify', methods=['POST'])
def verify():
    try:
        data = request.get_json()
        uid = data['uid']
        ts = data.get('ts')
        image_data = data['image'].split(',')[1]
        device_id = data.get('device_id')
        location = data.get('location')

        # Expiry Check (5 mins)
        if ts:
            ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if (now - ts_dt).total_seconds() > 300:
                logging.warning(f"[EXPIRED] UID {uid} expired.")
                log_scan(uid, "fail", "Expired", device_id, location)
                return jsonify({"status": "fail", "msg": "⏱️ QR Code Expired."})

        # Fingerprint Check
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        hash_val = str(imagehash.phash(image))

        # First-time scan
        if uid not in fingerprints:
            fingerprints[uid] = hash_val
            metadata[uid] = {
                "device_id": device_id,
                "location": location,
                "timestamp": ts
            }
            logging.info(f"[REGISTERED] {uid} with hash {hash_val}")
            log_scan(uid, "ok", "First scan", device_id, location)
            return jsonify({"status": "ok", "msg": "✅ Registered. First scan recorded."})

        # Device/Location check
        prev_meta = metadata[uid]
        if device_id != prev_meta['device_id'] or location != prev_meta['location']:
            logging.warning(f"[DEVICE/LOCATION MISMATCH] UID {uid}")
            log_scan(uid, "fail", "Device/Location mismatch", device_id, location)
            return jsonify({"status": "fail", "msg": "📍 QR scanned from different device or location."})

        # Hash Match
        if fingerprints[uid] == hash_val:
            logging.info(f"[VERIFIED] UID {uid} matched.")
            log_scan(uid, "ok", "Genuine", device_id, location)
            return jsonify({"status": "ok", "msg": "✅ Genuine QR Code."})
        else:
            logging.warning(f"[HASH MISMATCH] UID {uid} failed.")
            log_scan(uid, "fail", "Hash mismatch", device_id, location)
            return jsonify({"status": "fail", "msg": "❌ Tampered / Copied QR Code."})

    except Exception as e:
        logging.error(f"[ERROR] {str(e)}")
        return jsonify({"status": "fail", "msg": "❌ Error occurred during verification."})

# ✅ Serve the Verify Page
@app.route('/verify.html')
def serve_verify_page():
    return render_template('verify.html')

#
