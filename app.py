import os
import json
import base64
from threading import Thread
from flask import Flask, render_template, request

import gspread

app = Flask(__name__)

# -----------------------------
# Google Sheets setup
# -----------------------------
# Environment variable must contain base64-encoded JSON of service account
credentials_b64 = os.environ.get("GOOGLE_CREDENTIALS")
if not credentials_b64:
    raise Exception("Environment variable GOOGLE_CREDENTIALS not found!")

# Decode and load credentials
credentials_json = json.loads(base64.b64decode(credentials_b64))
gc = gspread.service_account_from_dict(credentials_json)

# Open spreadsheet once
SPREADSHEET_NAME = "IT_Tickets"
sheet = gc.open(SPREADSHEET_NAME).sheet1

# -----------------------------
# Helper function
# -----------------------------
def save_ticket_to_sheet(data):
    try:
        sheet.append_row(data)
    except Exception as e:
        print("Error saving ticket:", e)

# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def submit_ticket():
    if request.method == "POST":
        ticket_data = [
            request.form.get("name"),
            request.form.get("email"),
            request.form.get("office"),
            request.form.get("category"),
            request.form.get("priority"),
            request.form.get("description")
        ]
        # Save in background thread for speed
        Thread(target=save_ticket_to_sheet, args=(ticket_data,)).start()
        return "<h3>Ticket submitted successfully!</h3><a href='/'>Submit another ticket</a>"

    return render_template("ticket.html")  # Your HTML form

@app.route("/track")
def track_ticket():
    return "<h3>Tracking page coming soon!</h3>"

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
