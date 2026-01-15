import os
import json
from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from utils.emailer import send_email  # Make sure your utils/emailer.py exists

app = Flask(__name__)

# -----------------------------
# Google Sheets Setup
# -----------------------------
# Name of your spreadsheet in Google Drive
SPREADSHEET_NAME = "IT_Tickets"

# Load Google service account credentials from environment variable
if "GOOGLE_CREDENTIALS" not in os.environ:
    raise Exception("Environment variable GOOGLE_CREDENTIALS not found!")

credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
gc = gspread.service_account_from_dict(credentials_info)

# Open spreadsheet and first worksheet
try:
    sheet = gc.open(SPREADSHEET_NAME).sheet1
except gspread.SpreadsheetNotFound:
    raise Exception(
        f"Spreadsheet '{SPREADSHEET_NAME}' not found or not shared with the service account."
    )

# -----------------------------
# Routes
# -----------------------------
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
        sheet.append_row([name, email, office, category, priority, description, "New"])

        # Optional: send email notification
        try:
            send_email(
                subject=f"New IT Ticket from {name}",
                body=f"Category: {category}\nPriority: {priority}\nDescription: {description}",
                to=email
            )
        except Exception as e:
            print("Email sending failed:", e)

        return render_template("success.html", name=name)

    return render_template("ticket.html")


@app.route("/track", methods=["GET", "POST"])
def track():
    tickets = []
    if request.method == "POST":
        email = request.form.get("email")
        all_records = sheet.get_all_records()
        tickets = [r for r in all_records if r.get("Email") == email]

    return render_template("track.html", tickets=tickets)


@app.route("/admin")
def admin():
    all_records = sheet.get_all_records()
    return render_template("admin.html", tickets=all_records)


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
