"""
utils/helpers.py
Utility functions: password hashing, input validation, session management
"""
from __future__ import annotations
import re
import bcrypt
import hashlib
from datetime import datetime


# ── Password Hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── Input Validation ─────────────────────────────────────────────────────────

def validate_cnic(cnic: str) -> bool:
    """Validate Pakistani CNIC format: XXXXX-XXXXXXX-X"""
    pattern = r"^\d{5}-\d{7}-\d{1}$"
    return bool(re.match(pattern, cnic))


def validate_username(username: str) -> bool:
    """Username: 4-30 chars, alphanumeric + underscore."""
    return bool(re.match(r"^[a-zA-Z0-9_]{4,30}$", username))


def validate_password(password: str) -> tuple[bool, str]:
    """Password must be ≥8 chars with uppercase, lowercase, digit."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, "OK"


def validate_name(name: str) -> bool:
    """Full name: 2-100 printable chars."""
    return 2 <= len(name.strip()) <= 100


# ── Session Manager ───────────────────────────────────────────────────────────

class Session:
    """Lightweight in-memory session for the current user."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.user_id    = None
        self.user_type  = None   # 'admin' | 'voter'
        self.username   = None
        self.full_name  = None
        self.data       = {}     # extra user fields

    def login(self, user_type: str, user_id: int, username: str,
              full_name: str, extra: dict | None = None):
        self.user_type = user_type
        self.user_id   = user_id
        self.username  = username
        self.full_name = full_name
        self.data      = extra or {}

    def logout(self):
        self.reset()

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    @property
    def is_admin(self) -> bool:
        return self.user_type == "admin"

    @property
    def is_voter(self) -> bool:
        return self.user_type == "voter"


# Singleton session accessible across modules
current_session = Session()


# ── Misc Helpers ──────────────────────────────────────────────────────────────

def format_datetime(dt) -> str:
    """Return a friendly datetime string."""
    if dt is None:
        return "—"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%d %b %Y  %I:%M %p")


def format_cnic(raw: str) -> str:
    """Auto-format 13-digit string to XXXXX-XXXXXXX-X."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 13:
        return f"{digits[:5]}-{digits[5:12]}-{digits[12]}"
    return raw


def is_election_active(schedule_rows: list) -> bool:
    """Check if any schedule row is currently active."""
    now = datetime.now()
    for row in schedule_rows:
        if (row.get("is_active") and
                row["start_datetime"] <= now <= row["end_datetime"]):
            return True
    return False


def election_time_range(schedule_rows: list) -> str:
    """Return a human-readable time range for the active election."""
    now = datetime.now()
    for row in schedule_rows:
        if row.get("is_active"):
            start = format_datetime(row["start_datetime"])
            end   = format_datetime(row["end_datetime"])
            return f"{start}  →  {end}"
    return "No active election scheduled."


def generate_otp() -> str:
    """Simulate a 6-digit OTP (for demo purposes)."""
    import random
    return str(random.randint(100000, 999999))
