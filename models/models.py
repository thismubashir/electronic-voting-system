"""
models/constituency_model.py
models/candidate_model.py
models/vote_model.py
models/election_model.py
All data-access layers for core entities.
"""
from __future__ import annotations
from database.connection import execute_query
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# CONSTITUENCY MODEL
# ─────────────────────────────────────────────────────────────
class ConstituencyModel:

    @staticmethod
    def get_all(election_type: str = None, search: str = None) -> list:
        sql = "SELECT * FROM constituencies"
        conds, params = [], []
        if election_type:
            conds.append("election_type = %s"); params.append(election_type)
        if search:
            conds.append("name LIKE %s"); params.append(f"%{search}%")
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY election_type, name"
        return execute_query(sql, tuple(params), fetch=True)

    @staticmethod
    def get_by_id(cid: int) -> dict | None:
        rows = execute_query("SELECT * FROM constituencies WHERE id=%s", (cid,), fetch=True)
        return rows[0] if rows else None

    @staticmethod
    def get_national() -> list:
        return ConstituencyModel.get_all(election_type="national")

    @staticmethod
    def get_provincial() -> list:
        return ConstituencyModel.get_all(election_type="provincial")

    @staticmethod
    def add(name: str, election_type: str, province: str, description: str = "") -> int:
        return execute_query(
            "INSERT INTO constituencies (name, election_type, province, description) VALUES (%s,%s,%s,%s)",
            (name, election_type, province, description)
        )

    @staticmethod
    def update(cid: int, name: str, province: str, description: str) -> bool:
        r = execute_query(
            "UPDATE constituencies SET name=%s, province=%s, description=%s WHERE id=%s",
            (name, province, description, cid)
        )
        return r > 0

    @staticmethod
    def delete(cid: int) -> bool:
        r = execute_query("DELETE FROM constituencies WHERE id=%s", (cid,))
        return r > 0

    @staticmethod
    def exists(name: str) -> bool:
        rows = execute_query(
            "SELECT id FROM constituencies WHERE name=%s", (name,), fetch=True
        )
        return len(rows) > 0


# ─────────────────────────────────────────────────────────────
# CANDIDATE MODEL
# ─────────────────────────────────────────────────────────────
class CandidateModel:

    @staticmethod
    def get_all(election_type: str = None, constituency_id: int = None,
                search: str = None) -> list:
        sql = """
            SELECT c.*, con.name AS constituency_name, con.province
            FROM candidates c
            JOIN constituencies con ON c.constituency_id = con.id
            WHERE c.is_active = 1
        """
        params = []
        if election_type:
            sql += " AND c.election_type = %s"; params.append(election_type)
        if constituency_id:
            sql += " AND c.constituency_id = %s"; params.append(constituency_id)
        if search:
            sql += " AND (c.full_name LIKE %s OR c.party_name LIKE %s OR con.name LIKE %s)"
            like = f"%{search}%"
            params.extend([like, like, like])
        sql += " ORDER BY con.name, c.full_name"
        return execute_query(sql, tuple(params), fetch=True)

    @staticmethod
    def get_by_id(cid: int) -> dict | None:
        rows = execute_query(
            """SELECT c.*, con.name AS constituency_name
               FROM candidates c JOIN constituencies con ON c.constituency_id=con.id
               WHERE c.id=%s""",
            (cid,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def get_for_voter(constituency_id: int, election_type: str) -> list:
        """Return candidates for a specific constituency and election type."""
        return execute_query(
            """SELECT c.*, con.name AS constituency_name
               FROM candidates c
               JOIN constituencies con ON c.constituency_id = con.id
               WHERE c.constituency_id=%s AND c.election_type=%s AND c.is_active=1
               ORDER BY c.full_name""",
            (constituency_id, election_type), fetch=True
        )

    @staticmethod
    def add(full_name: str, party_name: str, constituency_id: int,
            election_type: str, symbol_path: str = None, bio: str = "") -> int:
        return execute_query(
            """INSERT INTO candidates
               (full_name, party_name, constituency_id, election_type, party_symbol_path, bio)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (full_name, party_name, constituency_id, election_type, symbol_path, bio)
        )

    @staticmethod
    def update(cid: int, full_name: str, party_name: str,
               constituency_id: int, symbol_path: str = None, bio: str = "") -> bool:
        r = execute_query(
            """UPDATE candidates
               SET full_name=%s, party_name=%s, constituency_id=%s,
                   party_symbol_path=%s, bio=%s
               WHERE id=%s""",
            (full_name, party_name, constituency_id, symbol_path, bio, cid)
        )
        return r > 0

    @staticmethod
    def delete(cid: int) -> bool:
        r = execute_query(
            "UPDATE candidates SET is_active=0 WHERE id=%s", (cid,)
        )
        return r > 0


# ─────────────────────────────────────────────────────────────
# VOTE MODEL
# ─────────────────────────────────────────────────────────────
class VoteModel:

    @staticmethod
    def cast_vote(voter_id: int, candidate_id: int,
                  constituency_id: int, election_type: str) -> bool:
        """Insert a vote. Returns True on success, False on duplicate."""
        try:
            execute_query(
                """INSERT INTO votes (voter_id, candidate_id, constituency_id, election_type)
                   VALUES (%s,%s,%s,%s)""",
                (voter_id, candidate_id, constituency_id, election_type)
            )
            return True
        except RuntimeError as e:
            if "Duplicate entry" in str(e) or "1062" in str(e):
                return False
            raise

    @staticmethod
    def get_results(election_type: str = None, constituency_id: int = None) -> list:
        """Return candidate-wise vote counts."""
        sql = """
            SELECT c.id, c.full_name, c.party_name, c.party_symbol_path,
                   c.election_type, con.name AS constituency_name,
                   COUNT(v.id) AS vote_count
            FROM candidates c
            JOIN constituencies con ON c.constituency_id = con.id
            LEFT JOIN votes v ON v.candidate_id = c.id
            WHERE c.is_active = 1
        """
        params = []
        if election_type:
            sql += " AND c.election_type = %s"; params.append(election_type)
        if constituency_id:
            sql += " AND c.constituency_id = %s"; params.append(constituency_id)
        sql += " GROUP BY c.id ORDER BY con.name, vote_count DESC"
        return execute_query(sql, tuple(params), fetch=True)

    @staticmethod
    def get_turnout(election_type: str) -> dict:
        """Return total eligible vs total voted for given election type."""
        eligible = execute_query(
            "SELECT COUNT(*) AS cnt FROM voters WHERE status='approved'",
            fetch=True
        )[0]["cnt"]
        voted = execute_query(
            "SELECT COUNT(*) AS cnt FROM votes WHERE election_type=%s",
            (election_type,), fetch=True
        )[0]["cnt"]
        return {"eligible": eligible, "voted": voted,
                "percentage": round(voted / eligible * 100, 1) if eligible else 0}

    @staticmethod
    def get_constituency_results(election_type: str) -> list:
        """Return winner per constituency for given election type."""
        return execute_query(
            """
            SELECT con.name AS constituency, cand.full_name AS winner,
                   cand.party_name, ranked.vote_count AS votes
            FROM (
                SELECT c.constituency_id, c.id AS candidate_id,
                       COUNT(v.id) AS vote_count,
                       ROW_NUMBER() OVER (
                           PARTITION BY c.constituency_id
                           ORDER BY COUNT(v.id) DESC
                       ) AS rn
                FROM candidates c
                LEFT JOIN votes v ON v.candidate_id = c.id
                WHERE c.election_type = %s AND c.is_active = 1
                GROUP BY c.id
            ) ranked
            JOIN candidates cand ON ranked.candidate_id = cand.id
            JOIN constituencies con ON cand.constituency_id = con.id
            WHERE ranked.rn = 1
            ORDER BY con.name
            """,
            (election_type,), fetch=True
        )


# ─────────────────────────────────────────────────────────────
# ELECTION SCHEDULE MODEL
# ─────────────────────────────────────────────────────────────
class ElectionModel:

    @staticmethod
    def get_all() -> list:
        return execute_query(
            """SELECT es.*, a.full_name AS created_by_name,
                      con.name AS constituency_name
               FROM election_schedule es
               LEFT JOIN admins a ON es.created_by = a.id
               LEFT JOIN constituencies con ON es.constituency_id = con.id
               ORDER BY es.start_datetime DESC""",
            fetch=True
        )

    @staticmethod
    def get_active() -> list:
        return execute_query(
            """SELECT * FROM election_schedule
               WHERE is_active=1 AND NOW() BETWEEN start_datetime AND end_datetime""",
            fetch=True
        )

    @staticmethod
    def is_voting_open(election_type: str) -> bool:
        rows = execute_query(
            """SELECT id FROM election_schedule
               WHERE is_active=1
                 AND election_type IN (%s, 'both')
                 AND NOW() BETWEEN start_datetime AND end_datetime""",
            (election_type,), fetch=True
        )
        return len(rows) > 0

    @staticmethod
    def add(election_type: str, start: str, end: str,
            admin_id: int, constituency_id: int = None) -> int:
        return execute_query(
            """INSERT INTO election_schedule
               (election_type, start_datetime, end_datetime, created_by, constituency_id)
               VALUES (%s,%s,%s,%s,%s)""",
            (election_type, start, end, admin_id, constituency_id)
        )

    @staticmethod
    def update(sid: int, start: str, end: str, is_active: int) -> bool:
        r = execute_query(
            """UPDATE election_schedule
               SET start_datetime=%s, end_datetime=%s, is_active=%s WHERE id=%s""",
            (start, end, is_active, sid)
        )
        return r > 0

    @staticmethod
    def disable(sid: int) -> bool:
        r = execute_query(
            "UPDATE election_schedule SET is_active=0 WHERE id=%s", (sid,)
        )
        return r > 0


# ─────────────────────────────────────────────────────────────
# AUDIT LOG MODEL
# ─────────────────────────────────────────────────────────────
class AuditModel:

    @staticmethod
    def log(user_type: str, user_id: int, action: str,
            details: str = "", ip: str = "127.0.0.1"):
        execute_query(
            """INSERT INTO audit_logs (user_type, user_id, action, details, ip_address)
               VALUES (%s,%s,%s,%s,%s)""",
            (user_type, user_id, action, details, ip)
        )

    @staticmethod
    def get_recent(limit: int = 100) -> list:
        return execute_query(
            "SELECT * FROM audit_logs ORDER BY logged_at DESC LIMIT %s",
            (limit,), fetch=True
        )
