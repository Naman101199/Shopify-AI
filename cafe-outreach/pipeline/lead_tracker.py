import csv
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "cafe-leads.csv")

FIELDNAMES = [
    "Cafe Name", "Area", "City", "Instagram", "Website",
    "Contact Email", "Owner/Manager Name", "Menu Fit (Bowl/Smoothie/Acai)",
    "Outreach Status", "Date Contacted", "Date Followed Up", "Notes",
    "Place ID", "Gmail Draft ID",
]


def load_leads() -> list:
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_existing_place_ids(leads: list) -> set:
    return {row.get("Place ID", "").strip() for row in leads if row.get("Place ID", "").strip()}


def get_existing_cafe_names(leads: list) -> set:
    return {row.get("Cafe Name", "").strip().lower() for row in leads}


def save_lead(lead: dict):
    leads = load_leads()
    leads.append(lead)
    _write(leads)


def update_lead(place_id: str, updates: dict):
    leads = load_leads()
    for row in leads:
        if row.get("Place ID", "").strip() == place_id:
            row.update(updates)
            break
    _write(leads)


def _write(leads: list):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)
