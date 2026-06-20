"""
views/voter_view.py
Voter Portal — sidebar nav with Dashboard, Vote NA, Vote PP, History.
"""
import tkinter as tk
from tkinter import ttk
from views.theme import (
    CLR, FONTS, make_frame, make_label, make_button,
    make_treeview, populate_tree, show_message, ask_confirm, make_card,
)
from controllers import AuthController, VoterController
from models import ElectionModel, VoterModel
from utils.helpers import current_session, format_datetime, election_time_range
import threading


NAV_ITEMS = [
    ("🏠", "Dashboard"),
    ("🗳", "Vote — National Assembly"),
    ("🏛", "Vote — Provincial Assembly"),
    ("📋", "Vote History"),
    ("👤", "My Profile"),
]


class VoterWindow(tk.Toplevel):

    def __init__(self, master, on_logout):
        super().__init__(master)
        self.on_logout = on_logout
        self.title(f"EVS Pakistan — Voter Portal: {current_session.full_name}")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=CLR["bg_dark"])
        self.protocol("WM_DELETE_WINDOW", self._logout)

        self._pages: dict[str, tk.Frame] = {}
        self._active_nav = tk.StringVar(value="Dashboard")
        self._build_layout()
        self._show_page("Dashboard")

        # Auto-refresh every 30s
        self._refresh_loop()

    # ─────────────────────────────────────────────────────────
    # LAYOUT
    # ─────────────────────────────────────────────────────────
    def _build_layout(self):
        # Sidebar
        self.sidebar = make_frame(self, bg=CLR["bg_sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Content area
        self.content = make_frame(self, bg=CLR["bg_dark"])
        self.content.pack(side="left", fill="both", expand=True)

        # Build all pages
        self._pages["Dashboard"]                  = self._make_dashboard()
        self._pages["Vote — National Assembly"]   = self._make_vote_page("national")
        self._pages["Vote — Provincial Assembly"] = self._make_vote_page("provincial")
        self._pages["Vote History"]               = self._make_history_page()
        self._pages["My Profile"]                 = self._make_profile_page()

    def _build_sidebar(self):
        # Logo area
        logo = make_frame(self.sidebar, bg=CLR["bg_sidebar"])
        logo.pack(fill="x", pady=(0, 10))

        tk.Label(logo, text="☽ ★", font=(FONTS["heading_xl"][0], 28),
                 fg=CLR["gold"], bg=CLR["bg_sidebar"]).pack(pady=(20, 2))
        tk.Label(logo, text="EVS Pakistan", font=FONTS["heading_sm"],
                 fg="#FFFFFF", bg=CLR["bg_sidebar"]).pack()
        tk.Label(logo, text="Voter Portal", font=FONTS["small"],
                 fg="#A8D5B8", bg=CLR["bg_sidebar"]).pack(pady=(0, 12))

        ttk.Separator(self.sidebar).pack(fill="x", padx=12)

        # Nav buttons
        for icon, label in NAV_ITEMS:
            btn = tk.Button(
                self.sidebar, text=f"  {icon}  {label}",
                command=lambda l=label: self._show_page(l),
                bg=CLR["bg_sidebar"], fg="#A8D5B8",
                activebackground=CLR["emerald_dark"], activeforeground="#FFFFFF",
                relief="flat", bd=0, anchor="w",
                font=FONTS["body"], pady=10, cursor="hand2",
            )
            btn.pack(fill="x", padx=8, pady=2)
            # Highlight active
            def on_enter(e, b=btn): b.config(bg=CLR["bg_hover"])
            def on_leave(e, b=btn):
                b.config(bg=CLR["emerald_dark"]
                         if b.cget("text").split("  ", 2)[-1] == self._active_nav.get()
                         else CLR["bg_sidebar"])
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        # Logout
        ttk.Separator(self.sidebar).pack(fill="x", padx=12, pady=10)
        make_button(self.sidebar, "  ⏻  Logout", command=self._logout,
                    style="danger").pack(fill="x", padx=12, pady=4)

        # Voter name at bottom
        tk.Label(self.sidebar, text=current_session.full_name,
                 font=FONTS["small"], fg=CLR["text_muted"],
                 bg=CLR["bg_sidebar"], wraplength=180).pack(
            side="bottom", pady=12)

    def _show_page(self, name: str):
        self._active_nav.set(name)
        for n, page in self._pages.items():
            if n == name:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
        # Refresh data on page visit
        if name == "Vote History":
            self._load_history()
        elif name in ("Vote — National Assembly", "Vote — Provincial Assembly"):
            et = "national" if "National" in name else "provincial"
            self._load_candidates(et)

    # ─────────────────────────────────────────────────────────
    # DASHBOARD PAGE
    # ─────────────────────────────────────────────────────────
    def _make_dashboard(self) -> tk.Frame:
        page = make_frame(self.content, bg=CLR["bg_dark"])

        # Top bar
        bar = make_frame(page, bg=CLR["bg_panel"])
        bar.pack(fill="x")
        make_label(bar, f"  Welcome, {current_session.full_name}",
                   font=FONTS["heading_md"], bg=CLR["bg_panel"],
                   fg=CLR["emerald"]).pack(side="left", pady=14, padx=10)

        # Schedule info
        sched = make_frame(page, bg=CLR["bg_dark"])
        sched.pack(fill="x", padx=30, pady=20)

        self.sched_lbl = make_label(sched, "Loading election schedule…",
                                    font=FONTS["body"], fg=CLR["sky"],
                                    bg=CLR["bg_dark"])
        self.sched_lbl.pack(anchor="w")

        # Status cards
        cards = make_frame(page, bg=CLR["bg_dark"])
        cards.pack(fill="x", padx=30, pady=10)

        voted_na = VoterModel.has_voted(current_session.user_id, "national")
        voted_pp = VoterModel.has_voted(current_session.user_id, "provincial")

        na_card = make_card(cards, "National Assembly Vote",
                            "✓ Voted" if voted_na else "Not Yet Voted",
                            accent=CLR["success"] if voted_na else CLR["orange"])
        na_card.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        pp_card = make_card(cards, "Provincial Assembly Vote",
                            "✓ Voted" if voted_pp else "Not Yet Voted",
                            accent=CLR["success"] if voted_pp else CLR["orange"])
        pp_card.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        # Constituency info
        info = make_frame(page, bg=CLR["bg_card"],
                          highlightthickness=1,
                          highlightbackground=CLR["border"])
        info.pack(fill="x", padx=30, pady=10)

        def info_row(label, value, color=CLR["text_primary"]):
            row = make_frame(info, bg=CLR["bg_card"])
            row.pack(fill="x", padx=20, pady=4)
            make_label(row, label + ":", font=FONTS["body_bold"],
                       fg=CLR["text_secondary"], bg=CLR["bg_card"]).pack(
                side="left", padx=(0, 10))
            make_label(row, value, fg=color, bg=CLR["bg_card"]).pack(side="left")

        make_label(info, "  Your Registration Details",
                   font=FONTS["heading_sm"], fg=CLR["text_primary"],
                   bg=CLR["bg_card"]).pack(anchor="w", padx=20, pady=(12, 6))

        from models import ConstituencyModel
        na_c = ConstituencyModel.get_by_id(
            current_session.data.get("na_constituency_id", 0))
        pp_c = ConstituencyModel.get_by_id(
            current_session.data.get("pp_constituency_id", 0))

        info_row("CNIC",   current_session.data.get("cnic", "—"))
        info_row("City",   current_session.data.get("city", "—"))
        info_row("NA Constituency",
                 na_c["name"] if na_c else "—", CLR["sky"])
        info_row("PP Constituency",
                 pp_c["name"] if pp_c else "—", CLR["sky"])
        info_row("Account Status", "Approved ✓", CLR["success"])

        # Refresh schedule text
        self._update_schedule_label()

        return page

    def _update_schedule_label(self):
        schedules = ElectionModel.get_all()
        if not schedules:
            txt = "⚠  No election is currently scheduled."
            color = CLR["warning"]
        else:
            active = ElectionModel.get_active()
            if active:
                rng = election_time_range(active)
                txt = f"🗳  Voting is OPEN  |  {rng}"
                color = CLR["success"]
            else:
                # Show next upcoming
                txt = "⏳  Voting is currently CLOSED. Check back later."
                color = CLR["error"]
        if hasattr(self, "sched_lbl"):
            self.sched_lbl.config(text=txt, fg=color)

    # ─────────────────────────────────────────────────────────
    # VOTING PAGE (national / provincial)
    # ─────────────────────────────────────────────────────────
    def _make_vote_page(self, election_type: str) -> tk.Frame:
        page = make_frame(self.content, bg=CLR["bg_dark"])
        title = "National Assembly" if election_type == "national" else "Provincial Assembly"

        # Top bar
        bar = make_frame(page, bg=CLR["bg_panel"])
        bar.pack(fill="x")
        make_label(bar, f"  🗳  {title} Election",
                   font=FONTS["heading_md"], bg=CLR["bg_panel"],
                   fg=CLR["gold"]).pack(side="left", pady=14, padx=10)

        # Status banner
        status_frame = make_frame(page, bg=CLR["bg_dark"])
        status_frame.pack(fill="x", padx=20, pady=10)

        status_lbl_attr = f"_status_lbl_{election_type}"
        lbl = make_label(status_frame, "Checking election status…",
                         fg=CLR["sky"], bg=CLR["bg_dark"])
        lbl.pack(anchor="w")
        setattr(self, status_lbl_attr, lbl)

        # Candidate list
        cols = [
            {"id": "name",  "label": "Candidate Name",  "width": 200},
            {"id": "party", "label": "Party",            "width": 200},
            {"id": "const", "label": "Constituency",     "width": 120},
        ]
        tree_attr = f"_tree_{election_type}"
        tree = make_treeview(page, cols, height=14)
        tree.pack(fill="both", expand=True, padx=20, pady=6)
        setattr(self, tree_attr, tree)
        page.pack_propagate(False)

        # Vote button
        btn_attr = f"_vote_btn_{election_type}"
        btn = make_button(page, f"  ✓  Cast My Vote for {title}",
                          command=lambda: self._cast_vote(election_type),
                          style="primary")
        btn.pack(pady=10)
        setattr(self, btn_attr, btn)

        return page

    def _load_candidates(self, election_type: str):
        tree = getattr(self, f"_tree_{election_type}")
        btn  = getattr(self, f"_vote_btn_{election_type}")
        lbl  = getattr(self, f"_status_lbl_{election_type}")

        # Check status
        voted = VoterModel.has_voted(current_session.user_id, election_type)
        is_open = ElectionModel.is_voting_open(election_type)

        if voted:
            lbl.config(text="✓  You have already voted in this election.",
                       fg=CLR["success"])
            btn.config(state="disabled",
                       text="Already Voted ✓", bg=CLR["bg_hover"])
        elif not is_open:
            lbl.config(text="⏳  Voting is currently CLOSED.",
                       fg=CLR["error"])
            btn.config(state="disabled")
        else:
            lbl.config(text="🟢  Voting is OPEN. Select a candidate and vote.",
                       fg=CLR["success"])
            btn.config(state="normal")

        # Load candidates
        candidates = VoterController.get_candidates_for_voter(election_type)
        tree.delete(*tree.get_children())
        for i, c in enumerate(candidates):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end",
                        values=(c["full_name"], c["party_name"],
                                c["constituency_name"]),
                        iid=str(c["id"]), tags=(tag,))

    def _cast_vote(self, election_type: str):
        tree = getattr(self, f"_tree_{election_type}")
        sel  = tree.selection()
        if not sel:
            show_message(self, "No Selection",
                         "Please select a candidate first.", "warning")
            return
        candidate_id = int(sel[0])
        vals = tree.item(sel[0], "values")

        confirmed = ask_confirm(
            self, "Confirm Vote",
            f"You are about to vote for:\n\n"
            f"  Candidate : {vals[0]}\n"
            f"  Party     : {vals[1]}\n"
            f"  Election  : {'National Assembly' if election_type == 'national' else 'Provincial Assembly'}\n\n"
            f"This action CANNOT be undone. Confirm?"
        )
        if not confirmed:
            return

        ok, msg = VoterController.cast_vote(candidate_id, election_type)
        kind = "info" if ok else "error"
        show_message(self, "Vote Result", msg, kind)
        if ok:
            self._load_candidates(election_type)
            # Refresh dashboard cards
            self._update_schedule_label()

    # ─────────────────────────────────────────────────────────
    # HISTORY PAGE
    # ─────────────────────────────────────────────────────────
    def _make_history_page(self) -> tk.Frame:
        page = make_frame(self.content, bg=CLR["bg_dark"])

        bar = make_frame(page, bg=CLR["bg_panel"])
        bar.pack(fill="x")
        make_label(bar, "  📋  My Vote History",
                   font=FONTS["heading_md"], bg=CLR["bg_panel"],
                   fg=CLR["purple"]).pack(side="left", pady=14, padx=10)

        cols = [
            {"id": "etype",      "label": "Election",       "width": 160},
            {"id": "candidate",  "label": "Voted For",       "width": 180},
            {"id": "party",      "label": "Party",           "width": 180},
            {"id": "const",      "label": "Constituency",    "width": 120},
            {"id": "voted_at",   "label": "Voted At",        "width": 160},
        ]
        self._hist_tree = make_treeview(page, cols, height=16)
        self._hist_tree.pack(fill="both", expand=True, padx=20, pady=20)

        self._no_vote_lbl = make_label(page, "No votes recorded yet.",
                                       fg=CLR["text_secondary"],
                                       bg=CLR["bg_dark"],
                                       font=FONTS["body"])
        return page

    def _load_history(self):
        history = VoterModel.get_vote_history(current_session.user_id)
        self._hist_tree.delete(*self._hist_tree.get_children())
        if not history:
            self._no_vote_lbl.pack(pady=20)
        else:
            self._no_vote_lbl.pack_forget()
            for i, h in enumerate(history):
                tag = "even" if i % 2 == 0 else "odd"
                self._hist_tree.insert("", "end", tags=(tag,), values=(
                    h["election_type"].title(),
                    h["candidate_name"],
                    h["party_name"],
                    h["constituency_name"],
                    format_datetime(h["voted_at"]),
                ))

    # ─────────────────────────────────────────────────────────
    # PROFILE PAGE
    # ─────────────────────────────────────────────────────────
    def _make_profile_page(self) -> tk.Frame:
        page = make_frame(self.content, bg=CLR["bg_dark"])

        bar = make_frame(page, bg=CLR["bg_panel"])
        bar.pack(fill="x")
        make_label(bar, "  👤  My Profile",
                   font=FONTS["heading_md"], bg=CLR["bg_panel"],
                   fg=CLR["sky"]).pack(side="left", pady=14, padx=10)

        card = make_frame(page, bg=CLR["bg_card"],
                          highlightthickness=1,
                          highlightbackground=CLR["border"])
        card.pack(padx=60, pady=40, fill="x")

        fields = [
            ("Full Name",   current_session.full_name),
            ("Username",    current_session.username),
            ("CNIC",        current_session.data.get("cnic", "—")),
            ("City",        current_session.data.get("city", "—")),
            ("User ID",     str(current_session.user_id)),
            ("Status",      "Approved ✓"),
        ]

        for label, value in fields:
            row = make_frame(card, bg=CLR["bg_card"])
            row.pack(fill="x", padx=30, pady=8)
            ttk.Separator(card, orient="horizontal").pack(
                fill="x", padx=30)
            make_label(row, label, font=FONTS["body_bold"],
                       fg=CLR["text_secondary"], bg=CLR["bg_card"]).pack(
                side="left", padx=(0, 20))
            make_label(row, value, fg=CLR["text_primary"],
                       bg=CLR["bg_card"]).pack(side="left")

        return page

    # ─────────────────────────────────────────────────────────
    # MISC
    # ─────────────────────────────────────────────────────────
    def _logout(self):
        AuthController.logout()
        self.destroy()
        self.on_logout()

    def _refresh_loop(self):
        """Refresh election status every 30 seconds."""
        self._update_schedule_label()
        self.after(30_000, self._refresh_loop)
