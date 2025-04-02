from flask import Flask, request, redirect, render_template, jsonify, abort
from datetime import datetime
from user_agents import parse
import csv
import requests
import os

app = Flask(__name__)
LOG_FILE = "logs.csv"
ADMIN_TOKEN = "secret123"  # Change this token to something secure in production

def get_geoip(ip):
    """Retrieve geo-location data for a given IP address."""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        return data.get("country", "Unknown"), data.get("city", "Unknown")
    except Exception as e:
        print(f"GeoIP lookup failed: {e}")
        return "Unknown", "Unknown"

def log_request():
    # Get visitor info
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent_str = request.headers.get('User-Agent')
    user_agent = parse(user_agent_str)
    referrer = request.referrer or "Direct"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    country, city = get_geoip(ip)

    # Prepare log data
    log_data = [
        ip,
        country,
        city,
        user_agent.device.family,
        user_agent.os.family,
        user_agent.browser.family,
        referrer,
        timestamp
    ]

    # Append data to the CSV log file
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(log_data)

    print(f"[+] Logged Data: {log_data}")
    return log_data

@app.route('/')
def index():
    log_request()
    # You can either redirect to an external site or show a decoy page.
    return redirect("https://www.wikipedia.org")
    # Or, to show a custom page:
    # return render_template("index.html")

@app.route('/logs')
def view_logs():
    token = request.args.get('token')
    if token != ADMIN_TOKEN:
        abort(403, description="Forbidden: Invalid token")
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
    return render_template("logs.html", logs=logs)

@app.route('/api/logs')
def api_logs():
    token = request.args.get('token')
    if token != ADMIN_TOKEN:
        abort(403, description="Forbidden: Invalid token")
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
    return jsonify(logs)

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    token = request.args.get('token')
    if token != ADMIN_TOKEN:
        abort(403, description="Forbidden: Invalid token")
    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["IP", "Country", "City", "Device", "OS", "Browser", "Referrer", "Timestamp"])
    return "Logs cleared.", 200

@app.route('/status')
def status():
    return "Server is running", 200

if __name__ == '__main__':
    # Ensure log file exists with headers
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["IP", "Country", "City", "Device", "OS", "Browser", "Referrer", "Timestamp"])
    app.run(host='0.0.0.0', port=5000)
