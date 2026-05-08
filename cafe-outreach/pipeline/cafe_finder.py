import logging
import time

import requests

log = logging.getLogger(__name__)

PLACES_TEXT_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"

SEARCH_QUERIES = [
    "smoothie bowl cafe Bangalore",
    "acai bowl cafe Bangalore",
    "healthy bowl cafe Koramangala Bangalore",
    "smoothie bowl cafe Indiranagar Bangalore",
    "wellness cafe bowl Bangalore",
    "health food cafe smoothie Bangalore",
    "bowl cafe HSR Layout Bangalore",
    "acai smoothie cafe Jayanagar Bangalore",
]

DETAIL_FIELDS = "name,formatted_address,website,formatted_phone_number"


def find_new_cafes(api_key: str, existing_place_ids: set, target: int = 10) -> list:
    cafes = []
    seen = set(existing_place_ids)

    for query in SEARCH_QUERIES:
        if len(cafes) >= target:
            break

        try:
            resp = requests.get(
                PLACES_TEXT_SEARCH,
                params={"query": query, "key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

            for place in results:
                if len(cafes) >= target:
                    break
                pid = place.get("place_id", "")
                if not pid or pid in seen:
                    continue
                seen.add(pid)

                details = _get_details(api_key, pid)
                if not details:
                    continue

                cafes.append({
                    "place_id": pid,
                    "name": details.get("name", ""),
                    "address": details.get("formatted_address", ""),
                    "website": details.get("website", ""),
                    "phone": details.get("formatted_phone_number", ""),
                })
                log.info("  Found: %s", details.get("name", pid))
                time.sleep(0.2)

        except Exception as exc:
            log.warning("Error on query '%s': %s", query, exc)

    return cafes


def _get_details(api_key: str, place_id: str) -> dict:
    try:
        resp = requests.get(
            PLACES_DETAILS,
            params={"place_id": place_id, "fields": DETAIL_FIELDS, "key": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("result", {})
    except Exception as exc:
        log.debug("Details fetch failed for %s: %s", place_id, exc)
        return {}
