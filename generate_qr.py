import qrcode
import uuid
from datetime import datetime, timedelta

# Set expiry duration (in minutes)
expiry_minutes = 10
expiry_time = (now + timedelta(minutes=expiry_minutes)).isoformat() + "Z" # type: ignore


# Generate a unique ID
uid = str(uuid.uuid4())

# Get current timestamp and calculate expiry
now = datetime.utcnow()
expiry_time = now + timedelta(minutes=expiry_minutes)
ts = expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format

# Construct the secure URL with timestamp
secure_url = f"http://localhost:5000/verify.html?id={uid}&ts={ts}"

# Generate QR code
img = qrcode.make(secure_url)
filename = f"{uid}.png"
img.save(filename)

print(f"✅ QR Code generated: {filename}")
print(f"🔗 URL encoded in QR: {secure_url}")
