"""
views/auth_view.py
Login window for Admin and Voter portals + Voter registration form.
"""
import tkinter as tk
from tkinter import ttk
from views.theme import (
    CLR, FONTS, make_frame, make_label, make_entry,
    make_button, show_message, make_labeled_field,
)
from controllers import AuthController, VoterController
from models import ConstituencyModel


class LoginWindow(tk.Toplevel):
    """
    Single window with two tabs: Admin Login | Voter Login.
    Also provides a link to open the Registration form.
    """

    def __init__(self, master, on_admin_success, on_voter_success):
        super().__init__(master)
        self.on_admin_success = on_admin_success
        self.on_voter_success = on_voter_success

        self.title("Electronic Voting System — Pakistan")
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(bg=CLR["bg_dark"])
        self.protocol("WM_DELETE_WINDOW", self.master.destroy)

        self._build_ui()
        self.grab_set()

    # ─────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──────────────────────────────────────────
        hdr = make_frame(self, bg=CLR["bg_sidebar"])
        hdr.pack(fill="x")

        # Crescent + star as text (Pakistan flag inspired)
        tk.Label(hdr, text="☽ ★", font=(FONTS["heading_xl"][0], 36),
                 fg=CLR["gold"], bg=CLR["bg_sidebar"]).pack(pady=(20, 4))

        tk.Label(hdr, text="الیکٹرانک ووٹنگ سسٹم",
                 font=(FONTS["heading_md"][0], 12),
                 fg=CLR["gold"], bg=CLR["bg_sidebar"]).pack()

        tk.Label(hdr, text="Electronic Voting System — Pakistan",
                 font=FONTS["heading_md"],
                 fg="#FFFFFF", bg=CLR["bg_sidebar"]).pack(pady=(4, 20))

        # ── Tabs ─────────────────────────────────────────────
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=24, pady=16)

        self._admin_tab(nb)
        self._voter_tab(nb)

    # ── Admin Login Tab ───────────────────────────────────────
    def _admin_tab(self, nb):
        frame = make_frame(nb, bg=CLR["bg_card"])
        nb.add(frame, text="  🛡  Admin Portal  ")

        inner = make_frame(frame, bg=CLR["bg_card"])
        inner.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.85)

        make_label(inner, "Admin Login", font=FONTS["heading_md"],
                   bg=CLR["bg_card"], fg=CLR["emerald"]).pack(pady=(0, 20))

        # Username
        f1, self.admin_user = make_labeled_field(inner, "Username", CLR["bg_card"])
        f1.pack(fill="x", pady=4)

        # Password
        f2, self.admin_pass = make_labeled_field(inner, "Password", CLR["bg_card"])
        self.admin_pass.config(show="•")
        f2.pack(fill="x", pady=4)

        make_button(inner, "Login as Admin", command=self._admin_login,
                    style="primary").pack(fill="x", pady=(16, 0))

        self.admin_err = make_label(inner, fg=CLR["error"],
                                    bg=CLR["bg_card"], wraplength=280)
        self.admin_err.pack(pady=4)

        # Bind Enter key
        self.bind("<Return>", lambda e: self._admin_login())

    # ── Voter Login Tab ───────────────────────────────────────
    def _voter_tab(self, nb):
        frame = make_frame(nb, bg=CLR["bg_card"])
        nb.add(frame, text="  🗳  Voter Portal  ")

        inner = make_frame(frame, bg=CLR["bg_card"])
        inner.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.85)

        make_label(inner, "Voter Login", font=FONTS["heading_md"],
                   bg=CLR["bg_card"], fg=CLR["sky"]).pack(pady=(0, 20))

        f1, self.voter_user = make_labeled_field(inner, "Username", CLR["bg_card"])
        f1.pack(fill="x", pady=4)

        f2, self.voter_pass = make_labeled_field(inner, "Password", CLR["bg_card"])
        self.voter_pass.config(show="•")
        f2.pack(fill="x", pady=4)

        make_button(inner, "Login as Voter", command=self._voter_login,
                    style="sky").pack(fill="x", pady=(16, 0))

        make_button(inner, "New Voter? Register Here",
                    command=self._open_register,
                    style="ghost").pack(fill="x", pady=4)

        self.voter_err = make_label(inner, fg=CLR["error"],
                                    bg=CLR["bg_card"], wraplength=280)
        self.voter_err.pack(pady=4)

    # ── Actions ──────────────────────────────────────────────
    def _admin_login(self):
        user = self.admin_user.get().strip()
        pwd  = self.admin_pass.get()
        ok, msg = AuthController.admin_login(user, pwd)
        if ok:
            self.destroy()
            self.on_admin_success()
        else:
            self.admin_err.config(text=msg)

    def _voter_login(self):
        user = self.voter_user.get().strip()
        pwd  = self.voter_pass.get()
        ok, msg = AuthController.voter_login(user, pwd)
        if ok:
            self.destroy()
            self.on_voter_success()
        else:
            self.voter_err.config(text=msg)

    def _open_register(self):
        RegisterWindow(self, on_success=lambda: show_message(
            self, "Registered!", "Registration submitted. Await admin approval.",
            "info"
        ))


# ─────────────────────────────────────────────────────────────
# VOTER REGISTRATION WINDOW
# ─────────────────────────────────────────────────────────────
class RegisterWindow(tk.Toplevel):

    def __init__(self, master, on_success=None):
        super().__init__(master)
        self.on_success = on_success
        self.title("Voter Registration")
        self.geometry("520x680")
        self.resizable(False, False)
        self.configure(bg=CLR["bg_dark"])
        self.grab_set()
        self._build()

    def _build(self):
        # Title bar
        bar = make_frame(self, bg=CLR["pakistan_green"])
        bar.pack(fill="x")
        make_label(bar, "  New Voter Registration", font=FONTS["heading_md"],
                   bg=CLR["pakistan_green"], fg=CLR["text_white"]).pack(
            side="left", pady=12)

        # Scrollable inner
        canvas = tk.Canvas(self, bg=CLR["bg_dark"], highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = make_frame(canvas, bg=CLR["bg_dark"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", on_resize)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))

        PAD = {"padx": 30, "pady": 6}

        def field(label, show=None, width=40):
            make_label(inner, label, font=FONTS["small"],
                       fg=CLR["text_secondary"]).pack(anchor="w", **PAD)
            e = make_entry(inner, width=width, show=show)
            e.pack(fill="x", padx=30)
            return e

        self.cnic     = field("CNIC  (e.g. 35202-1234567-8)")
        self.name     = field("Full Name")
        self.city     = field("City")

        # Constituencies from DB
        na_names = [r["name"] for r in ConstituencyModel.get_national()]
        pp_names = [r["name"] for r in ConstituencyModel.get_provincial()]

        make_label(inner, "National Assembly Constituency",
                   font=FONTS["small"], fg=CLR["text_secondary"]).pack(
            anchor="w", **PAD)
        self.na_var = tk.StringVar()
        self.na_cb  = ttk.Combobox(inner, textvariable=self.na_var,
                                    values=na_names, state="readonly", width=38)
        self.na_cb.pack(padx=30, fill="x")
        if na_names:
            self.na_cb.set(na_names[0])

        make_label(inner, "Provincial Assembly Constituency",
                   font=FONTS["small"], fg=CLR["text_secondary"]).pack(
            anchor="w", **PAD)
        self.pp_var = tk.StringVar()
        self.pp_cb  = ttk.Combobox(inner, textvariable=self.pp_var,
                                    values=pp_names, state="readonly", width=38)
        self.pp_cb.pack(padx=30, fill="x")
        if pp_names:
            self.pp_cb.set(pp_names[0])

        self.username = field("Username")
        self.password = field("Password", show="•")
        self.confirm  = field("Confirm Password", show="•")

        self.err_lbl = make_label(inner, fg=CLR["error"], wraplength=420)
        self.err_lbl.pack(**PAD)

        make_button(inner, "Submit Registration", command=self._submit,
                    style="primary").pack(fill="x", padx=30, pady=10)

    def _submit(self):
        self.err_lbl.config(text="")
        pwd = self.password.get()
        if pwd != self.confirm.get():
            self.err_lbl.config(text="Passwords do not match.")
            return

        ok, msg = VoterController.register(
            cnic       = self.cnic.get().strip(),
            full_name  = self.name.get().strip(),
            city       = self.city.get().strip(),
            na_name    = self.na_var.get(),
            pp_name    = self.pp_var.get(),
            username   = self.username.get().strip(),
            password   = pwd,
        )
        if ok:
            show_message(self, "Success", msg, "info")
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.err_lbl.config(text=msg)
