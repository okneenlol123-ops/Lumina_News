# -*- coding: utf-8 -*-
import streamlit as st
import requests, json, re
from datetime import datetime
from collections import Counter

# ----------------------------
# Basis-Setup
# ----------------------------
API_KEY = "64457577c9a14eb9a846b69dcae0d659"Backup 6 news gut

# -*- coding: utf-8 -*-
import streamlit as st
import requests, json, re
from datetime import datetime

API_KEY = "64457577c9a14eb9a846b69dcae0d659"
CATEGORIES = ["business", "technology", "sports", "politics", "world", "health", "science"]

CACHE_FILE = "news_cache.json"
FAV_FILE = "favorites.json"
USER_FILE = "users.json"

# ----------------------------
# Laden/Speichern Cache
# ----------------------------
def load_json(file, default={}):
    try:
        with open(file,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(file, data):
    try:
        with open(file,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False, indent=2)
    except:
        st.warning(f"{file} konnte nicht gespeichert werden.")

CACHE = load_json(CACHE_FILE, {"articles": {}, "last_update": ""})
FAVORITES = load_json(FAV_FILE, {})
USERS = load_json(USER_FILE, {"admin":"1234"})

# ----------------------------
# Spracheinstellungen (default Englisch)
# ----------------------------
if "language" not in st.session_state:
    st.session_state.language = "en"

# ----------------------------
# Zusammenfassung 7 Sätze, Sprache wählbar
# ----------------------------
SENTENCE_RE = re.compile(r'(?<=[.!?]) +')

def summarize_long(text, content="", language="en", max_sentences=7):
    if not text:
        text = content or "No description available."
    else:
        text += " " + (content or "")
    sentences = SENTENCE_RE.split(text)
    summary = " ".join(sentences[:max_sentences])
    if language=="de":
        # einfache Übersetzung (offline, Platzhalter)
        summary = fake_translate_de(summary)
    return summary

def fake_translate_de(text):
    # Placeholder Übersetzung: für Demo, nur text zurückgeben
    # Kann später durch echte Übersetzungs-API ersetzt werden
    return text  # TODO: Hier echte Übersetzung einbauen

# ----------------------------
# NewsAPI laden
# ----------------------------
def fetch_news(category):
    url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&pageSize=10&apiKey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("status")=="ok":
            articles=[]
            for a in data.get("articles",[]):
                articles.append({
                    "title": a.get("title",""),
                    "desc": a.get("description","") or "",
                    "content": a.get("content","") or "",
                    "date": a.get("publishedAt","")[:10],
                    "url": a.get("url","")
                })
            CACHE["articles"][category] = articles
            CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json(CACHE_FILE, CACHE)
            return articles
    except:
        st.warning("API konnte nicht geladen werden. Zeige letzte gespeicherte News.")
    return CACHE.get("articles",{}).get(category, [])

# ----------------------------
# Favoriten
# ----------------------------
def add_favorite(article):
    aid = article["url"]
    if aid not in FAVORITES:
        FAVORITES[aid] = article
        save_json(FAV_FILE, FAVORITES)
        st.success("Zur Favoritenliste hinzugefügt!")

def remove_favorite(article):
    aid = article["url"]
    if aid in FAVORITES:
        del FAVORITES[aid]
        save_json(FAV_FILE, FAVORITES)
        st.info("Aus Favoriten entfernt!")

# ----------------------------
# News Card
# ----------------------------
def render_card(article, show_fav=True):
    st.markdown(f"### [{article['title']}]({article['url']})")
    desc_text = summarize_long(article.get("desc",""), content=article.get("content",""), language=st.session_state.language)
    st.markdown(desc_text)
    if show_fav:
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("★ Favorit", key=f"fav-{article['url']}"):
                add_favorite(article)
                st.experimental_rerun()
        with col2:
            if st.button("✖ Entfernen", key=f"unfav-{article['url']}"):
                remove_favorite(article)
                st.experimental_rerun()
    st.markdown("---")

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v7.0", layout="wide")
st.title("🌐 Lumina News v7.0")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Gehe zu:", ["🏠 Home", "📚 Kategorien", "⭐ Favoriten", "⚙️ Profil / Einstellungen"])

# Home
if page=="🏠 Home":
    st.header("🏠 Home — Eine News pro Kategorie")
    for i in range(0,len(CATEGORIES),2):
        cols = st.columns(2)
        for j, cat in enumerate(CATEGORIES[i:i+2]):
            with cols[j]:
                st.subheader(cat.capitalize())
                news_list = fetch_news(cat)
                if news_list:
                    render_card(news_list[0], show_fav=True)
                else:
                    st.write("Keine News verfügbar.")

# Kategorien
elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    selected_cat = st.selectbox("Kategorie wählen:", CATEGORIES)
    news_list = fetch_news(selected_cat)
    if news_list:
        for article in news_list:
            render_card(article)
    else:
        st.write("Keine News verfügbar.")

# Favoriten
elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    if FAVORITES:
        for aid, article in FAVORITES.items():
            render_card(article, show_fav=True)
    else:
        st.info("Keine Favoriten. Klicke auf ★ bei einer News, um sie hier zu speichern.")

# Profil / Einstellungen
elif page=="⚙️ Profil / Einstellungen":
    st.header("⚙️ Profil / Einstellungen")
    st.subheader("Benutzerinformationen")
    st.text(f"Benutzername: admin")  # TODO: Login-System einbauen
    st.text_input("Passwort ändern:", type="password")
    
    st.subheader("Sprache der Zusammenfassungen")
    lang_choice = st.selectbox("Sprache wählen:", ["Englisch", "Deutsch"])
    lang_code = "en" if lang_choice=="Englisch" else "de"
    if lang_code != st.session_state.language:
        st.session_state.language = lang_code
        st.success(f"Sprache auf {lang_choice} gesetzt!")

st.markdown(f"*Letztes Update: {CACHE.get('last_update','Nie')}*")
CATEGORIES = ["business", "technology", "sports", "politics", "world", "health", "science"]

CACHE_FILE = "news_cache.json"
FAV_FILE = "favorites.json"
USER_FILE = "users.json"

# ----------------------------
# Hilfsfunktionen für JSON
# ----------------------------
def load_json(file, default=None):
    if default is None:
        default = {}
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

SENTENCE_RE = re.compile(r'(?<=[.!?]) +')

def fake_translate_de(text):
    return text  # Platzhalter, kann später durch echte Übersetzung ersetzt werden

def summarize_long(text, content="", language="en", max_sentences=7):
    if not text:
        text = content or "No description available."
    else:
        text += " " + (content or "")
    sentences = SENTENCE_RE.split(text)
    summary = " ".join(sentences[:max_sentences])
    if language == "de":
        summary = fake_translate_de(summary)
    return summary

# ----------------------------
# News laden
# ----------------------------
def fetch_news(category):
    url = f"https://newsapi.org/v2/everything?q={category}&language=en&pageSize=10&sortBy=publishedAt&apiKey={API_KEY}"
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
                    "url": a.get("url", "")
                })
            CACHE["articles"][category] = articles
            CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json(CACHE_FILE, CACHE)
            return articles
    except Exception:
        st.warning("⚠️ API konnte nicht geladen werden. Zeige gespeicherte News.")
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
    st.markdown("---")

# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="Lumina News v7.1", layout="wide")
st.title("🌐 Lumina News v7.1")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Gehe zu:",
    ["🏠 Home", "📚 Kategorien", "⭐ Favoriten", "⚙️ Profil / Einstellungen"]
)

# ----------------------------
# Seiten: Home / Kategorien / Favoriten / Profil
# ----------------------------
if page == "🏠 Home":
    st.header("🏠 Home — Eine News pro Kategorie")
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
        st.write("Keine News verfügbar.")

elif page == "⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    if FAVORITES:
        for article in FAVORITES.values():
            render_card(article)
    else:
        st.info("Keine Favoriten gespeichert.")

elif page == "⚙️ Profil / Einstellungen":
    st.header("⚙️ Profil / Einstellungen")
    st.subheader("Benutzerinformationen")
    st.text("Benutzername: admin")
    new_pw = st.text_input("Passwort ändern:", type="password")
    if st.button("Passwort speichern"):
        USERS["admin"] = new_pw or USERS["admin"]
        save_json(USER_FILE, USERS)
        st.success("🔐 Passwort geändert!")

    st.markdown("---")
    st.subheader("🌍 Sprache der Zusammenfassungen")
    lang_choice = st.selectbox("Sprache wählen:", ["Englisch", "Deutsch"])
    lang_code = "en" if lang_choice == "Englisch" else "de"
    st.session_state.language = lang_code
    st.success(f"✅ Sprache auf {lang_choice} gesetzt!")

# ----------------------------
# Analyse & Tools unten
# ----------------------------
st.markdown("---")
st.subheader("🧠 KI-News-Analyse")

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
    for word, count in freq:
        st.write(f"• {word.capitalize()} ({count}x)")

analyse_news()

st.markdown("---")
st.subheader("🔄 Manuelles Update aller Kategorien")
if st.button("Jetzt News neu laden"):
    all_articles = {}
    for cat in CATEGORIES:
        st.write(f"⏳ Lade Kategorie **{cat}** ...")
        all_articles[cat] = fetch_news(cat)
    CACHE["articles"] = all_articles
    CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_json(CACHE_FILE, CACHE)
    st.success("✅ Alle Kategorien aktualisiert!")

st.caption(f"🕒 Letztes Update: {CACHE.get('last_update', 'Nie')}")
