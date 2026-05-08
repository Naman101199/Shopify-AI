"""
Step 1 of the daily pipeline - run this script first.

It finds new cafes via Google Places API, scrapes contact emails,
and writes results to discovery_output.json for Claude to act on.

Usage:
    cd cafe-outreach
    python run_discovery.py
"""

import json
import logging
import os
from datetime import date

from dotenv import load_dotenv

from pipeline.cafe_finder import find_new_cafes
from pipeline.contact_finder import find_contact_email
from pipeline.email_drafter import generate_email
from pipeline.lead_tracker import load_leads, get_existing_place_ids, get_existing_cafe_names, save_lead

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "discovery_output.json")


def run():
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    target = int(os.environ.get("DAILY_TARGET", 10))

    if not api_key:
        log.error("GOOGLE_PLACES_API_KEY not set in .env")
        return

    log.info("===== Discovery started (target: %d cafes) =====", target)

    leads = load_leads()
    existing_ids = get_existing_place_ids(leads)
    existing_names = get_existing_cafe_names(leads)
    log.info("Existing leads: %d", len(leads))

    # Find new cafes
    cafes = find_new_cafes(api_key, existing_ids, target=target)
    log.info("Found %d new cafes", len(cafes))

    results = []
    for cafe in cafes:
        name = cafe["name"]
        if name.strip().lower() in existing_names:
            log.info("Skipping duplicate: %s", name)
            continue

        # Save immediately as Identified so reruns don't re-fetch
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
            "Date Contacted": date.today().isoformat(),
            "Date Followed Up": "",
            "Notes": "",
            "Place ID": cafe["place_id"],
            "Gmail Draft ID": "",
        })
        existing_names.add(name.strip().lower())

        # Find email
        email = find_contact_email(cafe["website"])

        # Generate email content
        subject, body = generate_email(cafe_name=name)

        results.append({
            "place_id": cafe["place_id"],
            "cafe_name": name,
            "area": area,
            "website": cafe["website"],
            "contact_email": email,
            "subject": subject,
            "body": body,
            "has_email": bool(email),
        })

    # Write output for Claude
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": date.today().isoformat(), "cafes": results}, f, indent=2)

    with_email = sum(1 for r in results if r["has_email"])
    log.info("===== Discovery done. %d cafes | %d with email | Output: %s =====",
             len(results), with_email, OUTPUT_FILE)

    return results


def _extract_area(address: str) -> str:
    parts = [p.strip() for p in address.split(",")]
    return parts[1] if len(parts) > 1 else parts[0]


if __name__ == "__main__":
    run()
