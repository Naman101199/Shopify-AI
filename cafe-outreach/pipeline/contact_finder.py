import re
import logging

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

BLOCKED_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "schema.org",
    "w3.org", "cloudflare.com", "jquery.com", "googleapis.com",
    "squarespace.com", "wordpress.com", "shopify.com",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def find_contact_email(website_url: str) -> str:
    if not website_url:
        return ""

    base = website_url.rstrip("/")
    pages = [base, f"{base}/contact", f"{base}/contact-us", f"{base}/about"]

    for url in pages:
        email = _scrape_page(url)
        if email:
            log.info("  Email found at %s: %s", url, email)
            return email

    log.info("  No email found for %s", website_url)
    return ""


def _scrape_page(url: str) -> str:
    try:
        r = requests.get(url, timeout=8, headers=HEADERS, allow_redirects=True)
        if r.status_code != 200:
            return ""

        soup = BeautifulSoup(r.text, "html.parser")

        # mailto links are highest confidence
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:"):
                email = href[7:].split("?")[0].strip().lower()
                if _valid(email):
                    return email

        # full text scan
        for email in EMAIL_RE.findall(r.text):
            if _valid(email.lower()):
                return email.lower()

    except Exception as exc:
        log.debug("Scrape failed for %s: %s", url, exc)

    return ""


def _valid(email: str) -> bool:
    if "@" not in email:
        return False
    domain = email.split("@")[-1]
    return domain not in BLOCKED_DOMAINS and "." in domain
