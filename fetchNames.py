import os
import requests
import socket
import sys
from datetime import datetime, timedelta

# --- Step 0: Load token ---
token_file = r"C:\Users\matia\OneDrive\Escritorio\Macroglobal\PfIntegration\pFinderHash.txt"
if not os.path.exists(token_file):
    sys.exit(f"❌ Token file not found: {token_file}")
with open(token_file, "r") as f:
    access_token = f.read().strip()
if not access_token:
    sys.exit("❌ Token file is empty")

# --- Step 1: DNS check ---
hostname = "atlas.propertyfinder.com"
try:
    ip = socket.gethostbyname(hostname)
    print(f"✅ Hostname resolved: {hostname} -> {ip}")
except socket.gaierror:
    sys.exit(f"❌ Failed to resolve hostname: {hostname}")

url = f"https://{hostname}/v1/leads"
headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}

# --- Step 2: Fetch all leads (IDs only) ---
now = datetime.utcnow()
last_30_days = now - timedelta(days=30)
params = {
    "perPage": 50,
    "orderBy": "createdAt",
    "orderDirection": "desc",
    "createdAtFrom": last_30_days.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "createdAtTo": now.strftime("%Y-%m-%dT%H:%M:%SZ")
}

all_leads = []
page = 1
while True:
    query_params = [(k, v) for k, v in params.items()] + [("page", page)]
    resp = requests.get(url, headers=headers, params=query_params)
    if resp.status_code != 200:
        sys.exit(f"❌ Failed to fetch leads: {resp.status_code} {resp.text}")
    data = resp.json()
    leads = data.get("data", [])
    if not leads:
        break
    all_leads.extend([lead["id"] for lead in leads])
    print(f"📄 Page {page} fetched, {len(leads)} leads")
    pagination = data.get("pagination", {})
    if not pagination.get("nextPage"):
        break
    page = pagination["nextPage"]

print(f"\n✅ Total lead IDs fetched: {len(all_leads)}")

# --- Step 3: Fetch full details for each lead ---
def fetch_lead_details(lead_id):
    """Fetch the full payload of a single lead by ID."""
    params = {"id": [lead_id], "perPage": 1}
    query_params = [(k, v) for k, v in params.items() if not isinstance(v, list)]
    for k, v in params.items():
        if isinstance(v, list):
            for item in v:
                query_params.append((k, item))
    resp = requests.get(url, headers=headers, params=query_params)
    if resp.status_code != 200:
        print(f"⚠️ Failed to fetch lead {lead_id}: {resp.status_code}")
        return None
    data = resp.json().get("data", [])
    return data[0] if data else None

# Example: fetch detailed info for all leads
for lead_id in all_leads:
    lead = fetch_lead_details(lead_id)
    if lead:
        sender = lead.get("sender", {})
        contacts = sender.get("contacts", [])
        phone = next((c["value"] for c in contacts if c["type"]=="phone"), "N/A")
        email = next((c["value"] for c in contacts if c["type"]=="email"), "N/A")
        name = sender.get("name", "N/A")
        print(
            f"Lead ID: {lead['id']} | Status: {lead.get('status','N/A')} | Channel: {lead.get('channel','N/A')} | "
            f"Sender: {name} | Phone: {phone} | Email: {email}"
        )
