"""
controllers/controllers.py
Business-logic controllers bridging models ↔ views.
"""
from __future__ import annotations
from models import (
    AdminModel, VoterModel, ConstituencyModel,
    CandidateModel, VoteModel, ElectionModel, AuditModel,
)
from utils.helpers import (
    current_session, validate_cnic, validate_username,
    validate_password, validate_name, is_election_active,
)


# ─────────────────────────────────────────────────────────────
# AUTH CONTROLLER
# ─────────────────────────────────────────────────────────────
class AuthController:

    @staticmethod
    def admin_login(username: str, password: str) -> tuple[bool, str]:
        admin = AdminModel.verify_login(username, password)
        if not admin:
            return False, "Invalid username or password."
        current_session.login("admin", admin["id"], admin["username"],
                              admin["full_name"])
        AuditModel.log("admin", admin["id"], "LOGIN", f"Admin {username} logged in.")
        return True, "Login successful."

    @staticmethod
    def voter_login(username: str, password: str) -> tuple[bool, str]:
        voter = VoterModel.verify_login(username, password)
        if not voter:
            return False, "Invalid username or password."
        if voter["status"] == "pending":
            return False, "Your account is pending admin approval."
        if voter["status"] == "rejected":
            return False, "Your registration has been rejected. Contact support."
        current_session.login(
            "voter", voter["id"], voter["username"], voter["full_name"],
            extra={
                "cnic": voter["cnic"],
                "city": voter["city"],
                "na_constituency_id": voter["na_constituency_id"],
                "pp_constituency_id": voter["pp_constituency_id"],
            }
        )
        AuditModel.log("voter", voter["id"], "LOGIN", f"Voter {username} logged in.")
        return True, "Login successful."

    @staticmethod
    def logout():
        if current_session.is_authenticated:
            AuditModel.log(current_session.user_type, current_session.user_id,
                           "LOGOUT", f"{current_session.username} logged out.")
        current_session.logout()


# ─────────────────────────────────────────────────────────────
# VOTER CONTROLLER
# ─────────────────────────────────────────────────────────────
class VoterController:

    @staticmethod
    def register(cnic, full_name, city, na_name, pp_name,
                 username, password) -> tuple[bool, str]:
        # Validate inputs
        if not validate_cnic(cnic):
            return False, "Invalid CNIC format. Use XXXXX-XXXXXXX-X."
        if not validate_name(full_name):
            return False, "Full name must be 2–100 characters."
        if not validate_username(username):
            return False, "Username: 4–30 chars, alphanumeric + underscore only."
        ok, msg = validate_password(password)
        if not ok:
            return False, msg

        # Check duplicates
        if VoterModel.get_by_cnic(cnic):
            return False, "A voter with this CNIC is already registered."
        if VoterModel.get_by_username(username):
            return False, "Username is already taken."

        # Resolve constituency IDs
        na_rows = ConstituencyModel.get_all(election_type="national")
        pp_rows = ConstituencyModel.get_all(election_type="provincial")

        na_map = {r["name"]: r["id"] for r in na_rows}
        pp_map = {r["name"]: r["id"] for r in pp_rows}

        if na_name not in na_map:
            return False, f"National constituency '{na_name}' not found."
        if pp_name not in pp_map:
            return False, f"Provincial constituency '{pp_name}' not found."

        try:
            VoterModel.register(cnic, full_name, city,
                                na_map[na_name], pp_map[pp_name],
                                username, password)
            return True, "Registration submitted! Please wait for admin approval."
        except Exception as e:
            return False, f"Registration failed: {e}"

    @staticmethod
    def cast_vote(candidate_id: int, election_type: str) -> tuple[bool, str]:
        if not current_session.is_voter:
            return False, "Not logged in as voter."

        # Check election open
        if not ElectionModel.is_voting_open(election_type):
            return False, "Voting is not currently active for this election."

        # Check already voted
        if VoterModel.has_voted(current_session.user_id, election_type):
            return False, "You have already voted in this election."

        # Get candidate to verify constituency
        candidate = CandidateModel.get_by_id(candidate_id)
        if not candidate:
            return False, "Invalid candidate."

        # Verify voter's constituency matches candidate's
        if election_type == "national":
            voter_const = current_session.data.get("na_constituency_id")
        else:
            voter_const = current_session.data.get("pp_constituency_id")

        if candidate["constituency_id"] != voter_const:
            return False, "You can only vote for candidates in your constituency."

        success = VoteModel.cast_vote(
            current_session.user_id, candidate_id,
            candidate["constituency_id"], election_type
        )
        if success:
            AuditModel.log("voter", current_session.user_id, "VOTE_CAST",
                           f"Voted for candidate {candidate_id} in {election_type}.")
            return True, "Your vote has been submitted successfully! ✓"
        return False, "You have already voted or an error occurred."

    @staticmethod
    def get_candidates_for_voter(election_type: str) -> list:
        if election_type == "national":
            cid = current_session.data.get("na_constituency_id")
        else:
            cid = current_session.data.get("pp_constituency_id")
        if not cid:
            return []
        return CandidateModel.get_for_voter(cid, election_type)


# ─────────────────────────────────────────────────────────────
# ADMIN CONTROLLER
# ─────────────────────────────────────────────────────────────
class AdminController:

    @staticmethod
    def get_stats() -> dict:
        return AdminModel.get_dashboard_stats()

    # ── Voters ──
    @staticmethod
    def get_voters(status=None, search=None) -> list:
        return VoterModel.get_all(status=status, search=search)

    @staticmethod
    def approve_voter(voter_id: int) -> tuple[bool, str]:
        ok = VoterModel.approve(voter_id, current_session.user_id)
        if ok:
            AuditModel.log("admin", current_session.user_id, "VOTER_APPROVED",
                           f"Voter {voter_id} approved.")
            return True, "Voter approved successfully."
        return False, "Failed to approve voter."

    @staticmethod
    def reject_voter(voter_id: int) -> tuple[bool, str]:
        ok = VoterModel.reject(voter_id, current_session.user_id)
        if ok:
            AuditModel.log("admin", current_session.user_id, "VOTER_REJECTED",
                           f"Voter {voter_id} rejected.")
            return True, "Voter rejected."
        return False, "Failed to reject voter."

    # ── Constituencies ──
    @staticmethod
    def add_constituency(name, election_type, province, desc="") -> tuple[bool, str]:
        if ConstituencyModel.exists(name):
            return False, f"Constituency '{name}' already exists."
        try:
            ConstituencyModel.add(name, election_type, province, desc)
            AuditModel.log("admin", current_session.user_id, "CONSTITUENCY_ADD",
                           f"Added {name}.")
            return True, f"Constituency '{name}' added."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def update_constituency(cid, name, province, desc) -> tuple[bool, str]:
        ok = ConstituencyModel.update(cid, name, province, desc)
        if ok:
            AuditModel.log("admin", current_session.user_id, "CONSTITUENCY_UPDATE",
                           f"Updated constituency {cid}.")
            return True, "Constituency updated."
        return False, "Update failed."

    @staticmethod
    def delete_constituency(cid: int) -> tuple[bool, str]:
        try:
            ok = ConstituencyModel.delete(cid)
            if ok:
                AuditModel.log("admin", current_session.user_id,
                               "CONSTITUENCY_DELETE", f"Deleted {cid}.")
                return True, "Constituency deleted."
            return False, "Delete failed."
        except Exception as e:
            return False, f"Cannot delete: {e}"

    # ── Candidates ──
    @staticmethod
    def add_candidate(full_name, party_name, constituency_id, election_type,
                      symbol_path=None, bio="") -> tuple[bool, str]:
        try:
            CandidateModel.add(full_name, party_name, constituency_id,
                               election_type, symbol_path, bio)
            AuditModel.log("admin", current_session.user_id, "CANDIDATE_ADD",
                           f"Added {full_name}.")
            return True, f"Candidate '{full_name}' added."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def update_candidate(cid, full_name, party_name, constituency_id,
                         symbol_path=None, bio="") -> tuple[bool, str]:
        ok = CandidateModel.update(cid, full_name, party_name,
                                   constituency_id, symbol_path, bio)
        if ok:
            AuditModel.log("admin", current_session.user_id, "CANDIDATE_UPDATE",
                           f"Updated candidate {cid}.")
            return True, "Candidate updated."
        return False, "Update failed."

    @staticmethod
    def delete_candidate(cid: int) -> tuple[bool, str]:
        ok = CandidateModel.delete(cid)
        if ok:
            AuditModel.log("admin", current_session.user_id, "CANDIDATE_DELETE",
                           f"Deleted candidate {cid}.")
            return True, "Candidate removed."
        return False, "Delete failed."

    # ── Elections ──
    @staticmethod
    def schedule_election(election_type, start, end,
                          constituency_id=None) -> tuple[bool, str]:
        try:
            ElectionModel.add(election_type, start, end,
                              current_session.user_id, constituency_id)
            AuditModel.log("admin", current_session.user_id, "ELECTION_SCHEDULED",
                           f"{election_type} election from {start} to {end}.")
            return True, "Election scheduled successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def update_election(sid, start, end, is_active) -> tuple[bool, str]:
        ok = ElectionModel.update(sid, start, end, is_active)
        if ok:
            return True, "Election updated."
        return False, "Update failed."

    @staticmethod
    def disable_election(sid: int) -> tuple[bool, str]:
        ok = ElectionModel.disable(sid)
        if ok:
            AuditModel.log("admin", current_session.user_id, "ELECTION_DISABLED",
                           f"Election {sid} disabled.")
            return True, "Election disabled."
        return False, "Failed to disable."

    # ── Results ──
    @staticmethod
    def get_results(election_type=None) -> list:
        return VoteModel.get_results(election_type)

    @staticmethod
    def get_turnout(election_type: str) -> dict:
        return VoteModel.get_turnout(election_type)
