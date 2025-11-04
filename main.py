import streamlit as st
from datetime import datetime

# =============================
# 🌐 Lumina News - Offline Streamlit Edition
# =============================

# ---------- Session-State Setup ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# ---------- Dummy User-Daten ----------
USERS = {"admin": "1234"}

# ---------- Offline News-Daten ----------
NEWS_DB = {
    "Powi": [
        {"title": f"Powi-News {i+1}", "desc": f"Beschreibung für Powi-News {i+1}. Schülerinnen und Schüler diskutieren aktuelle Themen.", 
         "date": f"2025-11-{i+1:02d}", "importance": (i%5)+1} for i in range(10)
    ],
    "Wirtschaft": [
        {"title": f"Wirtschaft-News {i+1}", "desc": f"Beschreibung für Wirtschaft-News {i+1}. Wirtschaftliche Entwicklungen werden analysiert.", 
         "date": f"2025-10-{i+1:02d}", "importance": (i%5)+1} for i in range(10)
    ],
    "Politik": [
        {"title": f"Politik-News {i+1}", "desc": f"Beschreibung für Politik-News {i+1}. Politische Entscheidungen werden diskutiert.", 
         "date": f"2025-09-{i+1:02d}", "importance": (i%5)+1} for i in range(10)
    ],
    "Sport": [
        {"title": f"Sport-News {i+1}", "desc": f"Beschreibung für Sport-News {i+1}. Aktuelle Ereignisse im Sport.", 
         "date": f"2025-08-{i+1:02d}", "importance": (i%5)+1} for i in range(10)
    ],
    "Technologie": [
        {"title": f"Technologie-News {i+1}", "desc": f"Beschreibung für Technologie-News {i+1}. Neue technologische Entwicklungen.", 
         "date": f"2025-07-{i+1:02d}", "importance": (i%5)+1} for i in range(10)
    ],
    "Weltweit": [
        {"title": f"Weltweit-News {i+1}", "desc": f"Beschreibung für Weltweit-News {i+1}. Globale Ereignisse.", 
         "date": f"2025-06-{i+1:02d}", "importance": (i%5)+1} for i in range(10)
    ],
    "Allgemein": [
        {"title": f"Allgemein-News {i+1}", "desc": f"Beschreibung für Allgemein-News {i+1}. Verschiedene Themen.", 
         "date": f"2025-05-{i+1:02d}", "importance": (i%5)+1} for i in range(10)
    ]
}

CATEGORIES = list(NEWS_DB.keys())

# ---------- Sentiment-Analyse ----------
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
st.title("🌐 Lumina News - Offline Edition")

# ---------- Login / Registrierung ----------
if not st.session_state.logged_in:
    st.subheader("🔐 Login")
    with st.form("login_form"):
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        submitted = st.form_submit_button("Einloggen")
        if submitted:
            if USERS.get(username) == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Willkommen, {username}!")
            else:
                st.error("Falsche Zugangsdaten!")

# ---------- Hauptseite ----------
if st.session_state.logged_in:
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.title("🗂️ Kategorien")
    pages = CATEGORIES + ["Analyse Gesamt"]
    choice = st.sidebar.radio("Wähle Kategorie:", pages)

    if choice != "Analyse Gesamt":
        st.header(f"📰 {choice}")
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

    else:
        st.header("📊 Gesamtanalyse")
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
        st.info("✨ Zusammenfassung: Lumina News zeigt insgesamt ein ausgewogenes Nachrichtenbild mit leichten positiven Tendenzen.")
