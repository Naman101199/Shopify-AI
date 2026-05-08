"""
Daily pipeline: finds 10 cafes, locates contact emails,
creates personalised Gmail drafts, labels them, and logs everything to cafe-leads.csv.

Run once manually to set up Gmail auth:
    python setup_gmail_auth.py

Then schedule daily:
    bash cron_setup.sh
"""

import logging
import os
from datetime import date

from dotenv import load_dotenv

from pipeline.cafe_finder import find_new_cafes
from pipeline.contact_finder import find_contact_email
from pipeline.email_drafter import generate_email
from pipeline.gmail_client import GmailClient
from pipeline.lead_tracker import (
    load_leads,
    get_existing_place_ids,
    get_existing_cafe_names,
    save_lead,
    update_lead,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "logs", "pipeline.log")),
    ],
)
log = logging.getLogger(__name__)

DAILY_TARGET = int(os.environ.get("DAILY_TARGET", 10))


def run():
    log.info("===== Starting daily cafe outreach pipeline =====")

    places_api_key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    token_path = os.environ.get("GMAIL_TOKEN_PATH", "token.json")
    creds_path = os.environ.get("GMAIL_CREDS_PATH", "credentials.json")

    if not places_api_key:
        log.error("GOOGLE_PLACES_API_KEY not set in .env - aborting")
        return

    gmail = GmailClient(token_path=token_path, creds_path=creds_path)
    gmail.ensure_labels()

    leads = load_leads()
    existing_ids = get_existing_place_ids(leads)
    existing_names = get_existing_cafe_names(leads)
    log.info("Existing leads in tracker: %d", len(leads))

    # --- Step 1: Find cafes ---
    log.info("Searching for new cafes (target: %d)...", DAILY_TARGET)
    cafes = find_new_cafes(places_api_key, existing_ids, target=DAILY_TARGET)
    log.info("Found %d new cafes", len(cafes))

    if not cafes:
        log.info("No new cafes found today. Exiting.")
        return

    drafted = 0
    no_email = 0

    for cafe in cafes:
        name = cafe["name"]

        # Extra dedup by name (catches places without a place_id match)
        if name.strip().lower() in existing_names:
            log.info("Skipping duplicate: %s", name)
            continue

        log.info("Processing: %s", name)

        # --- Step 2: Save as Identified ---
        area = _extract_area(cafe["address"])
        save_lead({
            "Cafe Name": name,
            "Area": area,
            "City": "Bangalore",
            "Instagram": "",
            "Website": cafe["website"],
            "Contact Email": "",
            "Owner/Manager Name": "",
            "Menu Fit (Bowl/Smoothie/Acai)": "Smoothie/Acai Bowls",
            "Outreach Status": "Identified",
            "Date Contacted": "",
            "Date Followed Up": "",
            "Notes": "",
            "Place ID": cafe["place_id"],
            "Gmail Draft ID": "",
        })
        existing_names.add(name.strip().lower())

        # --- Step 3: Find contact email ---
        email = find_contact_email(cafe["website"])
        if not email:
            log.info("  No email found for %s - marked Identified, skipping draft", name)
            no_email += 1
            continue

        # --- Step 4: Generate personalised email ---
        subject, body = generate_email(cafe_name=name)

        # --- Step 5: Create Gmail draft + apply label ---
        draft_id = gmail.create_draft(to=email, subject=subject, body=body)

        # --- Step 6: Update lead tracker ---
        update_lead(cafe["place_id"], {
            "Contact Email": email,
            "Outreach Status": "Draft Created",
            "Date Contacted": date.today().isoformat(),
            "Gmail Draft ID": draft_id,
        })

        drafted += 1
        log.info("  Draft created for %s (%s)", name, email)

    log.info(
        "===== Done. Cafes found: %d | Drafts created: %d | No email: %d =====",
        len(cafes), drafted, no_email,
    )


def _extract_area(address: str) -> str:
    parts = [p.strip() for p in address.split(",")]
    return parts[1] if len(parts) > 1 else parts[0]


if __name__ == "__main__":
    run()
