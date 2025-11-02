import json
import random
from datetime import datetime

# ====================================================
# 🧠 Lumina News - KI Logik & Daten (Offline Version)
# ====================================================

class NewsDatabase:
    """Offline gespeicherte News für 7 Kategorien"""
    def __init__(self):
        self.data = {
            "Powi": [
                {"title": "Schulen fördern politische Bildung",
                 "desc": "Immer mehr Schulen integrieren politische Bildung in den Unterricht.",
                 "date": "2025-10-30", "importance": 4, "link": "https://bildung.de"},
                {"title": "Jugend debattiert gewinnt an Beliebtheit",
                 "desc": "Das bekannte Schülerformat wächst stark an deutschen Schulen.",
                 "date": "2025-10-28", "importance": 3, "link": "https://jugend-debattiert.de"}
            ],
            "Wirtschaft": [
                {"title": "Deutsche Wirtschaft stabilisiert sich",
                 "desc": "Nach schwierigen Jahren zeigt die Wirtschaft wieder Wachstum.",
                 "date": "2025-11-01", "importance": 5, "link": "https://destatis.de"}
            ],
            "Politik": [
                {"title": "Bundestag beschließt Digitalstrategie",
                 "desc": "Die Regierung will Deutschland digitaler machen.",
                 "date": "2025-10-31", "importance": 5, "link": "https://bundestag.de"}
            ],
            "Sport": [
                {"title": "Deutschland gewinnt EM-Qualifikation",
                 "desc": "Mit einem 2:0 gegen Italien zieht Deutschland in die EM ein.",
                 "date": "2025-11-01", "importance": 5, "link": "https://kicker.de"}
            ],
            "Technologie": [
                {"title": "Europäisches KI-Startup beeindruckt",
                 "desc": "Ein neues Unternehmen revolutioniert maschinelles Lernen.",
                 "date": "2025-10-29", "importance": 4, "link": "https://heise.de"}
            ],
            "Weltweit": [
                {"title": "UNO startet Friedensinitiative",
                 "desc": "Eine neue globale Initiative soll Stabilität fördern.",
                 "date": "2025-10-25", "importance": 5, "link": "https://un.org"}
            ],
            "Allgemein": [
                {"title": "Bahn investiert in neue Strecken",
                 "desc": "Die Deutsche Bahn plant ein Rekordinvestitionsprogramm.",
                 "date": "2025-10-22", "importance": 3, "link": "https://bahn.de"}
            ]
        }

    def get_categories(self):
        return list(self.data.keys())

    def get_news(self, category):
        return sorted(
            self.data.get(category, []),
            key=lambda n: (n["importance"], n["date"]),
            reverse=True
        )


# ====================================================
# 🤖 KI Analyzer für News
# ====================================================

class NewsAnalyzer:
    """Einfache lokale 'KI'-Analyse"""
    def __init__(self, db: NewsDatabase):
        self.db = db

    def most_common_words(self):
        text = " ".join(n["desc"] for cat in self.db.data.values() for n in cat)
        words = [w.lower() for w in text.split() if len(w) > 4]
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]

    def category_importance(self):
        result = {}
        for cat, lst in self.db.data.items():
            if lst:
                result[cat] = sum(n["importance"] for n in lst) / len(lst)
        return sorted(result.items(), key=lambda x: x[1], reverse=True)

    def summarize(self, category):
        news = self.db.get_news(category)
        if not news:
            return "Keine Daten."
        titles = [n["title"] for n in news]
        return f"{category}: {len(news)} Artikel. Wichtigstes Thema: {titles[0]}."

    def full_report(self):
        words = ", ".join([w for w, _ in self.most_common_words()])
        trends = self.category_importance()
        trend_text = ", ".join([f"{c} ({round(v,1)})" for c, v in trends])
        return f"🧠 Häufige Begriffe: {words}\n🔥 Aktive Kategorien: {trend_text}"


# ====================================================
# 🧑‍💻 Benutzerverwaltung
# ====================================================

class UserManager:
    def __init__(self):
        self.users = {}

    def register(self, username, password):
        if username in self.users:
            return False
        self.users[username] = password
        return True

    def login(self, username, password):
        return self.users.get(username) == password
