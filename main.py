import streamlit as st
import json
from datetime import datetime

# =============================
# 🌐 Lumina News - Streamlit Edition
# =============================

# ---------- Benutzerverwaltung ----------
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = password
    save_users(users)
    return True

def login_user(username, password):
    users = load_users()
    return users.get(username) == password

# ---------- News Datenbank ----------
def load_news():
    return {
        "Powi": [
            {"title": "Schüler diskutieren über Klimaschutz",
             "desc": "An vielen Schulen wurden Diskussionen zum Thema Klimaschutz veranstaltet. Schülerinnen und Schüler äußerten eigene Vorschläge, wie man lokale CO₂-Emissionen senken könnte.",
             "date": "2025-11-01", "importance": 4},
            {"title": "Neue Unterrichtsreform in NRW",
             "desc": "Das Bildungsministerium kündigt eine Modernisierung des Politikunterrichts an, um mehr Praxisbezug zu schaffen. Experten begrüßen den Schritt.",
             "date": "2025-10-20", "importance": 5}
        ],
        "Wirtschaft": [
            {"title": "Inflation sinkt leicht im Oktober",
             "desc": "Die Verbraucherpreise sind im Oktober leicht gesunken. Experten sprechen von einer stabilisierenden Entwicklung.",
             "date": "2025-11-02", "importance": 5},
            {"title": "Tech-Unternehmen investieren in KI-Startups",
             "desc": "Große Technologiekonzerne investieren in europäische KI-Firmen, um Innovation zu fördern.",
             "date": "2025-10-25", "importance": 4}
        ],
        "Politik": [
            {"title": "Bundestag debattiert über Energiegesetz",
             "desc": "In Berlin wurde ein neues Energiegesetz diskutiert, das den Ausbau erneuerbarer Energien fördern soll.",
             "date": "2025-11-03", "importance": 5},
            {"title": "Außenministerin besucht Ukraine",
             "desc": "Die Außenministerin traf in Kiew Regierungsvertreter zu Gesprächen über Sicherheitsgarantien.",
             "date": "2025-10-29", "importance": 5}
        ],
        "Sport": [
            {"title": "Dortmund siegt 3:1 gegen Leipzig",
             "desc": "Borussia Dortmund gewinnt in einem spannenden Spiel mit 3:1. Trainer und Fans zeigten sich begeistert.",
             "date": "2025-11-02", "importance": 4},
            {"title": "Olympia 2028: Neue Disziplinen vorgestellt",
             "desc": "Das IOC kündigte neue Sportarten an, darunter E-Sport und Klettern.",
             "date": "2025-10-21", "importance": 3}
        ],
        "Technologie": [
            {"title": "KI-Assistenten werden alltagstauglicher",
             "desc": "Neue KI-Systeme übernehmen komplexe Aufgaben im Alltag. Forscher betonen ethische Leitlinien.",
             "date": "2025-11-03", "importance": 5},
            {"title": "ESA startet neue Asteroidenmission",
             "desc": "Die ESA startet eine neue Weltraummission, um Asteroiden zu erforschen.",
             "date": "2025-10-24", "importance": 4}
        ],
        "Weltweit": [
            {"title": "Gipfeltreffen in New York beendet",
             "desc": "Vertreter aus 60 Ländern einigten sich auf neue Klimaziele.",
             "date": "2025-10-31", "importance": 5},
            {"title": "Erdbeben erschüttert Japan",
             "desc": "Ein Erdbeben der Stärke 6,4 hat Teile Japans erschüttert. Rettungskräfte sind im Einsatz.",
             "date": "2025-11-01", "importance": 4}
        ],
        "Allgemein": [
            {"title": "Tag der Wissenschaft gefeiert",
             "desc": "Deutschland feiert den Tag der Wissenschaft mit Ausstellungen und Vorträgen.",
             "date": "2025-10-20", "importance": 3},
            {"title": "Neue Bahnstrecke eröffnet",
             "desc": "Die neue ICE-Strecke zwischen München und Prag verkürzt die Reisezeit erheblich.",
             "date": "2025-11-01", "importance": 4}
        ]
    }

# ---------- Analyzer ----------
POSITIVE = ["erfolgreich", "gewinnt", "stabil", "lobt", "positiv", "neue", "begeistert"]
NEGATIVE = ["krise", "verlust", "erdbeben", "kritik", "problem", "streit"]

def analyze_sentiment(text):
    t = text.lower()
    pos = sum(w in t for w in POSITIVE)
    neg = sum(w in t for w in NEGATIVE)
    if pos > neg:
        return "😊 Positiv"
    elif neg > pos:
        return "😞 Negativ"
    else:
        return "😐 Neutral"

def top_words(news_list):
    freq = {}
    for n in news_list:
        for w in n["desc"].lower().split():
            w = w.strip(".,!?")
            if len(w) > 5:
                freq[w] = freq.get(w, 0) + 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]

# ---------- Streamlit Layout ----------
st.set_page_config(page_title="Lumina News", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.title("🌐 Lumina News - Offline Edition")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Registrieren"])

    with tab1:
        u = st.text_input("Benutzername")
        p = st.text_input("Passwort", type="password")
        if st.button("Einloggen"):
            if login_user(u, p):
                st.session_state.logged_in = True
                st.success(f"Willkommen zurück, {u}!")
                st.experimental_rerun()
            else:
                st.error("Falsche Zugangsdaten!")

    with tab2:
        new_u = st.text_input("Neuer Benutzername")
        new_p = st.text_input("Neues Passwort", type="password")
        if st.button("Registrieren"):
            if register_user(new_u, new_p):
                st.success("Registrierung erfolgreich!")
            else:
                st.error("Benutzer existiert bereits.")
else:
    news_db = load_news()
    pages = list(news_db.keys()) + ["Analyse Gesamt"]
    st.sidebar.title("🗂️ Kategorien")
    choice = st.sidebar.radio("Wähle Kategorie:", pages)

    if choice != "Analyse Gesamt":
        st.header(f"📰 {choice}")
        news_list = news_db[choice]

        sort_option = st.radio("Sortieren nach:", ["Wichtigkeit", "Datum"])
        if sort_option == "Datum":
            news_list = sorted(news_list, key=lambda x: x["date"], reverse=True)
        else:
            news_list = sorted(news_list, key=lambda x: x["importance"], reverse=True)

        for n in news_list:
            st.subheader(f"{n['title']} ({n['date']})")
            st.write(n["desc"])
            sentiment = analyze_sentiment(n["desc"])
            st.write(f"**Stimmung:** {sentiment}")
            st.divider()

        st.markdown("### 🔍 Analyse dieser Kategorie")
        st.write("Top Wörter:", top_words(news_list))

    else:
        st.header("📊 Gesamtanalyse")
        overall = {}
        for cat, news_list in news_db.items():
            sentiments = [analyze_sentiment(n["desc"]) for n in news_list]
            pos = sentiments.count("😊 Positiv")
            neg = sentiments.count("😞 Negativ")
            neu = sentiments.count("😐 Neutral")
            total = len(news_list)
            overall[cat] = {
                "Positiv": pos * 100 // total,
                "Neutral": neu * 100 // total,
                "Negativ": neg * 100 // total
            }

        for cat, stats in overall.items():
            st.subheader(cat)
            st.write(stats)

        st.markdown("---")
        st.info("✨ Zusammenfassung: Lumina News zeigt insgesamt ein ausgewogenes Nachrichtenbild mit leichten positiven Tendenzen.")
