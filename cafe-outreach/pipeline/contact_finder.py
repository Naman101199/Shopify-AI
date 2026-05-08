import logging
import re

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
INSTAGRAM_RE = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)")

BLOCKED_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "schema.org",
    "w3.org", "cloudflare.com", "jquery.com", "googleapis.com",
    "squarespace.com", "wordpress.com", "shopify.com",
}

BLOCKED_IG_HANDLES = {"p", "reel", "reels", "explore", "stories", "accounts", "sharer"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CUSTOM_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


def find_contact_info(website_url: str, cafe_name: str, api_key: str = "", search_cx: str = "") -> dict:
    """Returns dict with 'email' and 'instagram' keys."""
    result = {"email": "", "instagram": ""}

    # --- Step 1: Scrape website for email + Instagram ---
    if website_url:
        base = website_url.rstrip("/")
        pages = [base, f"{base}/contact", f"{base}/contact-us", f"{base}/about", f"{base}/reach-us"]
        for url in pages:
            page_result = _scrape_page(url)
            if page_result["email"] and not result["email"]:
                result["email"] = page_result["email"]
                log.info("  Email found on website: %s", result["email"])
            if page_result["instagram"] and not result["instagram"]:
                result["instagram"] = page_result["instagram"]
                log.info("  Instagram found on website: @%s", result["instagram"])
            if result["email"] and result["instagram"]:
                break

    # --- Step 2: Google Custom Search for email (if not found yet) ---
    if not result["email"] and api_key and search_cx:
        email = _google_search_email(cafe_name, api_key, search_cx)
        if email:
            result["email"] = email
            log.info("  Email found via Google search: %s", email)

    # --- Step 3: Google Custom Search for Instagram (if not found yet) ---
    if not result["instagram"] and api_key and search_cx:
        handle = _google_search_instagram(cafe_name, api_key, search_cx)
        if handle:
            result["instagram"] = handle
            log.info("  Instagram found via Google search: @%s", handle)

    if not result["email"] and not result["instagram"]:
        log.info("  No contact info found for %s", cafe_name)

    return result


def _scrape_page(url: str) -> dict:
    out = {"email": "", "instagram": ""}
    try:
        r = requests.get(url, timeout=8, headers=HEADERS, allow_redirects=True)
        if r.status_code != 200:
            return out
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:") and not out["email"]:
                email = href[7:].split("?")[0].strip().lower()
                if _valid_email(email):
                    out["email"] = email
            if "instagram.com/" in href and not out["instagram"]:
                handle = _extract_ig_handle(href)
                if handle:
                    out["instagram"] = handle

        # Text scan for emails
        if not out["email"]:
            for email in EMAIL_RE.findall(r.text):
                if _valid_email(email.lower()):
                    out["email"] = email.lower()
                    break

        # Text scan for Instagram
        if not out["instagram"]:
            matches = INSTAGRAM_RE.findall(r.text)
            for handle in matches:
                if handle.lower() not in BLOCKED_IG_HANDLES:
                    out["instagram"] = handle
                    break

    except Exception as exc:
        log.debug("Scrape failed for %s: %s", url, exc)
    return out


def _google_search_email(cafe_name: str, api_key: str, cx: str) -> str:
    query = f'"{cafe_name}" bangalore email contact'
    try:
        resp = requests.get(
            CUSTOM_SEARCH_URL,
            params={"q": query, "key": api_key, "cx": cx, "num": 5},
            timeout=10,
        )
        if resp.status_code != 200:
            return ""
        items = resp.json().get("items", [])
        text = " ".join(i.get("snippet", "") for i in items)
        for email in EMAIL_RE.findall(text):
            if _valid_email(email.lower()):
                return email.lower()
    except Exception as exc:
        log.debug("Google search email failed: %s", exc)
    return ""


def _google_search_instagram(cafe_name: str, api_key: str, cx: str) -> str:
    query = f'"{cafe_name}" bangalore site:instagram.com'
    try:
        resp = requests.get(
            CUSTOM_SEARCH_URL,
            params={"q": query, "key": api_key, "cx": cx, "num": 3},
            timeout=10,
        )
        if resp.status_code != 200:
            return ""
        items = resp.json().get("items", [])
        for item in items:
            link = item.get("link", "")
            handle = _extract_ig_handle(link)
            if handle:
                return handle
    except Exception as exc:
        log.debug("Google search Instagram failed: %s", exc)
    return ""


def _extract_ig_handle(url: str) -> str:
    m = INSTAGRAM_RE.search(url)
    if m:
        handle = m.group(1).rstrip("/")
        if handle.lower() not in BLOCKED_IG_HANDLES and len(handle) > 1:
            return handle
    return ""


def _valid_email(email: str) -> bool:
    if "@" not in email:
        return False
    domain = email.split("@")[-1]
    return domain not in BLOCKED_DOMAINS and "." in domain
