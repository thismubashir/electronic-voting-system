"""
views/theme.py
Central design tokens and reusable widget factory functions.
Pakistan ECP light theme — cream/white, forest green, gold.
Matches the HTML reference design.
"""
import tkinter as tk
from tkinter import ttk
import platform

# ── Color Palette ─────────────────────────────────────────────────────────────
CLR = {
    # Backgrounds (light / cream)
    "bg_dark":       "#F4F1E8",   # off-white cream — main page bg
    "bg_panel":      "#FAFAF7",   # near-white — panels, toolbars
    "bg_card":       "#FFFFFF",   # pure white — cards
    "bg_sidebar":    "#01411C",   # Pakistan green — sidebar
    "bg_input":      "#FEFEFE",   # white — inputs
    "bg_hover":      "#F0FAF5",   # light green tint hover

    # Accents
    "emerald":       "#01411C",   # Pakistan green (primary action)
    "emerald_dark":  "#015C28",   # darker green hover
    "gold":          "#C8A951",   # gold accent
    "gold_dark":     "#9E7E2E",   # darker gold hover
    "pakistan_green":"#01411C",
    "crimson":       "#C0392B",   # danger red
    "crimson_dark":  "#A93226",
    "sky":           "#1A237E",   # deep blue accent
    "sky_dark":      "#0D1757",
    "purple":        "#6A1B9A",
    "orange":        "#E67E22",

    # Text
    "text_primary":  "#1A1A1A",   # near-black
    "text_secondary":"#6B6B6B",   # muted gray
    "text_muted":    "#B0A080",   # light muted
    "text_white":    "#FFFFFF",

    # Borders
    "border":        "#D4C99A",   # warm tan border
    "border_focus":  "#01411C",   # green on focus

    # Status
    "success":       "#1A5C30",   # dark green
    "warning":       "#856400",   # amber text
    "error":         "#7A2020",   # dark red
    "info":          "#1A237E",   # deep blue
}

FONT_FAMILY = "Georgia" if platform.system() == "Darwin" else (
    "Palatino Linotype" if platform.system() == "Windows" else "Georgia"
)
SANS_FAMILY = "Helvetica Neue" if platform.system() == "Darwin" else (
    "Segoe UI" if platform.system() == "Windows" else "Helvetica"
)

FONTS = {
    "heading_xl": (FONT_FAMILY, 26, "bold"),
    "heading_lg": (FONT_FAMILY, 20, "bold"),
    "heading_md": (FONT_FAMILY, 15, "bold"),
    "heading_sm": (SANS_FAMILY, 13, "bold"),
    "body":       (SANS_FAMILY, 11),
    "body_bold":  (SANS_FAMILY, 11, "bold"),
    "small":      (SANS_FAMILY, 10),
    "caption":    (SANS_FAMILY, 9),
    "mono":       ("Courier New", 10),
}


# ── TTK Style Configuration ───────────────────────────────────────────────────
def apply_theme(root: tk.Tk):
    """Apply the light ECP theme to ttk widgets globally."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # Treeview
    style.configure("Treeview",
        background=CLR["bg_card"], foreground=CLR["text_primary"],
        fieldbackground=CLR["bg_card"], rowheight=30,
        borderwidth=0, relief="flat",
        font=FONTS["body"]
    )
    style.configure("Treeview.Heading",
        background=CLR["emerald"], foreground="#FFFFFF",
        font=FONTS["body_bold"], relief="flat", borderwidth=0
    )
    style.map("Treeview",
        background=[("selected", CLR["emerald"])],
        foreground=[("selected", CLR["text_white"])]
    )
    style.map("Treeview.Heading",
        background=[("active", CLR["emerald_dark"])]
    )

    # Scrollbar
    style.configure("Vertical.TScrollbar",
        background=CLR["bg_panel"], troughcolor=CLR["bg_dark"],
        arrowcolor=CLR["text_secondary"], borderwidth=0
    )
    style.configure("Horizontal.TScrollbar",
        background=CLR["bg_panel"], troughcolor=CLR["bg_dark"],
        arrowcolor=CLR["text_secondary"], borderwidth=0
    )

    # Notebook (tabs)
    style.configure("TNotebook",
        background=CLR["bg_dark"], borderwidth=0, tabmargins=[0, 0, 0, 0]
    )
    style.configure("TNotebook.Tab",
        background=CLR["bg_panel"], foreground=CLR["text_secondary"],
        font=FONTS["body_bold"], padding=[16, 8]
    )
    style.map("TNotebook.Tab",
        background=[("selected", CLR["bg_card"]), ("active", CLR["bg_hover"])],
        foreground=[("selected", CLR["emerald"])]
    )

    # Combobox
    style.configure("TCombobox",
        fieldbackground=CLR["bg_input"], background=CLR["bg_input"],
        foreground=CLR["text_primary"], arrowcolor=CLR["emerald"],
        bordercolor=CLR["border"], insertcolor=CLR["text_primary"]
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", CLR["bg_input"])],
        selectbackground=[("readonly", CLR["bg_input"])],
        selectforeground=[("readonly", CLR["text_primary"])],
    )

    # Separator
    style.configure("TSeparator", background=CLR["border"])


# ── Widget Factory ────────────────────────────────────────────────────────────

def make_frame(parent, bg=None, **kw) -> tk.Frame:
    return tk.Frame(parent, bg=bg or CLR["bg_dark"], **kw)


def make_label(parent, text="", font=None, fg=None, bg=None, **kw) -> tk.Label:
    return tk.Label(parent, text=text,
                    font=font or FONTS["body"],
                    fg=fg or CLR["text_primary"],
                    bg=bg or CLR["bg_dark"], **kw)


def make_entry(parent, show=None, width=30, **kw) -> tk.Entry:
    e = tk.Entry(parent, bg=CLR["bg_input"], fg=CLR["text_primary"],
                 insertbackground=CLR["text_primary"],
                 relief="flat", bd=0, font=FONTS["body"],
                 highlightthickness=1,
                 highlightcolor=CLR["border_focus"],
                 highlightbackground=CLR["border"],
                 width=width, **kw)
    if show:
        e.config(show=show)
    return e


def make_button(parent, text="", command=None, style="primary",
                width=None, **kw) -> tk.Button:
    """
    style: 'primary' (green), 'danger' (red), 'secondary' (outline),
           'gold', 'sky', 'ghost'
    """
    colors = {
        "primary":   (CLR["emerald"],    CLR["emerald_dark"],  "#FFFFFF"),
        "danger":    (CLR["crimson"],    CLR["crimson_dark"],  "#FFFFFF"),
        "secondary": ("#FFFFFF",         CLR["bg_hover"],      CLR["emerald"]),
        "gold":      (CLR["gold"],       CLR["gold_dark"],     CLR["emerald"]),
        "sky":       (CLR["sky"],        CLR["sky_dark"],      "#FFFFFF"),
        "ghost":     (CLR["bg_panel"],   CLR["bg_hover"],      CLR["text_secondary"]),
    }
    bg, abg, fg = colors.get(style, colors["primary"])
    btn = tk.Button(parent, text=text, command=command,
                    bg=bg, fg=fg, activebackground=abg, activeforeground=fg,
                    relief="flat", bd=0, cursor="hand2",
                    font=FONTS["body_bold"], padx=16, pady=8, **kw)
    if width:
        btn.config(width=width)
    return btn


def make_search_bar(parent, placeholder="Search…", command=None) -> tk.Entry:
    """Entry styled as a search bar."""
    e = make_entry(parent, width=35)
    e.insert(0, placeholder)
    e.config(fg=CLR["text_muted"])

    def on_focus_in(event):
        if e.get() == placeholder:
            e.delete(0, tk.END)
            e.config(fg=CLR["text_primary"])

    def on_focus_out(event):
        if not e.get():
            e.insert(0, placeholder)
            e.config(fg=CLR["text_muted"])

    def on_key(event):
        if command:
            parent.after(100, lambda: command(e.get()
                         if e.get() != placeholder else ""))

    e.bind("<FocusIn>",  on_focus_in)
    e.bind("<FocusOut>", on_focus_out)
    e.bind("<KeyRelease>", on_key)
    return e


def make_treeview(parent, columns: list, show_scroll=True, height=12) -> ttk.Treeview:
    """Create a styled Treeview with alternating row colors."""
    frame = make_frame(parent, bg=CLR["bg_card"],
                       highlightthickness=1,
                       highlightbackground=CLR["border"])

    col_ids = [c["id"] for c in columns]
    tree = ttk.Treeview(frame, columns=col_ids, show="headings",
                        height=height, selectmode="browse")

    for col in columns:
        tree.heading(col["id"], text=col.get("label", col["id"]))
        tree.column(col["id"],
                    width=col.get("width", 120),
                    anchor=col.get("anchor", "w"),
                    stretch=col.get("stretch", True))

    # Alternating row tags
    tree.tag_configure("odd",  background="#FAFAF7")
    tree.tag_configure("even", background="#FFFFFF")
    tree.tag_configure("approved", foreground=CLR["success"])
    tree.tag_configure("pending",  foreground=CLR["warning"])
    tree.tag_configure("rejected", foreground=CLR["error"])
    tree.tag_configure("winner",   foreground=CLR["gold"],
                       background="#FFF9ED")

    if show_scroll:
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")

    tree.pack(side="left", fill="both", expand=True)
    frame.pack(fill="both", expand=True)
    return tree


def populate_tree(tree: ttk.Treeview, rows: list, keys: list):
    """Clear and repopulate a Treeview."""
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        values = [row.get(k, "") for k in keys]
        tag = "even" if i % 2 == 0 else "odd"
        status = str(row.get("status", "")).lower()
        if status in ("approved", "pending", "rejected"):
            tag = status
        tree.insert("", "end", values=values, tags=(tag,))


def show_message(parent, title: str, message: str, kind: str = "info"):
    """Custom styled message dialog."""
    from tkinter import messagebox
    if kind == "error":
        messagebox.showerror(title, message, parent=parent)
    elif kind == "warning":
        messagebox.showwarning(title, message, parent=parent)
    else:
        messagebox.showinfo(title, message, parent=parent)


def ask_confirm(parent, title: str, message: str) -> bool:
    from tkinter import messagebox
    return messagebox.askyesno(title, message, parent=parent)


def make_card(parent, title: str, value: str, subtitle: str = "",
              accent: str = None) -> tk.Frame:
    """Stat card for dashboards — light card style."""
    acc = accent or CLR["emerald"]
    card = tk.Frame(parent, bg=CLR["bg_card"], relief="flat",
                    highlightthickness=2,
                    highlightbackground=CLR["border"])
    card.config(padx=20, pady=16)

    # Top accent strip via a thin coloured frame
    strip = tk.Frame(card, bg=acc, height=3)
    strip.pack(fill="x", pady=(0, 10))

    tk.Label(card, text=title, font=FONTS["caption"],
             fg=CLR["text_secondary"], bg=CLR["bg_card"]).pack(anchor="w")

    tk.Label(card, text=value, font=(FONT_FAMILY, 28, "bold"),
             fg=acc, bg=CLR["bg_card"]).pack(anchor="w")

    if subtitle:
        tk.Label(card, text=subtitle, font=FONTS["caption"],
                 fg=CLR["text_muted"], bg=CLR["bg_card"]).pack(anchor="w")

    # Hover effect
    def on_enter(e):
        card.config(highlightbackground=acc)
    def on_leave(e):
        card.config(highlightbackground=CLR["border"])

    card.bind("<Enter>", on_enter)
    card.bind("<Leave>", on_leave)
    for child in card.winfo_children():
        child.bind("<Enter>", on_enter)
        child.bind("<Leave>", on_leave)

    return card


def make_labeled_field(parent, label: str, bg=None) -> tuple:
    """Return (frame, entry) for a labeled input row."""
    bg = bg or CLR["bg_dark"]
    frame = tk.Frame(parent, bg=bg)
    tk.Label(frame, text=label.upper(), font=FONTS["caption"],
             fg=CLR["text_secondary"], bg=bg).pack(anchor="w", pady=(0, 3))
    entry = make_entry(frame)
    entry.pack(fill="x")
    return frame, entry
