# -*- coding: utf-8 -*-
import streamlit as st
import requests, json, re, io
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
from deep_translator import GoogleTranslator

# ----------------------------
# Basis-Setup
# ----------------------------
API_KEY = "64457577c9a14eb9a846b69dcae0d659"
CATEGORIES = ["business", "technology", "sports", "politics", "world", "health", "science"]
COUNTRIES = {
    "🇺🇸 USA": "us",
    "🇩🇪 Deutschland": "de",
    "🇬🇧 Großbritannien": "gb",
    "🇫🇷 Frankreich": "fr",
    "🇮🇹 Italien": "it",
    "🇪🇸 Spanien": "es"
}

CACHE_FILE = "news_cache.json"
FAV_FILE = "favorites.json"
USER_FILE = "users.json"

# ----------------------------
# JSON-Helper
# ----------------------------
def load_json(file, default=None):
    if default is None: default = {}
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(file, data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        st.warning(f"{file} konnte nicht gespeichert werden.")

CACHE = load_json(CACHE_FILE, {"articles": {}, "last_update": ""})
FAVORITES = load_json(FAV_FILE, {})
USERS = load_json(USER_FILE, {"admin": "1234"})

# ----------------------------
# Spracheinstellung
# ----------------------------
if "language" not in st.session_state:
    st.session_state.language = "en"

if "country" not in st.session_state:
    st.session_state.country = "us"

SENTENCE_RE = re.compile(r'(?<=[.!?]) +')

def translate_text(text, lang):
    """Automatische Übersetzung"""
    if not text.strip():
        return text
    try:
        if lang == "de":
            return GoogleTranslator(source="en", target="de").translate(text)
        return text
    except Exception:
        return text

def summarize_long(text, content="", language="en", max_sentences=7):
    """Erstellt eine kurze Zusammenfassung"""
    if not text:
        text = content or "No description available."
    else:
        text += " " + (content or "")
    sentences = SENTENCE_RE.split(text)
    summary = " ".join(sentences[:max_sentences])
    return translate_text(summary, language)

# ----------------------------
# News abrufen mit Länderfilter & Suche
# ----------------------------
def fetch_news(category=None, query=None):
    base_url = "https://newsapi.org/v2/"
    lang = "en"

    if query:  # Suchmodus
        url = f"{base_url}everything?q={query}&language={lang}&pageSize=10&sortBy=publishedAt&apiKey={API_KEY}"
    else:  # Kategorie + Land
        url = f"{base_url}top-headlines?country={st.session_state.country}&category={category}&language={lang}&pageSize=10&apiKey={API_KEY}"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("status") == "ok":
            articles = []
            for a in data.get("articles", []):
                articles.append({
                    "title": a.get("title", ""),
                    "desc": a.get("description", "") or "",
                    "content": a.get("content", "") or "",
                    "date": a.get("publishedAt", "")[:10],
                    "url": a.get("url", ""),
                    "category": category or "search"
                })
            if not query:
                CACHE["articles"][category] = articles
                CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_json(CACHE_FILE, CACHE)
            return articles
    except Exception:
        st.warning("⚠️ API konnte nicht geladen werden.")
    return CACHE.get("articles", {}).get(category, [])

# ----------------------------
# Favoriten-System
# ----------------------------
def add_favorite(article):
    aid = article["url"]
    if aid not in FAVORITES:
        FAVORITES[aid] = article
        save_json(FAV_FILE, FAVORITES)
        st.success("✅ Zur Favoritenliste hinzugefügt!")

def remove_favorite(article):
    aid = article["url"]
    if aid in FAVORITES:
        del FAVORITES[aid]
        save_json(FAV_FILE, FAVORITES)
        st.info("❌ Aus Favoriten entfernt!")

# ----------------------------
# Automatisches Update 6:00 / 20:00 Uhr
# ----------------------------
def auto_update():
    now = datetime.now()
    last = CACHE.get("last_update", "")
    last_date = last[:10] if last else ""
    hour = now.hour
    if (hour in [6, 20]) and (last_date != now.strftime("%Y-%m-%d")):
        all_articles = {}
        for cat in CATEGORIES:
            all_articles[cat] = fetch_news(cat)
        CACHE["articles"] = all_articles
        CACHE["last_update"] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_json(CACHE_FILE, CACHE)
        st.success("🕒 Automatisches Update durchgeführt.")

auto_update()

# ----------------------------
# Darstellung einzelner News
# ----------------------------
def render_card(article, show_fav=True):
    st.markdown(f"### [{article['title']}]({article['url']})")
    desc_text = summarize_long(
        article.get("desc", ""),
        content=article.get("content", ""),
        language=st.session_state.language
    )
    st.markdown(desc_text)
    if show_fav:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("★ Favorit", key=f"fav-{article['url']}"):
                add_favorite(article)
        with col2:
            if st.button("✖ Entfernen", key=f"unfav-{article['url']}"):
                remove_favorite(article)
    st.caption(f"📅 {article.get('date', 'Unbekannt')} | 🗂 {article.get('category', '-')}")
    st.markdown("---")

# ----------------------------
# UI Layout
# ----------------------------
st.set_page_config(page_title="Lumina News v8", layout="wide")
st.title("📰 Lumina News v8")

# Sidebar
st.sidebar.title("⚙️ Navigation")
page = st.sidebar.radio("Gehe zu:", ["🏠 Home", "📚 Kategorien", "🔎 Suche", "⭐ Favoriten", "👤 Profil"])

# Länderfilter
st.sidebar.subheader("🌍 Land wählen")
country_choice = st.sidebar.selectbox("Land:", list(COUNTRIES.keys()))
st.session_state.country = COUNTRIES[country_choice]

# ----------------------------
# Seitenlogik
# ----------------------------
if page == "🏠 Home":
    st.header(f"🏠 Neueste News ({country_choice})")
    for i in range(0, len(CATEGORIES), 2):
        cols = st.columns(2)
        for j, cat in enumerate(CATEGORIES[i:i + 2]):
            with cols[j]:
                st.subheader(cat.capitalize())
                news_list = fetch_news(cat)
                if news_list:
                    render_card(news_list[0], show_fav=True)
                else:
                    st.write("Keine News verfügbar.")

elif page == "📚 Kategorien":
    st.header("📚 Kategorien")
    selected_cat = st.selectbox("Kategorie wählen:", CATEGORIES)
    news_list = fetch_news(selected_cat)
    if news_list:
        for article in news_list:
            render_card(article)
    else:
        st.info("Keine News verfügbar.")

elif page == "🔎 Suche":
    st.header("🔍 Suche in allen News")
    query = st.text_input("Suchbegriff eingeben:")
    if query:
        news_list = fetch_news(query=query)
        if news_list:
            for article in news_list:
                render_card(article)
        else:
            st.warning("Keine Ergebnisse gefunden.")

elif page == "⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    if FAVORITES:
        sort_by = st.selectbox("Sortieren nach:", ["Titel", "Datum", "Kategorie"])
        favs = list(FAVORITES.values())
        if sort_by == "Titel":
            favs = sorted(favs, key=lambda x: x["title"])
        elif sort_by == "Datum":
            favs = sorted(favs, key=lambda x: x["date"], reverse=True)
        elif sort_by == "Kategorie":
            favs = sorted(favs, key=lambda x: x["category"])
        for article in favs:
            render_card(article)

        # Export als CSV
        if st.button("📤 Favoriten exportieren als CSV"):
            import pandas as pd
            df = pd.DataFrame(favs)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv, "favorites.csv", "text/csv")
    else:
        st.info("Keine Favoriten gespeichert.")

elif page == "👤 Profil":
    st.header("👤 Profil / Einstellungen")
    st.text("Benutzername: admin")
    new_pw = st.text_input("Neues Passwort:", type="password")
    if st.button("Passwort speichern"):
        USERS["admin"] = new_pw or USERS["admin"]
        save_json(USER_FILE, USERS)
        st.success("🔐 Passwort geändert!")

    st.markdown("---")
    st.subheader("🈳 Sprache der Zusammenfassungen")
    lang_choice = st.selectbox("Sprache wählen:", ["Englisch", "Deutsch"])
    st.session_state.language = "en" if lang_choice == "Englisch" else "de"
    st.success(f"✅ Sprache auf {lang_choice} gesetzt!")

# ----------------------------
# Trendanalyse unten
# ----------------------------
st.markdown("---")
st.subheader("📊 Trend-Analyse")

def analyse_news():
    all_text = ""
    for arts in CACHE.get("articles", {}).values():
        for art in arts:
            all_text += " " + art.get("title", "") + " " + art.get("desc", "")
    words = re.findall(r"[A-Za-zÄÖÜäöüß]+", all_text.lower())
    stopwords = {"und","der","die","das","mit","ein","eine","für","auf","von","the","and","in","to","is","are"}
    words = [w for w in words if w not in stopwords and len(w) > 3]
    freq = Counter(words).most_common(10)
    if not freq:
        st.info("Noch keine Trenddaten verfügbar.")
        return
    st.write("**Top 10 Begriffe in aktuellen News:**")

    labels, values = zip(*freq)
    plt.figure(figsize=(8, 4))
    plt.barh(labels, values)
    plt.xlabel("Vorkommen")
    plt.ylabel("Begriff")
    plt.title("Häufigste Begriffe")
    st.pyplot(plt)

analyse_news()

st.caption(f"🕒 Letztes Update: {CACHE.get('last_update', 'Nie')} | Land: {country_choice.upper()}")
