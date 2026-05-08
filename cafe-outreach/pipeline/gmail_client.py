import base64
import logging
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.labels",
]

PIPELINE_LABELS = {
    "1_identified": ("TRT Cafe Outreach/1 - Identified", "#e4e4e4", "#000000"),
    "2_contacted":  ("TRT Cafe Outreach/2 - Contacted",  "#4a86e8", "#ffffff"),
    "3_replied":    ("TRT Cafe Outreach/3 - Replied",    "#ffad47", "#000000"),
    "4_meeting":    ("TRT Cafe Outreach/4 - Meeting",    "#16a766", "#ffffff"),
    "5_partner":    ("TRT Cafe Outreach/5 - Partner",    "#0d7a5f", "#ffffff"),
}


class GmailClient:
    def __init__(self, token_path: str = "token.json", creds_path: str = "credentials.json"):
        self.service = self._authenticate(token_path, creds_path)
        self._label_ids: dict = {}

    def _authenticate(self, token_path: str, creds_path: str):
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        return build("gmail", "v1", credentials=creds)

    def ensure_labels(self):
        existing = {
            lbl["name"]: lbl["id"]
            for lbl in self.service.users().labels().list(userId="me").execute().get("labels", [])
        }
        for key, (name, bg, fg) in PIPELINE_LABELS.items():
            if name in existing:
                self._label_ids[key] = existing[name]
            else:
                result = self.service.users().labels().create(
                    userId="me",
                    body={"name": name, "color": {"backgroundColor": bg, "textColor": fg}},
                ).execute()
                self._label_ids[key] = result["id"]
                log.info("Created Gmail label: %s", name)

    def create_draft(self, to: str, subject: str, body: str, label_key: str = "2_contacted") -> str:
        msg = MIMEText(body, "plain", "utf-8")
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        draft = self.service.users().drafts().create(
            userId="me", body={"message": {"raw": raw}}
        ).execute()

        msg_id = draft["message"]["id"]

        if label_key in self._label_ids:
            self.service.users().messages().modify(
                userId="me",
                id=msg_id,
                body={"addLabelIds": [self._label_ids[label_key]]},
            ).execute()

        log.info("Draft created (id=%s) to %s", draft["id"], to)
        return draft["id"]
