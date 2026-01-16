import os
import json
import base64
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_from_directory
import gspread
import uuid
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# Google Sheets setup
# -----------------------------
credentials_b64 = os.environ.get("GOOGLE_CREDENTIALS")
if not credentials_b64:
    raise Exception("Environment variable GOOGLE_CREDENTIALS not found!")

credentials_json = json.loads(base64.b64decode(credentials_b64))
gc = gspread.service_account_from_dict(credentials_json)

SPREADSHEET_NAME = "IT_Tickets"
sheet = gc.open(SPREADSHEET_NAME).sheet1

# -----------------------------
# Background task
# -----------------------------
def save_ticket_to_sheet(data):
    try:
        sheet.append_row(data)
    except Exception as e:
        print("❌ Error saving ticket:", e)

# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def submit_ticket():
    if request.method == "POST":
        try:
            # Generate 8-character Ticket ID
            ticket_id = uuid.uuid4().hex[:8]

            # Timestamp
            date_created = datetime.now().strftime("%Y-%m-%d %H:%M")

            # Row structure must match Google Sheet
            ticket_data = [
                ticket_id,                         # Ticket ID
                request.form.get("name"),          # Name
                request.form.get("office"),        # Office
                request.form.get("category"),      # Category
                request.form.get("priority"),      # Priority
                request.form.get("description"),   # Description
                "New",                             # Status
                "",                                 # Assigned To
                "",                                 # Remarks
                date_created,                       # Date Created
                "",                                 # Last Updated
                request.form.get("email")           # Email
            ]

            # Save in background thread
            Thread(target=save_ticket_to_sheet, args=(ticket_data,), daemon=True).start()

            # Return Ticket ID to frontend
            return jsonify({"success": True, "ticket_id": ticket_id})

        except Exception as e:
            print("❌ Submit error:", e)
            return jsonify({"success": False, "error": "Failed to submit ticket"}), 500

    return render_template("ticket.html")

@app.route("/track")
def track_ticket():
    return "<h3>Tracking page coming soon!</h3>"

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.static_folder,
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
