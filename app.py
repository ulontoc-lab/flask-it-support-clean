from flask import Flask, render_template, request, redirect, session
import gspread
from datetime import datetime
import uuid
import os
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- CONFIG ----------------
SPREADSHEET_NAME = "IT_Tickets"
CREDENTIAL_FILE = "credentials.json"

HEADERS = [
    "Ticket ID",
    "Name",
    "Office",
    "Category",
    "Priority",
    "Description",
    "Status",
    "Assigned To",
    "Remarks",
    "Date Created",
    "Last Updated",
    "Email"
]

# ---------------- DEBUG ----------------
print("Working directory:", os.getcwd())
print("Credentials found:", os.path.exists(CREDENTIAL_FILE))

# ---------------- GOOGLE SHEETS SETUP ----------------
gc = gspread.service_account(filename=CREDENTIAL_FILE)

# Load the service account email safely
with open(CREDENTIAL_FILE) as f:
    cred_data = json.load(f)
SERVICE_ACCOUNT_EMAIL = cred_data.get("client_email")

def get_sheet():
    """
    Opens the spreadsheet if it exists.
    Raises clear error if missing.
    """
    try:
        sh = gc.open(SPREADSHEET_NAME)
        ws = sh.sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        raise Exception(
            f"Spreadsheet '{SPREADSHEET_NAME}' not found or not shared with the service account.\n"
            f"Please create it manually in Google Drive, add headers in row 1, "
            f"and share it with: {SERVICE_ACCOUNT_EMAIL}"
        )

    # Optional: Check headers
    existing_headers = ws.row_values(1)
    if existing_headers != HEADERS:
        print("Warning: Sheet headers do not match expected headers. Make sure row 1 is:")
        print(HEADERS)

    return ws

# Initialize sheet
sheet = get_sheet()

# ---------------- USER: SUBMIT TICKET ----------------
@app.route("/", methods=["GET", "POST"])
def submit_ticket():
    if request.method == "POST":
        ticket_id = str(uuid.uuid4())[:8]

        sheet.append_row([
            ticket_id,
            request.form["name"],
            request.form["office"],
            request.form["category"],
            request.form["priority"],
            request.form["description"],
            "New",
            "",
            "",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "",
            request.form["email"]
        ])

        return render_template("success.html", ticket_id=ticket_id)

    return render_template("ticket.html")


# ---------------- USER: TRACK TICKET ----------------
@app.route("/track", methods=["GET", "POST"])
def track_ticket():
    ticket = None

    if request.method == "POST":
        ticket_id = request.form["ticket_id"]
        records = sheet.get_all_records()

        for r in records:
            if r["Ticket ID"] == ticket_id:
                ticket = r
                break

    return render_template("track.html", ticket=ticket)


# ---------------- ADMIN LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")


# ---------------- ADMIN PANEL ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    records = sheet.get_all_records()

    if request.method == "POST":
        row = int(request.form["row"])
        sheet.update_cell(row, 7, request.form["status"])
        sheet.update_cell(row, 8, request.form["assigned"])
        sheet.update_cell(row, 9, request.form["remarks"])
        sheet.update_cell(row, 11, datetime.now().strftime("%Y-%m-%d %H:%M"))

    return render_template("admin.html", tickets=records)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
