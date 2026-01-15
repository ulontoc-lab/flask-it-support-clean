import os
import json
from flask import Flask, render_template, request, redirect, url_for
import gspread
from google.oauth2.service_account import Credentials
from utils.emailer import send_email  # your existing email helper

app = Flask(__name__)

# -------------------------------
# Google Sheets setup via ENV
# -------------------------------

CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS")
if not CREDENTIALS_JSON:
    raise Exception("Environment variable GOOGLE_CREDENTIALS not found!")

# Load credentials from the JSON string
credentials_dict = json.loads(CREDENTIALS_JSON)
creds = Credentials.from_service_account_info(credentials_dict)
gc = gspread.Client(auth=creds)
gc.login()

# Your spreadsheet name
SPREADSHEET_NAME = "IT_Tickets"

# Get the sheet
try:
    sheet = gc.open(SPREADSHEET_NAME).sheet1
except gspread.SpreadsheetNotFound:
    raise Exception(
        f"Spreadsheet '{SPREADSHEET_NAME}' not found in your Google Drive. "
        f"Make sure it exists and your service account has access!"
    )

# -------------------------------
# Routes
# -------------------------------

@app.route("/", methods=["GET", "POST"])
def ticket():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        office = request.form.get("office")
        category = request.form.get("category")
        priority = request.form.get("priority")
        description = request.form.get("description")

        # Append ticket to Google Sheet
        sheet.append_row([name, email, office, category, priority, description])

        # Optionally send email
        send_email(email, "Ticket Submitted", f"Hi {name}, your ticket was submitted!")

        return render_template("success.html", name=name)

    return render_template("ticket.html")


@app.route("/track")
def track():
    return render_template("track.html")


@app.route("/admin")
def admin():
    tickets = sheet.get_all_records()
    return render_template("admin.html", tickets=tickets)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
