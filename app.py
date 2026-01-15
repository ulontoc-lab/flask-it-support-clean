import os
import json
import base64
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_from_directory
import gspread

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
            ticket_data = [
                request.form.get("name"),
                request.form.get("email"),
                request.form.get("office"),
                request.form.get("category"),
                request.form.get("priority"),
                request.form.get("description")
            ]

            # Run Google Sheets write in background
            Thread(target=save_ticket_to_sheet, args=(ticket_data,), daemon=True).start()

            return jsonify({"success": True})

        except Exception as e:
            print("❌ Submit error:", e)
            return jsonify({"success": False, "error": "Failed to submit ticket"}), 500

    return render_template("ticket.html")

@app.route("/track")
def track_ticket():
    return "<h3>Tracking page coming soon!</h3>"

# -----------------------------
# Favicon route (optional but clean)
# -----------------------------
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
