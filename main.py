import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import random

# ====================================================
# 🌐 Lumina News - Offline Version (GUI + KI Analyzer)
# ====================================================

class NewsDatabase:
    def __init__(self):
        self.data = {
            "Powi": [
                {"title": "Schulen fördern politische Bildung",
                 "desc": "Immer mehr Schulen integrieren politische Bildung, um demokratisches Denken zu stärken.",
                 "date": "2025-10-30", "importance": 4, "link": "https://bildung.de"},
                {"title": "Jugend debattiert boomt",
                 "desc": "Das bundesweite Projekt verzeichnet Rekordzahlen bei der Teilnahme.",
                 "date": "2025-10-29", "importance": 3, "link": "https://jugend-debattiert.de"}
            ],
            "Wirtschaft": [
                {"title": "Deutsche Wirtschaft wächst wieder",
                 "desc": "Nach einer schwierigen Phase zeigt die Wirtschaft 2025 deutliche Erholungstendenzen.",
                 "date": "2025-11-01", "importance": 5, "link": "https://destatis.de"}
            ],
            "Politik": [
                {"title": "Digitalstrategie beschlossen",
                 "desc": "Die Regierung verabschiedet ein umfassendes Digitalpaket für Verwaltung und Schulen.",
                 "date": "2025-10-31", "importance": 5, "link": "https://bundestag.de"}
            ],
            "Sport": [
                {"title": "Deutschland qualifiziert sich für die EM",
                 "desc": "Mit einem 2:0 gegen Italien gelingt die Qualifikation zur Europameisterschaft.",
                 "date": "2025-11-01", "importance": 5, "link": "https://kicker.de"}
            ],
            "Technologie": [
                {"title": "Europäisches KI-Startup begeistert Investoren",
                 "desc": "Ein junges Unternehmen revolutioniert die Bildanalyse durch neue KI-Modelle.",
                 "date": "2025-10-29", "importance": 4, "link": "https://heise.de"}
            ],
            "Weltweit": [
                {"title": "UNO startet globale Friedensinitiative",
                 "desc": "Eine neue Initiative soll Stabilität und Bildung in Krisenregionen fördern.",
                 "date": "2025-10-25", "importance": 5, "link": "https://un.org"}
            ],
            "Allgemein": [
                {"title": "Bahn investiert Milliarden in Infrastruktur",
                 "desc": "Die Bahn kündigt ein groß angelegtes Modernisierungsprogramm an.",
                 "date": "2025-10-22", "importance": 3, "link": "https://bahn.de"}
            ]
        }

    def get_categories(self):
        return list(self.data.keys())

    def get_news(self, category):
        return sorted(self.data.get(category, []),
                      key=lambda n: (n["importance"], n["date"]),
                      reverse=True)


class NewsAnalyzer:
    def __init__(self, db):
        self.db = db

    def most_common_words(self):
        text = " ".join(n["desc"] for cat in self.db.data.values() for n in cat)
        words = [w.lower().strip(".,!?") for w in text.split() if len(w) > 4]
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]

    def category_importance(self):
        res = {}
        for cat, lst in self.db.data.items():
            if lst:
                res[cat] = sum(n["importance"] for n in lst) / len(lst)
        return sorted(res.items(), key=lambda x: x[1], reverse=True)

    def summarize(self, category):
        news = self.db.get_news(category)
        if not news:
            return "Keine Artikel verfügbar."
        return f"{category}: {len(news)} Artikel, Hauptthema: {news[0]['title']}."

    def full_report(self):
        words = ", ".join([w for w, _ in self.most_common_words()])
        cats = ", ".join([f"{c} ({round(v,1)})" for c, v in self.category_importance()])
        return f"🧠 Top Wörter: {words}\n🔥 Aktive Themen: {cats}"


class UserManager:
    def __init__(self):
        self.file = "users.json"
        try:
            with open(self.file, "r") as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.users = {}

    def save(self):
        with open(self.file, "w") as f:
            json.dump(self.users, f)

    def register(self, username, password):
        if username in self.users:
            return False
        self.users[username] = password
        self.save()
        return True

    def login(self, username, password):
        return self.users.get(username) == password


class LuminaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌐 Lumina News")
        self.geometry("1000x600")
        self.db = NewsDatabase()
        self.analyzer = NewsAnalyzer(self.db)
        self.users = UserManager()
        self.current_user = None
        self.theme = "light"
        self.apply_theme()
        self.show_login()

    def apply_theme(self):
        if self.theme == "dark":
            self.bg, self.fg, self.accent = "#1a1a1a", "#ffffff", "#4a90e2"
        elif self.theme == "neon":
            self.bg, self.fg, self.accent = "#0a001f", "#00ff99", "#ff0099"
        else:
            self.bg, self.fg, self.accent = "#fafafa", "#000000", "#0078d7"
        self.configure(bg=self.bg)

    # ---------------- Login ----------------
    def show_login(self):
        for w in self.winfo_children():
            w.destroy()
        frame = ttk.Frame(self)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(frame, text="🔐 Lumina News", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Benutzername:").grid(row=1, column=0)
        user = ttk.Entry(frame)
        user.grid(row=1, column=1)
        ttk.Label(frame, text="Passwort:").grid(row=2, column=0)
        pw = ttk.Entry(frame, show="*")
        pw.grid(row=2, column=1)

        def login():
            if self.users.login(user.get(), pw.get()):
                self.current_user = user.get()
                self.show_main()
            else:
                messagebox.showerror("Fehler", "Ungültiger Login.")

        def register():
            if self.users.register(user.get(), pw.get()):
                messagebox.showinfo("Erfolg", "Benutzer registriert.")
            else:
                messagebox.showwarning("Fehler", "Benutzer existiert bereits.")

        ttk.Button(frame, text="Login", command=login).grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Registrieren", command=register).grid(row=3, column=1, pady=5)

    # ---------------- Hauptansicht ----------------
    def show_main(self):
        for w in self.winfo_children():
            w.destroy()

        sidebar = tk.Frame(self, bg=self.bg)
        sidebar.pack(side="left", fill="y", padx=10, pady=10)
        main = tk.Frame(self, bg=self.bg)
        main.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ttk.Label(sidebar, text=f"👤 {self.current_user}", font=("Segoe UI", 10)).pack(pady=5)
        ttk.Button(sidebar, text="🧠 Analyzer", command=lambda: messagebox.showinfo("Analyzer", self.analyzer.full_report())).pack(fill="x", pady=5)
        ttk.Button(sidebar, text="⚙️ Einstellungen", command=self.settings).pack(fill="x", pady=5)
        ttk.Button(sidebar, text="🚪 Logout", command=self.show_login).pack(fill="x", pady=5)

        ttk.Label(sidebar, text="Kategorien:").pack(pady=10)
        for c in self.db.get_categories():
            ttk.Button(sidebar, text=c, command=lambda cat=c: self.show_news(main, cat)).pack(fill="x", pady=2)

    # ---------------- News Anzeige ----------------
    def show_news(self, frame, category):
        for w in frame.winfo_children():
            w.destroy()
        ttk.Label(frame, text=f"📰 {category}", font=("Segoe UI", 16, "bold")).pack(pady=5)

        for n in self.db.get_news(category):
            box = tk.Frame(frame, bg=self.bg, bd=1, relief="solid", padx=8, pady=6)
            tk.Label(box, text=n["title"], fg=self.accent, bg=self.bg, font=("Segoe UI", 12, "bold")).pack(anchor="w")
            tk.Label(box, text=n["desc"], fg=self.fg, bg=self.bg, wraplength=600, justify="left").pack(anchor="w")
            tk.Label(box, text=f"📅 {n['date']} | Wichtigkeit: {n['importance']}", fg=self.fg, bg=self.bg).pack(anchor="w")
            tk.Label(box, text=f"🔗 {n['link']}", fg=self.accent, bg=self.bg).pack(anchor="w")
            box.pack(fill="x", pady=4)
        ttk.Label(frame, text=f"💡 {self.analyzer.summarize(category)}", font=("Segoe UI", 10, "italic")).pack(pady=10)

    # ---------------- Einstellungen ----------------
    def settings(self):
        win = tk.Toplevel(self)
        win.title("Einstellungen")
        win.geometry("300x200")
        ttk.Label(win, text="🎨 Designmodus:").pack(pady=5)
        combo = ttk.Combobox(win, values=["light", "dark", "neon"])
        combo.set(self.theme)
        combo.pack(pady=5)

        def save():
            self.theme = combo.get()
            self.apply_theme()
            messagebox.showinfo("Gespeichert", "Design geändert.")
            win.destroy()
            self.show_main()

        ttk.Button(win, text="Speichern", command=save).pack(pady=20)


if __name__ == "__main__":
    app = LuminaApp()
    app.mainloop()
