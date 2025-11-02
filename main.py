import json
from datetime import datetime
import random

# ============================
# 🧠 Lumina News Offline CLI
# ============================

# ------------------- News-Daten -------------------
class NewsDatabase:
    def __init__(self):
        self.data = {
            "Powi": [{"title": f"Powi-News {i}", 
                      "desc": f"Beschreibung von Powi News {i} für Schüler.",
                      "date": f"2025-10-{30-i:02d}", 
                      "importance": random.randint(1,5),
                      "link": f"https://powi{i}.de"} for i in range(1,11)],
            "Wirtschaft": [{"title": f"Wirtschaft-News {i}", 
                             "desc": f"Wirtschaftliche Entwicklungen {i}.",
                             "date": f"2025-11-{i:02d}", 
                             "importance": random.randint(1,5),
                             "link": f"https://wirtschaft{i}.de"} for i in range(1,11)],
            "Politik": [{"title": f"Politik-News {i}", 
                         "desc": f"Politische Entscheidungen {i}.",
                         "date": f"2025-10-{i:02d}", 
                         "importance": random.randint(1,5),
                         "link": f"https://politik{i}.de"} for i in range(1,11)],
            "Sport": [{"title": f"Sport-News {i}", 
                       "desc": f"Sportevents {i} erklärt.",
                       "date": f"2025-11-{i:02d}", 
                       "importance": random.randint(1,5),
                       "link": f"https://sport{i}.de"} for i in range(1,11)],
            "Technologie": [{"title": f"Tech-News {i}", 
                             "desc": f"Technologie-Entwicklung {i}.",
                             "date": f"2025-10-{i:02d}", 
                             "importance": random.randint(1,5),
                             "link": f"https://tech{i}.de"} for i in range(1,11)],
            "Weltweit": [{"title": f"Welt-News {i}", 
                          "desc": f"Internationale Ereignisse {i}.",
                          "date": f"2025-10-{i:02d}", 
                          "importance": random.randint(1,5),
                          "link": f"https://welt{i}.de"} for i in range(1,11)],
            "Allgemein": [{"title": f"Allgemein-News {i}", 
                           "desc": f"Allgemeine Neuigkeiten {i}.",
                           "date": f"2025-10-{i:02d}", 
                           "importance": random.randint(1,5),
                           "link": f"https://allgemein{i}.de"} for i in range(1,11)]
        }

    def get_categories(self):
        return list(self.data.keys())

    def get_news(self, category, sort_by="importance"):
        if sort_by=="importance":
            return sorted(self.data[category], key=lambda x: x["importance"], reverse=True)
        else:
            return sorted(self.data[category], key=lambda x: x["date"], reverse=True)

# ------------------- Benutzer -------------------
class UserManager:
    def __init__(self):
        try:
            with open("users.json", "r") as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.users = {}

    def save(self):
        with open("users.json", "w") as f:
            json.dump(self.users, f)

    def register(self, username, password):
        if username in self.users:
            return False
        self.users[username] = password
        self.save()
        return True

    def login(self, username, password):
        return self.users.get(username) == password

# ------------------- Analyzer -------------------
class NewsAnalyzer:
    def __init__(self, db: NewsDatabase):
        self.db = db

    def most_common_words(self):
        text = " ".join(n["desc"] for cat in self.db.data.values() for n in cat)
        words = [w.strip(".,!?").lower() for w in text.split() if len(w)>4]
        freq = {}
        for w in words:
            freq[w] = freq.get(w,0)+1
        return sorted(freq.items(), key=lambda x:x[1], reverse=True)[:5]

    def category_importance(self):
        res = {}
        for cat, lst in self.db.data.items():
            res[cat] = sum(n["importance"] for n in lst)/len(lst)
        return sorted(res.items(), key=lambda x:x[1], reverse=True)

# ------------------- CLI Interface -------------------
def main():
    db = NewsDatabase()
    users = UserManager()
    analyzer = NewsAnalyzer(db)

    print("🌐 Willkommen bei Lumina News CLI!")

    while True:
        action = input("Willst du [login/register/exit]? ").strip().lower()
        if action=="login":
            u = input("Benutzername: ")
            p = input("Passwort: ")
            if users.login(u,p):
                print(f"✅ Willkommen, {u}!")
                break
            else:
                print("❌ Login fehlgeschlagen.")
        elif action=="register":
            u = input("Benutzername: ")
            p = input("Passwort: ")
            if users.register(u,p):
                print("✅ Registrierung erfolgreich!")
            else:
                print("❌ Benutzer existiert bereits.")
        elif action=="exit":
            return

    while True:
        print("\nKategorien:")
        for i, c in enumerate(db.get_categories(),1):
            print(f"{i}. {c}")
        print("0. Analyzer / Trends / Exit")
        choice = input("Wähle Kategorie (Nummer): ").strip()
        if choice=="0":
            print("\n🧠 News Analyzer:")
            print("Häufigste Wörter:", analyzer.most_common_words())
            print("Durchschnittliche Wichtigkeit je Kategorie:", analyzer.category_importance())
            continue
        try:
            choice = int(choice)
            if 1 <= choice <= len(db.get_categories()):
                cat = db.get_categories()[choice-1]
                sort_method = input("Sortieren nach [importance/date]? ").strip().lower()
                news_list = db.get_news(cat, sort_by=sort_method)
                print(f"\n📰 {cat} News:")
                for n in news_list:
                    print(f"- {n['title']} ({n['date']}) | Wichtigkeit: {n['importance']}")
                    print(f"  {n['desc']}")
                    print(f"  Link: {n['link']}\n")
            else:
                print("Ungültige Wahl.")
        except ValueError:
            print("Bitte Zahl eingeben.")

if __name__=="__main__":
    main()
