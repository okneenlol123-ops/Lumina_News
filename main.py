import streamlit as st
import json
import os
from datetime import datetime

# =============================
# 🌐 Lumina News - Offline KI Version
# =============================

st.set_page_config(page_title="Lumina News", layout="wide")

# ---------- Benutzerverwaltung ----------
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
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

# ---------- Offline News Daten ----------
def load_news():
    categories = ["Powi", "Wirtschaft", "Politik", "Sport", "Technologie", "Weltweit", "Allgemein"]
    data = {}
    for cat in categories:
        data[cat] = [
            {
                "title": f"{cat} News #{i+1}",
                "desc": f"Dies ist eine lokale Beispielnachricht für {cat}. Hier könnten echte Inhalte angezeigt werden. "
                        "Diese News wurde erstellt, um das Layout der Lumina News KI offline zu testen.",
                "date": f"2025-11-{(i%28)+1:02d}",
                "importance": (i % 5) + 1
            }
            for i in range(10)
        ]
    return data

NEWS_DB = load_news()
CATEGORIES = list(NEWS_DB.keys())
POSITIVE = ["erfolgreich", "gewinnt", "stabil", "lobt", "positiv", "neue", "begeistert"]
NEGATIVE = ["krise", "verlust", "erdbeben", "kritik", "problem", "streit"]

# ---------- KI-Analyse ----------
def analyze_sentiment(text):
    t = text.lower()
    pos = sum(w in t for w in POSITIVE)
    neg = sum(w in t for w in NEGATIVE)
    if pos > neg:
        return "😊 Positiv"
    elif neg > pos:
        return "😞 Negativ"
    return "😐 Neutral"

def top_words(news_list):
    freq = {}
    for n in news_list:
        for w in n["desc"].lower().split():
            w = w.strip(".,!?")
            if len(w) > 5:
                freq[w] = freq.get(w, 0) + 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]

# ---------- Session Setup ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# ---------- Titel ----------
st.markdown(
    """
    <style>
        h1 {
            color: #004aad;
        }
        .stButton>button {
            background-color: #004aad;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
        }
        .stButton>button:hover {
            background-color: #0066ff;
        }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("🌐 Lumina News – Offline KI")

# ---------- Login & Registrierung ----------
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Anmelden", "🆕 Registrieren"])

    with tab1:
        u = st.text_input("Benutzername", key="login_user")
        p = st.text_input("Passwort", type="password", key="login_pass")
        if st.button("Einloggen"):
            if login_user(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.success(f"Willkommen zurück, {u}!")
            else:
                st.error("❌ Falscher Benutzername oder Passwort.")

    with tab2:
        new_u = st.text_input("Neuer Benutzername", key="reg_user")
        new_p = st.text_input("Neues Passwort", type="password", key="reg_pass")
        if st.button("Registrieren"):
            if register_user(new_u, new_p):
                st.success("✅ Registrierung erfolgreich! Bitte einloggen.")
            else:
                st.warning("⚠️ Benutzername existiert bereits.")

else:
    # ---------- Sidebar ----------
    st.sidebar.title(f"👤 Angemeldet als {st.session_state.username}")
    pages = ["🏠 Home"] + CATEGORIES + ["📊 Analyse Gesamt"]
    choice = st.sidebar.radio("Navigiere zu:", pages)

    # ---------- Home ----------
    if choice == "🏠 Home":
        st.header("🏠 Startseite – Wichtigste News")
        st.write("Hier siehst du die wichtigsten News aus allen Kategorien:")

        for cat in CATEGORIES:
            st.subheader(f"📚 {cat}")
            top_news = sorted(NEWS_DB[cat], key=lambda x: x["importance"], reverse=True)[:2]
            for n in top_news:
                st.markdown(f"**{n['title']} ({n['date']})**")
                st.write(n["desc"])
                st.write(f"🧠 Stimmung: {analyze_sentiment(n['desc'])}")
                st.divider()

    # ---------- Einzelne Kategorien ----------
    elif choice in CATEGORIES:
        st.header(f"📰 {choice} – Nachrichtenübersicht")
        news_list = NEWS_DB[choice]
        sort_option = st.radio("Sortieren nach:", ["Wichtigkeit", "Datum"])
        if sort_option == "Datum":
            news_list = sorted(news_list, key=lambda x: x["date"], reverse=True)
        else:
            news_list = sorted(news_list, key=lambda x: x["importance"], reverse=True)

        for n in news_list:
            st.subheader(f"{n['title']} ({n['date']})")
            st.write(n["desc"])
            st.write(f"**Stimmung:** {analyze_sentiment(n['desc'])}")
            st.divider()

        st.markdown("### 🔍 Analyse dieser Kategorie")
        st.write("Top Wörter:", top_words(news_list))

    # ---------- Gesamtanalyse ----------
    elif choice == "📊 Analyse Gesamt":
        st.header("📊 Gesamtanalyse aller Kategorien")
        overall = {}
        for cat, news_list in NEWS_DB.items():
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
        st.info("✨ Die Lumina KI zeigt aktuell ein ausgeglichenes Nachrichtenbild mit Tendenz zu positiven Meldungen.")
