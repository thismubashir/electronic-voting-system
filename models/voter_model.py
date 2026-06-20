"""
models/voter_model.py
Voter data-access layer
"""
from __future__ import annotations
from database.connection import execute_query
from utils.helpers import verify_password, hash_password


class VoterModel:

    @staticmethod
    def register(cnic, full_name, city, na_id, pp_id, username, plain_password) -> int:
        """Insert a new voter (status=pending). Returns new voter id."""
        ph = hash_password(plain_password)
        return execute_query(
            """INSERT INTO voters
               (cnic, full_name, city, na_constituency_id, pp_constituency_id,
                username, password_hash, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'pending')""",
            (cnic, full_name, city, na_id, pp_id, username, ph)
        )

    @staticmethod
    def get_by_username(username: str) -> dict | None:
        rows = execute_query(
            "SELECT * FROM voters WHERE username = %s", (username,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def get_by_cnic(cnic: str) -> dict | None:
        rows = execute_query(
            "SELECT * FROM voters WHERE cnic = %s", (cnic,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def verify_login(username: str, password: str) -> dict | None:
        voter = VoterModel.get_by_username(username)
        if voter and verify_password(password, voter["password_hash"]):
            return voter
        return None

    @staticmethod
    def get_all(status: str = None, search: str = None) -> list:
        """Fetch voters with optional status filter and search."""
        base = """
            SELECT v.*, nc.name AS na_name, pc.name AS pp_name
            FROM voters v
            LEFT JOIN constituencies nc ON v.na_constituency_id = nc.id
            LEFT JOIN constituencies pc ON v.pp_constituency_id = pc.id
        """
        conds, params = [], []

        if status:
            conds.append("v.status = %s")
            params.append(status)
        if search:
            conds.append("(v.full_name LIKE %s OR v.cnic LIKE %s OR nc.name LIKE %s OR pc.name LIKE %s)")
            like = f"%{search}%"
            params.extend([like, like, like, like])

        if conds:
            base += " WHERE " + " AND ".join(conds)
        base += " ORDER BY v.registered_at DESC"
        return execute_query(base, tuple(params), fetch=True)

    @staticmethod
    def approve(voter_id: int, admin_id: int) -> bool:
        r = execute_query(
            """UPDATE voters SET status='approved', approved_at=NOW(),
               approved_by=%s WHERE id=%s""",
            (admin_id, voter_id)
        )
        return r > 0

    @staticmethod
    def reject(voter_id: int, admin_id: int) -> bool:
        r = execute_query(
            "UPDATE voters SET status='rejected', approved_by=%s WHERE id=%s",
            (admin_id, voter_id)
        )
        return r > 0

    @staticmethod
    def get_vote_history(voter_id: int) -> list:
        return execute_query(
            """SELECT v.election_type, v.voted_at,
                      c.full_name AS candidate_name, c.party_name,
                      con.name AS constituency_name
               FROM votes v
               JOIN candidates c ON v.candidate_id = c.id
               JOIN constituencies con ON v.constituency_id = con.id
               WHERE v.voter_id = %s
               ORDER BY v.voted_at""",
            (voter_id,), fetch=True
        )

    @staticmethod
    def has_voted(voter_id: int, election_type: str) -> bool:
        rows = execute_query(
            "SELECT id FROM votes WHERE voter_id=%s AND election_type=%s",
            (voter_id, election_type), fetch=True
        )
        return len(rows) > 0

    @staticmethod
    def count_by_status() -> dict:
        rows = execute_query(
            "SELECT status, COUNT(*) AS cnt FROM voters GROUP BY status",
            fetch=True
        )
        return {r["status"]: r["cnt"] for r in rows}
