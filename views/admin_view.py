"""
views/admin_view.py
Admin Portal — tabbed interface with all management features.
"""
import tkinter as tk
from tkinter import ttk, filedialog
import shutil, os
from views.theme import (
    CLR, FONTS, make_frame, make_label, make_button, make_entry,
    make_treeview, populate_tree, show_message, ask_confirm,
    make_card, make_search_bar,
)
from controllers import AuthController, AdminController
from models import (
    ConstituencyModel, CandidateModel, ElectionModel,
    VoteModel, AuditModel,
)
from utils.helpers import current_session, format_datetime


class AdminWindow(tk.Toplevel):

    def __init__(self, master, on_logout):
        super().__init__(master)
        self.on_logout = on_logout
        self.title(f"EVS Pakistan — Admin Portal: {current_session.full_name}")
        self.geometry("1280x780")
        self.minsize(1000, 650)
        self.configure(bg=CLR["bg_dark"])
        self.protocol("WM_DELETE_WINDOW", self._logout)
        self._build_layout()

    # ─────────────────────────────────────────────────────────
    def _build_layout(self):
        # Top bar
        topbar = make_frame(self, bg=CLR["bg_sidebar"])
        topbar.pack(fill="x")
        tk.Label(topbar, text="☽ ★  EVS Pakistan  —  Admin Control Panel",
                 font=FONTS["heading_sm"], fg=CLR["gold"],
                 bg=CLR["bg_sidebar"]).pack(side="left", padx=20, pady=10)
        make_button(topbar, "⏻ Logout", command=self._logout,
                    style="danger").pack(side="right", padx=10, pady=6)
        make_label(topbar, f"Logged in as: {current_session.username}",
                   font=FONTS["small"], fg="#A8D5B8",
                   bg=CLR["bg_sidebar"]).pack(side="right", padx=10)

        # Notebook
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._tab_names = []
        self._tabs = [
            ("📊 Dashboard",      self._build_dashboard),
            ("👥 Voters",         self._build_voters),
            ("🏙 Constituencies", self._build_constituencies),
            ("🧑‍💼 Candidates",    self._build_candidates),
            ("📅 Elections",      self._build_elections),
            ("📈 Results",        self._build_results),
            ("📜 Audit Log",      self._build_audit),
        ]
        for label, builder in self._tabs:
            frame = make_frame(self.nb, bg=CLR["bg_dark"])
            self.nb.add(frame, text=f"  {label}  ")
            self._tab_names.append(label)
            builder(frame)

    def _switch_tab(self, tab_label: str):
        for i, name in enumerate(self._tab_names):
            if name == tab_label:
                self.nb.select(i)
                break

    # ═════════════════════════════════════════════════════════
    # DASHBOARD
    # ═════════════════════════════════════════════════════════
    def _build_dashboard(self, parent):
        make_label(parent, "  System Dashboard",
                   font=FONTS["heading_lg"], fg=CLR["emerald"],
                   bg=CLR["bg_dark"]).pack(anchor="w", padx=20, pady=16)

        # Stats row
        self._stats_frame = make_frame(parent, bg=CLR["bg_dark"])
        self._stats_frame.pack(fill="x", padx=20, pady=10)
        self._refresh_dashboard()

        make_button(parent, "🔄  Refresh Stats",
                    command=self._refresh_dashboard,
                    style="secondary").pack(padx=20, pady=6, anchor="w")

        # Quick actions
        sep_frame = make_frame(parent, bg=CLR["bg_dark"])
        sep_frame.pack(fill="x", padx=20, pady=20)
        make_label(sep_frame, "Quick Actions",
                   font=FONTS["heading_sm"], fg=CLR["text_secondary"],
                   bg=CLR["bg_dark"]).pack(anchor="w")

        btns = make_frame(parent, bg=CLR["bg_dark"])
        btns.pack(fill="x", padx=20)
        make_button(btns, "View Pending Approvals",
                    command=lambda: self._switch_tab("👥 Voters"),
                    style="gold").pack(side="left", padx=4)
        make_button(btns, "View All Candidates",
                    command=lambda: self._switch_tab("🧑‍💼 Candidates"),
                    style="sky").pack(side="left", padx=4)
        make_button(btns, "View Live Results",
                    command=lambda: self._switch_tab("📈 Results"),
                    style="primary").pack(side="left", padx=4)

    def _refresh_dashboard(self):
        for w in self._stats_frame.winfo_children():
            w.destroy()

        try:
            stats = AdminController.get_stats()
        except Exception:
            make_label(self._stats_frame, "Could not load stats. Check database connection.",
                       fg=CLR["error"]).pack(pady=20)
            return
        cards_data = [
            ("Total Voters",       str(stats["total_voters"]),     CLR["sky"]),
            ("Approved Voters",    str(stats["approved_voters"]),  CLR["success"]),
            ("Pending Approvals",  str(stats["pending_voters"]),   CLR["warning"]),
            ("Rejected",           str(stats["rejected_voters"]),  CLR["error"]),
            ("Candidates",         str(stats["total_candidates"]), CLR["purple"]),
            ("Total Votes Cast",   str(stats["total_votes"]),      CLR["emerald"]),
            ("Active Elections",   str(stats["active_elections"]), CLR["gold"]),
            ("Constituencies",     str(stats["total_constituencies"]), CLR["orange"]),
        ]
        for i, (title, val, color) in enumerate(cards_data):
            c = make_card(self._stats_frame, title, val, accent=color)
            c.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="ew")

        for col in range(4):
            self._stats_frame.columnconfigure(col, weight=1)

    # ═════════════════════════════════════════════════════════
    # VOTERS
    # ═════════════════════════════════════════════════════════
    def _build_voters(self, parent):
        # Search & filter bar
        toolbar = make_frame(parent, bg=CLR["bg_panel"])
        toolbar.pack(fill="x", padx=0, pady=0)

        make_label(toolbar, "  Filter: ", fg=CLR["text_secondary"],
                   bg=CLR["bg_panel"]).pack(side="left", pady=10)

        self.voter_filter = tk.StringVar(value="all")
        for val, lbl in [("all","All"),("pending","Pending"),
                         ("approved","Approved"),("rejected","Rejected")]:
            rb = tk.Radiobutton(toolbar, text=lbl, variable=self.voter_filter,
                                value=val, command=self._load_voters,
                                bg=CLR["bg_panel"], fg=CLR["text_primary"],
                                selectcolor=CLR["bg_card"], activebackground=CLR["bg_panel"],
                                font=FONTS["body"])
            rb.pack(side="left", padx=6)

        self.voter_search = make_search_bar(toolbar, "Search name, CNIC, constituency…",
                                           command=lambda q: self._load_voters(q))
        self.voter_search.pack(side="right", padx=10, pady=8)

        # Tree
        cols = [
            {"id": "id",      "label": "ID",           "width": 50,  "stretch": False},
            {"id": "cnic",    "label": "CNIC",          "width": 150},
            {"id": "name",    "label": "Full Name",     "width": 160},
            {"id": "city",    "label": "City",          "width": 100},
            {"id": "na",      "label": "NA Const.",     "width": 90},
            {"id": "pp",      "label": "PP Const.",     "width": 90},
            {"id": "status",  "label": "Status",        "width": 90},
            {"id": "regdate", "label": "Registered",    "width": 140},
        ]
        self._voter_tree = make_treeview(parent, cols, height=16)
        self._voter_tree.pack(fill="both", expand=True, padx=10, pady=6)

        # Action buttons
        acts = make_frame(parent, bg=CLR["bg_dark"])
        acts.pack(fill="x", padx=10, pady=6)
        make_button(acts, "✓  Approve Selected", command=self._approve_voter,
                    style="primary").pack(side="left", padx=4)
        make_button(acts, "✗  Reject Selected", command=self._reject_voter,
                    style="danger").pack(side="left", padx=4)
        make_button(acts, "💾 Export CSV", command=self._export_voters_csv,
                    style="gold").pack(side="left", padx=4)
        make_button(acts, "🔄  Refresh", command=self._load_voters,
                    style="secondary").pack(side="right", padx=4)

        self._load_voters()

    def _load_voters(self, search=""):
        f = self.voter_filter.get()
        status = None if f == "all" else f
        rows = AdminController.get_voters(status=status, search=search or None)
        self._voter_tree.delete(*self._voter_tree.get_children())
        for i, r in enumerate(rows):
            tag = r.get("status", "odd")
            self._voter_tree.insert("", "end", iid=str(r["id"]),
                tags=(tag,), values=(
                    r["id"], r["cnic"], r["full_name"], r["city"],
                    r.get("na_name", "—"), r.get("pp_name", "—"),
                    r["status"].title(),
                    format_datetime(r["registered_at"]),
                ))

    def _export_voters_csv(self):
        from tkinter import filedialog
        import csv
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Export Voter List"
        )
        if not path:
            return
        rows = AdminController.get_voters()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "id","cnic","full_name","city","na_name","pp_name",
                "status","registered_at"])
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k,"") for k in
                    ["id","cnic","full_name","city","na_name","pp_name",
                     "status","registered_at"]})
        show_message(self, "Exported", f"Voter list exported:\n{path}", "info")

    def _approve_voter(self):
        sel = self._voter_tree.selection()
        if not sel:
            show_message(self, "No Selection", "Select a voter first.", "warning")
            return
        if not ask_confirm(self, "Approve", "Approve selected voter?"):
            return
        ok, msg = AdminController.approve_voter(int(sel[0]))
        show_message(self, "Result", msg, "info" if ok else "error")
        self._load_voters()

    def _reject_voter(self):
        sel = self._voter_tree.selection()
        if not sel:
            show_message(self, "No Selection", "Select a voter first.", "warning")
            return
        if not ask_confirm(self, "Reject", "Reject selected voter?"):
            return
        ok, msg = AdminController.reject_voter(int(sel[0]))
        show_message(self, "Result", msg, "info" if ok else "error")
        self._load_voters()

    # ═════════════════════════════════════════════════════════
    # CONSTITUENCIES
    # ═════════════════════════════════════════════════════════
    def _build_constituencies(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal",
                               bg=CLR["bg_dark"], sashrelief="flat",
                               sashwidth=6)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: list
        left = make_frame(paned, bg=CLR["bg_dark"])
        paned.add(left, minsize=500)

        toolbar = make_frame(left, bg=CLR["bg_panel"])
        toolbar.pack(fill="x")
        make_label(toolbar, "  Constituencies",
                   font=FONTS["heading_sm"], fg=CLR["text_primary"],
                   bg=CLR["bg_panel"]).pack(side="left", pady=10, padx=8)

        self.const_type_filter = tk.StringVar(value="all")
        for val, lbl in [("all","All"),("national","National"),("provincial","Provincial")]:
            tk.Radiobutton(toolbar, text=lbl, variable=self.const_type_filter,
                           value=val, command=self._load_constituencies,
                           bg=CLR["bg_panel"], fg=CLR["text_primary"],
                           selectcolor=CLR["bg_card"],
                           activebackground=CLR["bg_panel"],
                           font=FONTS["body"]).pack(side="left", padx=4)

        cols = [
            {"id": "id",     "label": "ID",     "width": 50,  "stretch": False},
            {"id": "name",   "label": "Name",   "width": 100},
            {"id": "type",   "label": "Type",   "width": 100},
            {"id": "prov",   "label": "Province","width": 120},
            {"id": "desc",   "label": "Description","width": 200},
        ]
        self._const_tree = make_treeview(left, cols, height=18)
        self._const_tree.pack(fill="both", expand=True)

        acts = make_frame(left, bg=CLR["bg_dark"])
        acts.pack(fill="x", pady=6)
        make_button(acts, "✏  Edit Selected",
                    command=self._edit_constituency,
                    style="sky").pack(side="left", padx=4)
        make_button(acts, "🗑  Delete Selected",
                    command=self._delete_constituency,
                    style="danger").pack(side="left", padx=4)
        make_button(acts, "🔄  Refresh",
                    command=self._load_constituencies,
                    style="secondary").pack(side="right", padx=4)

        # Right: add form
        right = make_frame(paned, bg=CLR["bg_card"])
        paned.add(right, minsize=300)

        make_label(right, "  Add Constituency",
                   font=FONTS["heading_sm"], fg=CLR["emerald"],
                   bg=CLR["bg_card"]).pack(anchor="w", padx=16, pady=12)

        PAD = dict(padx=16, pady=4)

        make_label(right, "Name (e.g. NA-109)",
                   font=FONTS["small"], fg=CLR["text_secondary"],
                   bg=CLR["bg_card"]).pack(anchor="w", **PAD)
        self.cn_name = make_entry(right)
        self.cn_name.pack(fill="x", **PAD)

        make_label(right, "Election Type",
                   font=FONTS["small"], fg=CLR["text_secondary"],
                   bg=CLR["bg_card"]).pack(anchor="w", **PAD)
        self.cn_type = tk.StringVar(value="national")
        for v, t in [("national","National Assembly"),
                     ("provincial","Provincial Assembly")]:
            tk.Radiobutton(right, text=t, variable=self.cn_type,
                           value=v, bg=CLR["bg_card"],
                           fg=CLR["text_primary"], selectcolor=CLR["bg_card"],
                           activebackground=CLR["bg_card"],
                           font=FONTS["body"]).pack(anchor="w", padx=20)

        make_label(right, "Province",
                   font=FONTS["small"], fg=CLR["text_secondary"],
                   bg=CLR["bg_card"]).pack(anchor="w", **PAD)
        self.cn_prov = ttk.Combobox(right,
            values=["Punjab","Sindh","KPK","Balochistan","Islamabad Capital Territory"],
            state="readonly")
        self.cn_prov.pack(fill="x", **PAD)
        self.cn_prov.set("Punjab")

        make_label(right, "Description (optional)",
                   font=FONTS["small"], fg=CLR["text_secondary"],
                   bg=CLR["bg_card"]).pack(anchor="w", **PAD)
        self.cn_desc = make_entry(right)
        self.cn_desc.pack(fill="x", **PAD)

        self.cn_err = make_label(right, fg=CLR["error"], bg=CLR["bg_card"],
                                  wraplength=240)
        self.cn_err.pack(**PAD)

        make_button(right, "➕  Add Constituency",
                    command=self._add_constituency,
                    style="primary").pack(fill="x", **PAD)

        self._load_constituencies()

    def _load_constituencies(self):
        f = self.const_type_filter.get()
        et = None if f == "all" else f
        rows = ConstituencyModel.get_all(election_type=et)
        self._const_tree.delete(*self._const_tree.get_children())
        for i, r in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self._const_tree.insert("", "end", iid=str(r["id"]), tags=(tag,),
                values=(r["id"], r["name"], r["election_type"].title(),
                        r.get("province",""), r.get("description","")))

    def _add_constituency(self):
        self.cn_err.config(text="")
        name = self.cn_name.get().strip().upper()
        prov = self.cn_prov.get()
        desc = self.cn_desc.get().strip()
        et   = self.cn_type.get()
        if not name:
            self.cn_err.config(text="Name is required.")
            return
        ok, msg = AdminController.add_constituency(name, et, prov, desc)
        self.cn_err.config(text=msg, fg=CLR["success"] if ok else CLR["error"])
        if ok:
            self.cn_name.delete(0, tk.END)
            self.cn_desc.delete(0, tk.END)
            self._load_constituencies()

    def _edit_constituency(self):
        sel = self._const_tree.selection()
        if not sel:
            show_message(self, "No Selection", "Select a constituency to edit.", "warning")
            return
        vals = self._const_tree.item(sel[0], "values")
        cid, name, _, prov, desc = vals

        dlg = tk.Toplevel(self)
        dlg.title("Edit Constituency")
        dlg.geometry("360x300")
        dlg.configure(bg=CLR["bg_panel"])
        dlg.grab_set()

        PAD = dict(padx=20, pady=6)
        make_label(dlg, "Name:", font=FONTS["small"],
                   fg=CLR["text_secondary"]).pack(anchor="w", **PAD)
        e_name = make_entry(dlg); e_name.insert(0, name); e_name.pack(fill="x", padx=20)

        make_label(dlg, "Province:", font=FONTS["small"],
                   fg=CLR["text_secondary"]).pack(anchor="w", **PAD)
        e_prov = make_entry(dlg); e_prov.insert(0, prov); e_prov.pack(fill="x", padx=20)

        make_label(dlg, "Description:", font=FONTS["small"],
                   fg=CLR["text_secondary"]).pack(anchor="w", **PAD)
        e_desc = make_entry(dlg); e_desc.insert(0, desc); e_desc.pack(fill="x", padx=20)

        err = make_label(dlg, fg=CLR["error"]); err.pack()

        def save():
            ok, msg = AdminController.update_constituency(
                int(cid), e_name.get().strip(),
                e_prov.get().strip(), e_desc.get().strip()
            )
            if ok:
                dlg.destroy(); self._load_constituencies()
            else:
                err.config(text=msg)

        make_button(dlg, "Save Changes", command=save,
                    style="primary").pack(fill="x", padx=20, pady=10)

    def _delete_constituency(self):
        sel = self._const_tree.selection()
        if not sel:
            show_message(self, "No Selection", "Select a constituency.", "warning")
            return
        if not ask_confirm(self, "Delete",
                           "Delete this constituency? This may affect registered voters."):
            return
        ok, msg = AdminController.delete_constituency(int(sel[0]))
        show_message(self, "Result", msg, "info" if ok else "error")
        self._load_constituencies()

    # ═════════════════════════════════════════════════════════
    # CANDIDATES
    # ═════════════════════════════════════════════════════════
    def _build_candidates(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal",
                               bg=CLR["bg_dark"], sashwidth=6)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: list
        left = make_frame(paned, bg=CLR["bg_dark"])
        paned.add(left, minsize=560)

        toolbar = make_frame(left, bg=CLR["bg_panel"])
        toolbar.pack(fill="x")
        make_label(toolbar, "  Candidates",
                   font=FONTS["heading_sm"], fg=CLR["text_primary"],
                   bg=CLR["bg_panel"]).pack(side="left", pady=10, padx=8)

        self.cand_search = make_search_bar(toolbar, "Search…",
                                           command=lambda q: self._load_candidates(q))
        self.cand_search.pack(side="right", padx=10, pady=8)

        cols = [
            {"id":"id",     "label":"ID",           "width":50, "stretch":False},
            {"id":"name",   "label":"Candidate",    "width":160},
            {"id":"party",  "label":"Party",        "width":160},
            {"id":"type",   "label":"Election",     "width":100},
            {"id":"const",  "label":"Constituency", "width":100},
            {"id":"bio",    "label":"Bio",          "width":200},
        ]
        self._cand_tree = make_treeview(left, cols, height=18)
        self._cand_tree.pack(fill="both", expand=True)

        acts = make_frame(left, bg=CLR["bg_dark"])
        acts.pack(fill="x", pady=6)
        make_button(acts, "✏  Edit", command=self._edit_candidate,
                    style="sky").pack(side="left", padx=4)
        make_button(acts, "🗑  Remove", command=self._delete_candidate,
                    style="danger").pack(side="left", padx=4)
        make_button(acts, "🔄  Refresh", command=self._load_candidates,
                    style="secondary").pack(side="right", padx=4)

        # Right: add form
        right = make_frame(paned, bg=CLR["bg_card"])
        paned.add(right, minsize=300)

        make_label(right, "  Add Candidate",
                   font=FONTS["heading_sm"], fg=CLR["emerald"],
                   bg=CLR["bg_card"]).pack(anchor="w", padx=16, pady=12)

        PAD = dict(padx=16, pady=4)

        def lbl(t): make_label(right, t, font=FONTS["small"],
                               fg=CLR["text_secondary"],
                               bg=CLR["bg_card"]).pack(anchor="w", **PAD)

        lbl("Full Name")
        self.ca_name = make_entry(right); self.ca_name.pack(fill="x", **PAD)

        lbl("Party Name")
        self.ca_party = make_entry(right); self.ca_party.pack(fill="x", **PAD)

        lbl("Election Type")
        self.ca_type = tk.StringVar(value="national")
        fr = make_frame(right, bg=CLR["bg_card"]); fr.pack(anchor="w", padx=16)
        for v, t in [("national","National"),("provincial","Provincial")]:
            tk.Radiobutton(fr, text=t, variable=self.ca_type, value=v,
                           bg=CLR["bg_card"], fg=CLR["text_primary"],
                           selectcolor=CLR["bg_card"],
                           activebackground=CLR["bg_card"],
                           font=FONTS["body"],
                           command=self._refresh_const_dropdown
                           ).pack(side="left", padx=6)

        lbl("Constituency")
        self.ca_const_var = tk.StringVar()
        self.ca_const_cb = ttk.Combobox(right, textvariable=self.ca_const_var,
                                        state="readonly")
        self.ca_const_cb.pack(fill="x", **PAD)

        lbl("Party Symbol Image (optional)")
        sym_frame = make_frame(right, bg=CLR["bg_card"])
        sym_frame.pack(fill="x", **PAD)
        self.ca_sym_path = tk.StringVar(value="")
        self.ca_sym_lbl = make_label(sym_frame, "No file selected",
                                     font=FONTS["small"],
                                     fg=CLR["text_muted"],
                                     bg=CLR["bg_card"])
        self.ca_sym_lbl.pack(side="left")
        make_button(sym_frame, "Browse", command=self._browse_symbol,
                    style="ghost").pack(side="right")

        lbl("Bio (optional)")
        self.ca_bio = tk.Text(right, height=3, bg=CLR["bg_input"],
                              fg=CLR["text_primary"], font=FONTS["body"],
                              relief="flat", bd=0,
                              insertbackground=CLR["text_primary"])
        self.ca_bio.pack(fill="x", **PAD)

        self.ca_err = make_label(right, fg=CLR["error"], bg=CLR["bg_card"],
                                  wraplength=260)
        self.ca_err.pack(**PAD)

        make_button(right, "➕  Add Candidate", command=self._add_candidate,
                    style="primary").pack(fill="x", **PAD)

        self._refresh_const_dropdown()
        self._load_candidates()

    def _refresh_const_dropdown(self):
        et = self.ca_type.get()
        rows = ConstituencyModel.get_all(election_type=et)
        names = [r["name"] for r in rows]
        self._cand_const_map = {r["name"]: r["id"] for r in rows}
        self.ca_const_cb["values"] = names
        if names:
            self.ca_const_cb.set(names[0])

    def _browse_symbol(self):
        path = filedialog.askopenfilename(
            title="Select Party Symbol",
            filetypes=[("Images","*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if path:
            # Copy to assets/symbols
            fname = os.path.basename(path)
            dest  = os.path.join("assets", "symbols", fname)
            os.makedirs("assets/symbols", exist_ok=True)
            shutil.copy2(path, dest)
            self.ca_sym_path.set(dest)
            self.ca_sym_lbl.config(text=fname, fg=CLR["success"])

    def _load_candidates(self, search=""):
        rows = CandidateModel.get_all(search=search or None)
        self._cand_tree.delete(*self._cand_tree.get_children())
        for i, r in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self._cand_tree.insert("", "end", iid=str(r["id"]), tags=(tag,),
                values=(r["id"], r["full_name"], r["party_name"],
                        r["election_type"].title(),
                        r["constituency_name"], r.get("bio","")))

    def _add_candidate(self):
        self.ca_err.config(text="")
        name  = self.ca_name.get().strip()
        party = self.ca_party.get().strip()
        et    = self.ca_type.get()
        const_name = self.ca_const_var.get()
        bio   = self.ca_bio.get("1.0", tk.END).strip()
        sym   = self.ca_sym_path.get() or None

        if not name or not party or not const_name:
            self.ca_err.config(text="Name, party, and constituency are required.")
            return

        cid = self._cand_const_map.get(const_name)
        if not cid:
            self.ca_err.config(text="Invalid constituency selected.")
            return

        ok, msg = AdminController.add_candidate(name, party, cid, et, sym, bio)
        self.ca_err.config(text=msg, fg=CLR["success"] if ok else CLR["error"])
        if ok:
            self.ca_name.delete(0, tk.END)
            self.ca_party.delete(0, tk.END)
            self.ca_bio.delete("1.0", tk.END)
            self.ca_sym_path.set("")
            self.ca_sym_lbl.config(text="No file selected", fg=CLR["text_muted"])
            self._load_candidates()

    def _edit_candidate(self):
        sel = self._cand_tree.selection()
        if not sel:
            show_message(self, "No Selection", "Select a candidate.", "warning")
            return
        r = CandidateModel.get_by_id(int(sel[0]))
        if not r:
            return

        dlg = tk.Toplevel(self)
        dlg.title("Edit Candidate")
        dlg.geometry("400x380")
        dlg.configure(bg=CLR["bg_panel"])
        dlg.grab_set()

        PAD = dict(padx=20, pady=5)

        def lbl(t): make_label(dlg, t, font=FONTS["small"],
                               fg=CLR["text_secondary"]).pack(anchor="w", **PAD)

        lbl("Full Name")
        e_name = make_entry(dlg); e_name.insert(0, r["full_name"])
        e_name.pack(fill="x", padx=20)

        lbl("Party Name")
        e_party = make_entry(dlg); e_party.insert(0, r["party_name"])
        e_party.pack(fill="x", padx=20)

        lbl("Constituency")
        all_const = ConstituencyModel.get_all()
        const_map = {c["name"]: c["id"] for c in all_const}
        const_var = tk.StringVar()
        const_cb = ttk.Combobox(dlg, textvariable=const_var,
                                values=list(const_map.keys()), state="readonly")
        const_cb.set(r["constituency_name"])
        const_cb.pack(fill="x", padx=20)

        lbl("Bio")
        e_bio = make_entry(dlg); e_bio.insert(0, r.get("bio",""))
        e_bio.pack(fill="x", padx=20)

        err = make_label(dlg, fg=CLR["error"]); err.pack()

        def save():
            cid2 = const_map.get(const_var.get())
            ok, msg = AdminController.update_candidate(
                r["id"], e_name.get().strip(), e_party.get().strip(),
                cid2, r.get("party_symbol_path"), e_bio.get().strip()
            )
            if ok:
                dlg.destroy(); self._load_candidates()
            else:
                err.config(text=msg)

        make_button(dlg, "Save Changes", command=save,
                    style="primary").pack(fill="x", padx=20, pady=10)

    def _delete_candidate(self):
        sel = self._cand_tree.selection()
        if not sel:
            show_message(self, "No Selection", "Select a candidate.", "warning")
            return
        if not ask_confirm(self, "Delete", "Remove this candidate?"):
            return
        ok, msg = AdminController.delete_candidate(int(sel[0]))
        show_message(self, "Result", msg, "info" if ok else "error")
        self._load_candidates()

    # ═════════════════════════════════════════════════════════
    # ELECTION SCHEDULE
    # ═════════════════════════════════════════════════════════
    def _build_elections(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal",
                               bg=CLR["bg_dark"], sashwidth=6)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: schedule list
        left = make_frame(paned, bg=CLR["bg_dark"])
        paned.add(left, minsize=540)

        make_label(left, "  Election Schedules",
                   font=FONTS["heading_sm"], fg=CLR["text_primary"],
                   bg=CLR["bg_dark"]).pack(anchor="w", padx=10, pady=8)

        cols = [
            {"id":"id",      "label":"ID",          "width":40, "stretch":False},
            {"id":"type",    "label":"Type",        "width":100},
            {"id":"const",   "label":"Constituency","width":110},
            {"id":"start",   "label":"Start",       "width":150},
            {"id":"end",     "label":"End",         "width":150},
            {"id":"active",  "label":"Active",      "width":70},
            {"id":"by",      "label":"Created By",  "width":120},
        ]
        self._elec_tree = make_treeview(left, cols, height=16)
        self._elec_tree.pack(fill="both", expand=True)

        acts = make_frame(left, bg=CLR["bg_dark"])
        acts.pack(fill="x", pady=6)
        make_button(acts, "🔴  Disable Selected",
                    command=self._disable_election,
                    style="danger").pack(side="left", padx=4)
        make_button(acts, "✏  Edit Selected",
                    command=self._edit_election,
                    style="sky").pack(side="left", padx=4)
        make_button(acts, "🔄  Refresh",
                    command=self._load_elections,
                    style="secondary").pack(side="right", padx=4)

        # Right: schedule form
        right = make_frame(paned, bg=CLR["bg_card"])
        paned.add(right, minsize=310)

        make_label(right, "  Schedule New Election",
                   font=FONTS["heading_sm"], fg=CLR["emerald"],
                   bg=CLR["bg_card"]).pack(anchor="w", padx=16, pady=12)

        PAD = dict(padx=16, pady=4)

        make_label(right, "Election Type", font=FONTS["small"],
                   fg=CLR["text_secondary"], bg=CLR["bg_card"]).pack(anchor="w", **PAD)
        self.es_type = tk.StringVar(value="both")
        for v, t in [("both","Both (NA + PA)"),
                     ("national","National Assembly Only"),
                     ("provincial","Provincial Assembly Only")]:
            tk.Radiobutton(right, text=t, variable=self.es_type, value=v,
                           bg=CLR["bg_card"], fg=CLR["text_primary"],
                           selectcolor=CLR["bg_card"],
                           activebackground=CLR["bg_card"],
                           font=FONTS["body"]).pack(anchor="w", padx=24)

        make_label(right, "Start (YYYY-MM-DD HH:MM)",
                   font=FONTS["small"], fg=CLR["text_secondary"],
                   bg=CLR["bg_card"]).pack(anchor="w", **PAD)
        self.es_start = make_entry(right)
        self.es_start.pack(fill="x", **PAD)

        make_label(right, "End (YYYY-MM-DD HH:MM)",
                   font=FONTS["small"], fg=CLR["text_secondary"],
                   bg=CLR["bg_card"]).pack(anchor="w", **PAD)
        self.es_end = make_entry(right)
        self.es_end.pack(fill="x", **PAD)

        self.es_err = make_label(right, fg=CLR["error"], bg=CLR["bg_card"],
                                  wraplength=260)
        self.es_err.pack(**PAD)

        make_button(right, "➕  Schedule Election",
                    command=self._add_election,
                    style="primary").pack(fill="x", **PAD)

        self._load_elections()

    def _load_elections(self):
        rows = ElectionModel.get_all()
        self._elec_tree.delete(*self._elec_tree.get_children())
        for i, r in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self._elec_tree.insert("", "end", iid=str(r["id"]), tags=(tag,),
                values=(
                    r["id"], r["election_type"].title(),
                    r.get("constituency_name", "All"),
                    format_datetime(r["start_datetime"]),
                    format_datetime(r["end_datetime"]),
                    "Yes ✓" if r["is_active"] else "No",
                    r.get("created_by_name", "—"),
                ))

    def _add_election(self):
        self.es_err.config(text="")
        start = self.es_start.get().strip()
        end   = self.es_end.get().strip()
        et    = self.es_type.get()
        if not start or not end:
            self.es_err.config(text="Start and End datetime are required.")
            return
        ok, msg = AdminController.schedule_election(et, start, end)
        self.es_err.config(text=msg, fg=CLR["success"] if ok else CLR["error"])
        if ok:
            self.es_start.delete(0, tk.END)
            self.es_end.delete(0, tk.END)
            self._load_elections()

    def _disable_election(self):
        sel = self._elec_tree.selection()
        if not sel:
            show_message(self, "No Selection", "Select an election.", "warning")
            return
        if not ask_confirm(self, "Disable", "Disable this election? Voting will stop."):
            return
        ok, msg = AdminController.disable_election(int(sel[0]))
        show_message(self, "Result", msg, "info" if ok else "error")
        self._load_elections()

    def _edit_election(self):
        sel = self._elec_tree.selection()
        if not sel:
            show_message(self, "No Selection", "Select an election.", "warning")
            return
        vals = self._elec_tree.item(sel[0], "values")
        eid = int(sel[0])

        dlg = tk.Toplevel(self)
        dlg.title("Edit Election Schedule")
        dlg.geometry("380x300")
        dlg.configure(bg=CLR["bg_panel"])
        dlg.grab_set()

        PAD = dict(padx=20, pady=6)

        make_label(dlg, "New Start (YYYY-MM-DD HH:MM)",
                   font=FONTS["small"], fg=CLR["text_secondary"]).pack(anchor="w", **PAD)
        e_start = make_entry(dlg); e_start.pack(fill="x", padx=20)

        make_label(dlg, "New End (YYYY-MM-DD HH:MM)",
                   font=FONTS["small"], fg=CLR["text_secondary"]).pack(anchor="w", **PAD)
        e_end = make_entry(dlg); e_end.pack(fill="x", padx=20)

        active_var = tk.IntVar(value=1)
        tk.Checkbutton(dlg, text="Active", variable=active_var,
                       bg=CLR["bg_dark"], fg=CLR["text_primary"],
                       selectcolor=CLR["bg_card"],
                       font=FONTS["body"]).pack(anchor="w", **PAD)

        err = make_label(dlg, fg=CLR["error"]); err.pack()

        def save():
            ok, msg = AdminController.update_election(
                eid, e_start.get().strip(),
                e_end.get().strip(), active_var.get()
            )
            if ok:
                dlg.destroy(); self._load_elections()
            else:
                err.config(text=msg)

        make_button(dlg, "Save", command=save,
                    style="primary").pack(fill="x", padx=20, pady=10)

    # ═════════════════════════════════════════════════════════
    # RESULTS & ANALYTICS
    # ═════════════════════════════════════════════════════════
    def _build_results(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        for et, label in [("national","National Assembly"),
                          ("provincial","Provincial Assembly")]:
            frame = make_frame(nb, bg=CLR["bg_dark"])
            nb.add(frame, text=f"  {label}  ")
            self._build_result_tab(frame, et)

    def _build_result_tab(self, parent, election_type: str):
        # Toolbar
        bar = make_frame(parent, bg=CLR["bg_panel"])
        bar.pack(fill="x")
        make_label(bar, f"  Live Results — {election_type.title()} Assembly",
                   font=FONTS["heading_sm"], fg=CLR["gold"],
                   bg=CLR["bg_panel"]).pack(side="left", pady=10, padx=8)
        make_button(bar, "🔄 Refresh",
                    command=lambda: self._load_results(tree, turnout_lbl, election_type),
                    style="secondary").pack(side="right", padx=10, pady=6)
        make_button(bar, "📊 Chart",
                    command=lambda: self._show_chart(election_type),
                    style="gold").pack(side="right", padx=4, pady=6)
        make_button(bar, "📄 Export PDF",
                    command=lambda: self._export_results_pdf(election_type),
                    style="sky").pack(side="right", padx=4, pady=6)

        # Turnout
        turnout_lbl = make_label(parent, "Loading turnout…",
                                  fg=CLR["sky"], bg=CLR["bg_dark"],
                                  font=FONTS["body"])
        turnout_lbl.pack(anchor="w", padx=20, pady=6)

        # Tree
        cols = [
            {"id":"rank",  "label":"#",            "width":40, "stretch":False},
            {"id":"cand",  "label":"Candidate",    "width":180},
            {"id":"party", "label":"Party",        "width":180},
            {"id":"const", "label":"Constituency", "width":120},
            {"id":"votes", "label":"Votes",        "width":80, "anchor":"e"},
            {"id":"pct",   "label":"% Share",      "width":80, "anchor":"e"},
        ]
        tree = make_treeview(parent, cols, height=16)
        tree.pack(fill="both", expand=True, padx=10, pady=4)
        tree.tag_configure("winner", background="#FFF8E1", foreground="#856400")

        self._load_results(tree, turnout_lbl, election_type)

    def _load_results(self, tree, turnout_lbl, election_type: str):
        rows = VoteModel.get_results(election_type)
        turnout = AdminController.get_turnout(election_type)

        turnout_lbl.config(
            text=f"Eligible Voters: {turnout['eligible']}  |  "
                 f"Voted: {turnout['voted']}  |  "
                 f"Turnout: {turnout['percentage']}%"
        )

        tree.delete(*tree.get_children())

        # Group by constituency, rank within each
        from collections import defaultdict
        by_const = defaultdict(list)
        for r in rows:
            by_const[r["constituency_name"]].append(r)

        rank = 0
        for const_name in sorted(by_const.keys()):
            candidates = sorted(by_const[const_name],
                                key=lambda x: x["vote_count"], reverse=True)
            const_total = sum(c["vote_count"] for c in candidates)
            for i, c in enumerate(candidates):
                rank += 1
                pct = round(c["vote_count"] / const_total * 100, 1) if const_total else 0
                tag = "winner" if i == 0 and c["vote_count"] > 0 else (
                    "even" if rank % 2 == 0 else "odd")
                tree.insert("", "end", tags=(tag,), values=(
                    rank, c["candidate_name"], c["party_name"],
                    c["constituency_name"], c["vote_count"], f"{pct}%"
                ))

    def _show_chart(self, election_type: str):
        """Show a matplotlib bar chart in a new window."""
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            show_message(self, "Missing Library",
                         "Install matplotlib: pip install matplotlib", "error")
            return

        rows = VoteModel.get_results(election_type)
        if not rows:
            show_message(self, "No Data", "No votes to display.", "info")
            return

        # Top 15 candidates
        top = sorted(rows, key=lambda x: x["vote_count"], reverse=True)[:15]
        labels = [f"{r['candidate_name']}\n({r['constituency_name']})" for r in top]
        values = [r["vote_count"] for r in top]
        parties = [r["party_name"] for r in top]

        # Party color map
        party_colors = {
            "Pakistan Tehreek-e-Insaf": "#E94560",
            "Pakistan Muslim League (N)": "#3498DB",
            "Pakistan Peoples Party": "#2ECC71",
            "Jamaat-e-Islami": "#95A5A6",
            "Muttahida Qaumi Movement": "#F39C12",
        }
        colors = [party_colors.get(p, "#8B949E") for p in parties]

        win = tk.Toplevel(self)
        win.title(f"Results Chart — {election_type.title()} Assembly")
        win.geometry("1000x600")
        win.configure(bg=CLR["bg_panel"])

        fig, axes = plt.subplots(1, 2, figsize=(14, 5),
                                  facecolor=CLR["bg_dark"])
        fig.patch.set_facecolor(CLR["bg_dark"])

        # Bar chart
        ax1 = axes[0]
        ax1.set_facecolor(CLR["bg_card"])
        bars = ax1.barh(labels, values, color=colors, edgecolor="none", height=0.6)
        ax1.set_xlabel("Votes", color=CLR["text_secondary"])
        ax1.set_title(f"{election_type.title()} Assembly — Vote Count",
                      color=CLR["text_primary"], pad=12)
        ax1.tick_params(colors=CLR["text_secondary"], labelsize=7)
        ax1.spines[:].set_color(CLR["border"])
        for bar, val in zip(bars, values):
            ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                     str(val), va="center", color=CLR["text_primary"], fontsize=7)

        # Pie chart (by party)
        from collections import defaultdict
        party_totals = defaultdict(int)
        for r in rows:
            party_totals[r["party_name"]] += r["vote_count"]

        ax2 = axes[1]
        ax2.set_facecolor(CLR["bg_card"])
        if party_totals:
            wedge_colors = [party_colors.get(p, "#8B949E")
                            for p in party_totals.keys()]
            wedges, texts, autotexts = ax2.pie(
                party_totals.values(),
                labels=list(party_totals.keys()),
                autopct="%1.1f%%",
                colors=wedge_colors,
                startangle=140,
                textprops={"color": CLR["text_primary"], "fontsize": 7}
            )
            for at in autotexts:
                at.set_color(CLR["bg_dark"])
        ax2.set_title("Party-wise Vote Share",
                      color=CLR["text_primary"], pad=12)

        plt.tight_layout(pad=2)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _export_results_pdf(self, election_type: str):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title=f"Export {election_type.title()} Results PDF",
        )
        if not path:
            return
        from utils.pdf_export import export_results_pdf
        rows = VoteModel.get_results(election_type)
        ok = export_results_pdf(rows, election_type, path)
        if ok:
            show_message(self, "Exported", f"PDF saved to:\n{path}", "info")
        else:
            show_message(self, "Error",
                         "PDF export failed. Is reportlab installed?\n"
                         "Run: pip install reportlab", "error")

    # ═════════════════════════════════════════════════════════
    # AUDIT LOG
    # ═════════════════════════════════════════════════════════
    def _build_audit(self, parent):
        bar = make_frame(parent, bg=CLR["bg_panel"])
        bar.pack(fill="x")
        make_label(bar, "  📜  Audit Log",
                   font=FONTS["heading_sm"], fg=CLR["text_primary"],
                   bg=CLR["bg_panel"]).pack(side="left", pady=10, padx=8)
        make_button(bar, "🔄 Refresh", command=self._load_audit,
                    style="secondary").pack(side="right", padx=10, pady=6)
        make_button(bar, "💾 Export CSV", command=self._export_audit_csv,
                    style="gold").pack(side="right", padx=4, pady=6)

        cols = [
            {"id":"id",      "label":"ID",          "width":60,  "stretch":False},
            {"id":"type",    "label":"User Type",   "width":90},
            {"id":"uid",     "label":"User ID",     "width":70},
            {"id":"action",  "label":"Action",      "width":160},
            {"id":"details", "label":"Details",     "width":300},
            {"id":"ip",      "label":"IP",          "width":110},
            {"id":"time",    "label":"Timestamp",   "width":150},
        ]
        self._audit_tree = make_treeview(parent, cols, height=22)
        self._audit_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._load_audit()

    def _load_audit(self):
        rows = AuditModel.get_recent(200)
        self._audit_tree.delete(*self._audit_tree.get_children())
        for i, r in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self._audit_tree.insert("", "end", tags=(tag,), values=(
                r["id"], r["user_type"], r["user_id"],
                r["action"], r.get("details",""),
                r.get("ip_address",""), format_datetime(r["logged_at"])
            ))

    def _export_audit_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Export Audit Log"
        )
        if not path:
            return
        import csv
        rows = AuditModel.get_recent(10000)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "id","user_type","user_id","action","details","ip_address","logged_at"])
            writer.writeheader()
            writer.writerows(rows)
        show_message(self, "Exported", f"Audit log exported to:\n{path}", "info")

    # ─────────────────────────────────────────────────────────
    def _logout(self):
        AuthController.logout()
        self.destroy()
        self.on_logout()
