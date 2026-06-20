"""
models/admin_model.py
Admin data-access layer
"""
from __future__ import annotations
from database.connection import execute_query
from utils.helpers import verify_password, hash_password


class AdminModel:

    @staticmethod
    def get_by_username(username: str) -> dict | None:
        rows = execute_query(
            "SELECT * FROM admins WHERE username = %s", (username,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def verify_login(username: str, password: str) -> dict | None:
        admin = AdminModel.get_by_username(username)
        if admin and verify_password(password, admin["password_hash"]):
            # update last login
            execute_query(
                "UPDATE admins SET last_login = NOW() WHERE id = %s",
                (admin["id"],)
            )
            return admin
        return None

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Return aggregated counts for the admin dashboard."""
        stats = {}

        rows = execute_query(
            "SELECT COUNT(*) AS total FROM voters", fetch=True
        )
        stats["total_voters"] = rows[0]["total"]

        rows = execute_query(
            "SELECT COUNT(*) AS total FROM voters WHERE status='approved'",
            fetch=True
        )
        stats["approved_voters"] = rows[0]["total"]

        rows = execute_query(
            "SELECT COUNT(*) AS total FROM voters WHERE status='pending'",
            fetch=True
        )
        stats["pending_voters"] = rows[0]["total"]

        rows = execute_query(
            "SELECT COUNT(*) AS total FROM voters WHERE status='rejected'",
            fetch=True
        )
        stats["rejected_voters"] = rows[0]["total"]

        rows = execute_query(
            "SELECT COUNT(*) AS total FROM candidates WHERE is_active=1",
            fetch=True
        )
        stats["total_candidates"] = rows[0]["total"]

        rows = execute_query(
            "SELECT COUNT(*) AS total FROM votes", fetch=True
        )
        stats["total_votes"] = rows[0]["total"]

        rows = execute_query(
            """SELECT COUNT(*) AS total FROM election_schedule
               WHERE is_active=1 AND NOW() BETWEEN start_datetime AND end_datetime""",
            fetch=True
        )
        stats["active_elections"] = rows[0]["total"]

        rows = execute_query(
            "SELECT COUNT(*) AS total FROM constituencies", fetch=True
        )
        stats["total_constituencies"] = rows[0]["total"]

        return stats

    @staticmethod
    def change_password(admin_id: int, new_password: str) -> bool:
        h = hash_password(new_password)
        affected = execute_query(
            "UPDATE admins SET password_hash = %s WHERE id = %s",
            (h, admin_id)
        )
        return affected > 0
