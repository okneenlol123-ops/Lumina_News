import tkinter as tk
from tkinter import ttk, messagebox
from main import NewsDatabase, NewsAnalyzer, UserManager

# ====================================================
# 🌈 Lumina News - GUI Frontend
# ====================================================

class LuminaNewsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lumina News")
        self.geometry("1000x600")
        self.db = NewsDatabase()
        self.users = UserManager()
        self.analyzer = NewsAnalyzer(self.db)
        self.current_user = None
        self.theme = "light"
        self.configure_theme()
        self.show_login()

    # ---------------------- Theme ----------------------
    def configure_theme(self):
        if self.theme == "dark":
            self.bg, self.fg, self.accent = "#202020", "#eeeeee", "#4a90e2"
        elif self.theme == "neon":
            self.bg, self.fg, self.accent = "#080018", "#39ff14", "#ff00cc"
        else:
            self.bg, self.fg, self.accent = "#fafafa", "#111", "#0078d7"
        self.configure(bg=self.bg)

    # ---------------------- Login ----------------------
    def show_login(self):
        for w in self.winfo_children():
            w.destroy()
        frame = ttk.Frame(self)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(frame, text="🌐 Lumina News Login", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
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
                messagebox.showerror("Fehler", "Ungültige Login-Daten.")

        def register():
            if self.users.register(user.get(), pw.get()):
                messagebox.showinfo("Erfolg", "Registrierung erfolgreich.")
            else:
                messagebox.showwarning("Hinweis", "Benutzer existiert bereits.")

        ttk.Button(frame, text="Login", command=login).grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Registrieren", command=register).grid(row=3, column=1, pady=5)

    # ---------------------- Hauptansicht ----------------------
    def show_main(self):
        for w in self.winfo_children():
            w.destroy()
        left = tk.Frame(self, bg=self.bg)
        left.pack(side="left", fill="y", padx=10, pady=10)
        right = tk.Frame(self, bg=self.bg)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ttk.Label(left, text=f"👤 {self.current_user}", font=("Segoe UI", 10)).pack(pady=5)
        ttk.Button(left, text="🧠 Analyzer", command=lambda: messagebox.showinfo("Analyzer", self.analyzer.full_report())).pack(fill="x", pady=5)
        ttk.Button(left, text="⚙️ Einstellungen", command=self.settings_window).pack(fill="x", pady=5)
        ttk.Button(left, text="🚪 Logout", command=self.show_login).pack(fill="x", pady=5)
        ttk.Label(left, text="Kategorien:").pack(pady=10)
        for c in self.db.get_categories():
            ttk.Button(left, text=c, command=lambda cat=c: self.show_news(right, cat)).pack(fill="x", pady=2)

    # ---------------------- News ----------------------
    def show_news(self, frame, category):
        for w in frame.winfo_children():
            w.destroy()
        ttk.Label(frame, text=f"📰 {category} News", font=("Segoe UI", 16, "bold")).pack(pady=5)
        for n in self.db.get_news(category):
            box = tk.Frame(frame, bg=self.bg, bd=1, relief="solid", padx=10, pady=6)
            tk.Label(box, text=n["title"], fg=self.accent, bg=self.bg, font=("Segoe UI", 12, "bold")).pack(anchor="w")
            tk.Label(box, text=n["desc"], fg=self.fg, bg=self.bg, wraplength=600, justify="left").pack(anchor="w")
            tk.Label(box, text=f"📅 {n['date']} | Wichtigkeit: {n['importance']}", bg=self.bg, fg=self.fg).pack(anchor="w")
            tk.Label(box, text=f"🔗 {n['link']}", fg=self.accent, bg=self.bg).pack(anchor="w")
            box.pack(fill="x", pady=5)
        summary = self.analyzer.summarize(category)
        ttk.Label(frame, text=f"💡 {summary}", font=("Segoe UI", 10, "italic")).pack(pady=10)

    # ---------------------- Einstellungen ----------------------
    def settings_window(self):
        win = tk.Toplevel(self)
        win.title("Einstellungen")
        win.geometry("300x250")
        ttk.Label(win, text="🎨 Designmodus").pack(pady=5)
        theme_box = ttk.Combobox(win, values=["light", "dark", "neon"])
        theme_box.set(self.theme)
        theme_box.pack()
        def save():
            self.theme = theme_box.get()
            self.configure_theme()
            messagebox.showinfo("OK", "Design geändert.")
            win.destroy()
        ttk.Button(win, text="Speichern", command=save).pack(pady=20)


if __name__ == "__main__":
    app = LuminaNewsApp()
    app.mainloop()
