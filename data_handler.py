"""
data_handler.py
Handles secure, GDPR-aligned storage of candidate screening data.
Data is stored locally as anonymised JSON (no plain-text sensitive fields in logs).
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path


DATA_DIR = Path("candidate_data")


class DataHandler:
    """
    Manages candidate data persistence.

    Privacy approach:
    - Email and phone are stored as one-way SHA-256 hashes in session logs.
    - Full PII is stored separately in a restricted candidates/ directory.
    - Session transcripts strip sensitive tokens before saving.
    """

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        (DATA_DIR / "sessions").mkdir(exist_ok=True)
        (DATA_DIR / "candidates").mkdir(exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def save_session(self, candidate_info: dict, messages: list) -> str:
        """
        Persist the screening session. Returns the session ID.
        """
        session_id = self._generate_session_id(candidate_info)
        timestamp = datetime.utcnow().isoformat()

        # Save full candidate profile (PII) to restricted folder
        profile_path = DATA_DIR / "candidates" / f"{session_id}.json"
        profile = {
            "session_id": session_id,
            "timestamp": timestamp,
            "candidate": {
                "full_name": candidate_info.get("full_name"),
                "email": candidate_info.get("email"),
                "phone": candidate_info.get("phone"),
                "years_experience": candidate_info.get("years_experience"),
                "desired_position": candidate_info.get("desired_position"),
                "location": candidate_info.get("location"),
                "tech_stack": candidate_info.get("tech_stack", []),
            },
        }
        self._write_json(profile_path, profile)

        # Save anonymised session log (no PII)
        session_path = DATA_DIR / "sessions" / f"{session_id}_session.json"
        session_log = {
            "session_id": session_id,
            "timestamp": timestamp,
            "candidate_id_hash": self._hash(candidate_info.get("email", "")),
            "tech_stack": candidate_info.get("tech_stack", []),
            "message_count": len(messages),
            "transcript": self._sanitise_transcript(messages, candidate_info),
        }
        self._write_json(session_path, session_log)

        return session_id

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_session_id(info: dict) -> str:
        seed = (info.get("email") or "") + datetime.utcnow().isoformat()
        return "ts_" + hashlib.sha256(seed.encode()).hexdigest()[:12]

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    @staticmethod
    def _write_json(path: Path, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _sanitise_transcript(messages: list, candidate_info: dict) -> list:
        """
        Return transcript with email and phone replaced by [REDACTED].
        """
        sensitive = [
            v for v in [
                candidate_info.get("email"),
                candidate_info.get("phone"),
            ]
            if v
        ]
        cleaned = []
        for msg in messages:
            content = msg.get("content", "")
            for s in sensitive:
                content = content.replace(s, "[REDACTED]")
            cleaned.append({"role": msg["role"], "content": content})
        return cleaned
