"""
app.py
Electronic Voting System — Pakistan
Entry point: initialises DB, applies theme, launches login window.

Run:
    python app.py

Credentials (default):
    Admin   → username: admin      password: Admin@123
    Voter   → username: ahmed_hassan  password: Voter@123  (approved)
              username: sara_khan     password: Voter@123  (pending – cannot login)
"""

import tkinter as tk
import sys
import os

# ── Ensure project root is on the path ────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # ── 1. Root window (hidden host) ─────────────────────────────────────────
    root = tk.Tk()
    root.withdraw()                  # hidden – only Toplevels shown to user
    root.title("EVS Pakistan")

    # ── 2. Apply TTK theme ───────────────────────────────────────────────────
    from views.theme import apply_theme
    apply_theme(root)

    # ── 3. Initialise database ───────────────────────────────────────────────
    try:
        from database.connection import init_database
        init_database()
    except Exception as e:
        import tkinter.messagebox as mb
        mb.showerror(
            "Database Error",
            f"Could not connect to MySQL.\n\n"
            f"Error: {e}\n\n"
            f"Please check:\n"
            f"  • MySQL is installed and running\n"
            f"  • Edit the .env file with your MySQL credentials\n"
            f"  • Default: root user with no password\n"
            f"  • The 'evs_pakistan' database will be created automatically"
        )
        root.destroy()
        return

    # ── 4. Callbacks for portal transitions ──────────────────────────────────
    def launch_login():
        """Open the login/register window."""
        from views.auth_view import LoginWindow
        LoginWindow(root,
                    on_admin_success=launch_admin,
                    on_voter_success=launch_voter)

    def launch_admin():
        """Open the Admin portal, go back to login on logout."""
        from views.admin_view import AdminWindow
        AdminWindow(root, on_logout=launch_login)

    def launch_voter():
        """Open the Voter portal, go back to login on logout."""
        from views.voter_view import VoterWindow
        VoterWindow(root, on_logout=launch_login)

    # ── 5. Start ─────────────────────────────────────────────────────────────
    launch_login()
    root.mainloop()


if __name__ == "__main__":
    main()
