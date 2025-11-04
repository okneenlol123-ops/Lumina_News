import json
from datetime import datetime

# =========================
# 🌐 Lumina News CLI (Offline)
# =========================

# ---------- Benutzerverwaltung ----------
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

# ---------- News-Daten ----------
class NewsDatabase:
    def __init__(self):
        self.data = {
            "Powi": [
                {"title": "Schüler diskutieren über Klimaschutz",
                 "desc": "An vielen Schulen wurden in dieser Woche Podiumsdiskussionen zum Thema Klimaschutz veranstaltet. Schülerinnen und Schüler äußerten eigene Vorschläge, wie man lokale CO₂-Emissionen senken könnte.",
                 "date": "2025-11-01", "importance": 4,
                 "link": "https://powinews.de/klimaschutz-schule"},
                {"title": "Neue Unterrichtsreform in NRW",
                 "desc": "Das Bildungsministerium kündigt eine Modernisierung des Politikunterrichts an, um mehr Praxisbezug zu schaffen. Experten begrüßen den Schritt.",
                 "date": "2025-10-20", "importance": 5,
                 "link": "https://powinews.de/unterrichtsreform"},
            ],
            "Wirtschaft": [
                {"title": "Inflation sinkt leicht im Oktober",
                 "desc": "Die Verbraucherpreise in Deutschland sind im Oktober erstmals seit Monaten leicht gesunken. Experten sprechen von einer stabilisierenden Entwicklung.",
                 "date": "2025-11-02", "importance": 5,
                 "link": "https://wirtschaftnews.de/inflation"},
                {"title": "Tech-Unternehmen investieren in KI-Startups",
                 "desc": "Mehrere große Technologiekonzerne kündigten neue Investitionen in europäische KI-Firmen an. Ziel ist es, die Wettbewerbsfähigkeit zu stärken.",
                 "date": "2025-10-25", "importance": 4,
                 "link": "https://wirtschaftnews.de/ki-investments"},
            ],
            "Politik": [
                {"title": "Bundestag debattiert über Energiegesetz",
                 "desc": "In Berlin wurde heute ein neues Energiegesetz diskutiert. Es soll langfristig den Ausbau erneuerbarer Energien fördern und Bürger entlasten.",
                 "date": "2025-11-03", "importance": 5,
                 "link": "https://politiknews.de/energiegesetz"},
                {"title": "Außenministerin besucht Ukraine",
                 "desc": "Die Außenministerin traf in Kiew Regierungsvertreter zu Gesprächen über Sicherheitsgarantien und Wiederaufbauhilfe.",
                 "date": "2025-10-29", "importance": 5,
                 "link": "https://politiknews.de/ukraine-besuch"},
            ],
            "Sport": [
                {"title": "Fußball: Dortmund siegt 3:1 gegen Leipzig",
                 "desc": "Borussia Dortmund gewinnt in einem spannenden Bundesligaspiel mit 3:1 gegen RB Leipzig. Trainer und Fans zeigten sich begeistert.",
                 "date": "2025-11-02", "importance": 4,
                 "link": "https://sportnews.de/bvb"},
                {"title": "Olympia 2028: Neue Disziplinen vorgestellt",
                 "desc": "Das IOC kündigte mehrere neue Sportarten für die Olympischen Spiele 2028 an, darunter E-Sport und Klettern.",
                 "date": "2025-10-21", "importance": 3,
                 "link": "https://sportnews.de/olympia2028"},
            ],
            "Technologie": [
                {"title": "KI-Assistenten werden alltagstauglicher",
                 "desc": "Neue KI-Systeme lernen, komplexe Aufgaben im Alltag zu übernehmen. Forscher betonen die Bedeutung ethischer Leitlinien.",
                 "date": "2025-11-03", "importance": 5,
                 "link": "https://technews.de/ki-assistenten"},
                {"title": "Europäische Raumfahrt startet neue Mission",
                 "desc": "Die ESA hat eine neue Weltraummission gestartet, um Asteroiden zu erforschen. Die Sonde soll 2027 ihr Ziel erreichen.",
                 "date": "2025-10-24", "importance": 4,
                 "link": "https://technews.de/esa-mission"},
            ],
            "Weltweit": [
                {"title": "Gipfeltreffen in New York beendet",
                 "desc": "Nach drei Tagen intensiver Verhandlungen einigten sich Vertreter aus 60 Ländern auf gemeinsame Klimaziele.",
                 "date": "2025-10-31", "importance": 5,
                 "link": "https://weltnews.de/gipfel"},
                {"title": "Erdbeben erschüttert Japan",
                 "desc": "Ein starkes Erdbeben der Stärke 6,4 hat Teile Japans erschüttert. Rettungskräfte sind im Einsatz.",
                 "date": "2025-11-01", "importance": 4,
                 "link": "https://weltnews.de/erdbeben"},
            ],
            "Allgemein": [
                {"title": "Tag der Wissenschaft gefeiert",
                 "desc": "Deutschland feiert den Tag der Wissenschaft mit Ausstellungen und Vorträgen in vielen Städten.",
                 "date": "2025-10-20", "importance": 3,
                 "link": "https://allgemeinnews.de/wissenschaft"},
                {"title": "Neue Bahnstrecke eröffnet",
                 "desc": "Die neue ICE-Strecke zwischen München und Prag verkürzt die Reisezeit erheblich. Verkehrsminister lobt den Ausbau.",
                 "date": "2025-11-01", "importance": 4,
                 "link": "https://allgemeinnews.de/bahnstrecke"},
            ]
        }

    def get_categories(self):
        return list(self.data.keys())

    def get_news(self, category, sort_by="importance"):
        news = self.data.get(category, [])
        if sort_by == "importance":
            return sorted(news, key=lambda x: x["importance"], reverse=True)
        else:
            return sorted(news, key=lambda x: x["date"], reverse=True)

# ---------- Analyzer ----------
class Analyzer:
    POSITIVE_WORDS = ["erfolgreich", "gewinnt", "neue", "stabil", "positiv", "lobt", "verringert", "besser"]
    NEGATIVE_WORDS = ["krise", "streit", "konflikt", "problem", "verlust", "erdbeben", "kritik", "sorge"]

    def __init__(self, db: NewsDatabase):
        self.db = db

    def analyze_sentiment(self, text):
        text = text.lower()
        pos = sum(w in text for w in self.POSITIVE_WORDS)
        neg = sum(w in text for w in self.NEGATIVE_WORDS)
        if pos > neg:
            return "Positiv"
        elif neg > pos:
            return "Negativ"
        return "Neutral"

    def category_overview(self):
        result = {}
        for cat, news_list in self.db.data.items():
            sentiments = [self.analyze_sentiment(n["desc"]) for n in news_list]
            positive = sentiments.count("Positiv")
            negative = sentiments.count("Negativ")
            neutral = sentiments.count("Neutral")
            total = len(news_list)
            result[cat] = {
                "Positiv": positive * 100 // total,
                "Neutral": neutral * 100 // total,
                "Negativ": negative * 100 // total
            }
        return result

    def top_words(self, category):
        words = {}
        for news in self.db.data.get(category, []):
            for w in news["desc"].lower().split():
                w = w.strip(".,!?")
                if len(w) > 5:
                    words[w] = words.get(w, 0) + 1
        return sorted(words.items(), key=lambda x: x[1], reverse=True)[:5]

# ---------- Hauptsystem ----------
def main():
    db = NewsDatabase()
    users = UserManager()
    analyzer = Analyzer(db)

    print("="*60)
    print("🌐 Willkommen bei Lumina News Offline Edition 🌐")
    print("="*60)
    print("1. Starten")
    print("2. Beenden")
    if input("> ") != "1":
        print("👋 Auf Wiedersehen!")
        return

    while True:
        action = input("Willst du [login/register]? ").strip().lower()
        if action == "login":
            u = input("Benutzername: ")
            p = input("Passwort: ")
            if users.login(u, p):
                print(f"✅ Willkommen zurück, {u}!")
                break
            else:
                print("❌ Falsche Daten.")
        elif action == "register":
            u = input("Benutzername: ")
            p = input("Passwort: ")
            if users.register(u, p):
                print("✅ Registrierung erfolgreich!")
            else:
                print("❌ Benutzer existiert bereits.")

    while True:
        print("\nKategorien:")
        for i, c in enumerate(db.get_categories(), 1):
            print(f"{i}. {c}")
        print("8. Analyzer")
        print("0. Beenden")
        choice = input("Wähle Kategorie: ").strip()
        if choice == "0":
            print("\n🧠 Tagesanalyse:")
            overview = analyzer.category_overview()
            for cat, stats in overview.items():
                print(f"{cat}: {stats}")
            print("👋 Bis bald bei Lumina News!")
            break
        elif choice == "8":
            print("\n📊 Kategorie-Analyse:")
            for cat in db.get_categories():
                top_words = analyzer.top_words(cat)
                print(f"{cat}: häufige Wörter: {top_words}")
            continue
        try:
            idx = int(choice)
            if 1 <= idx <= len(db.get_categories()):
                cat = db.get_categories()[idx-1]
                sort_by = input("Sortieren nach [importance/date]: ").strip().lower()
                news_list = db.get_news(cat, sort_by=sort_by)
                print(f"\n📰 {cat} News:")
                for n in news_list:
                    sentiment = analyzer.analyze_sentiment(n["desc"])
                    print(f"- {n['title']} ({n['date']}) | Wichtigkeit: {n['importance']} | Stimmung: {sentiment}")
                    print(f"  {n['desc']}")
                    print(f"  🔗 {n['link']}\n")
            else:
                print("Ungültige Auswahl.")
        except ValueError:
            print("Bitte eine Zahl eingeben.")

if __name__ == "__main__":
    main()
