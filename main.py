# -*- coding: utf-8 -*-
"""
Lumina News v4.0 - Streamlit Edition mit API-News, längeren Zusammenfassungen & Sprachwahl
"""
import streamlit as st
import json, os, requests, re
from collections import Counter
from datetime import datetime

# ----------------------------
# File paths
# ----------------------------
USERS_FILE = "users.json"
FAV_FILE = "favorites.json"
SETTINGS_FILE = "settings.json"
CACHE_FILE = "news_cache.json"

# ----------------------------
# Safe JSON helpers
# ----------------------------
def safe_load(path, default):
    try:
        if os.path.exists(path):
            with open(path,"r",encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return default

def safe_save(path,data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
    except:
        st.error(f"Fehler beim Speichern von {path}")

# ----------------------------
# Initialize persistent files if missing
# ----------------------------
if not os.path.exists(USERS_FILE):
    safe_save(USERS_FILE, {"admin":"1234"})
if not os.path.exists(FAV_FILE):
    safe_save(FAV_FILE,{})
if not os.path.exists(SETTINGS_FILE):
    safe_save(SETTINGS_FILE, {"theme":"light","home_count_each":1,"language":"en"})
if not os.path.exists(CACHE_FILE):
    safe_save(CACHE_FILE, {"articles":[],"last_update":""})

USERS = safe_load(USERS_FILE, {"admin":"1234"})
FAVORITES = safe_load(FAV_FILE,{})
SETTINGS = safe_load(SETTINGS_FILE, {"theme":"light","home_count_each":1,"language":"en"})
CACHE = safe_load(CACHE_FILE, {"articles":[],"last_update":""})

# ----------------------------
# Session-state defaults
# ----------------------------
if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=SETTINGS.get("theme","light")
if "last_read" not in st.session_state: st.session_state.last_read=[]
if "language" not in st.session_state: st.session_state.language=SETTINGS.get("language","en")

# ----------------------------
# Text processing helpers
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei","hat","haben","wird","werden","nicht","oder","aber"])

def tokenize(text):
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t)>2]

def extractive_summary(text, max_sentences=7):
    # längere Zusammenfassungen
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences: return ""
    tokens = tokenize(text)
    freq = Counter(tokens)
    scored = [(sum(freq.get(w,0) for w in tokenize(s)), s) for s in sentences]
    scored.sort(key=lambda x:x[0], reverse=True)
    chosen = [s for _,s in scored[:max_sentences]]
    return " ".join(chosen)

# ----------------------------
# Favorites
# ----------------------------
def add_favorite(user,aid):
    favs = FAVORITES.get(user,[])
    if aid not in favs: favs.append(aid)
    FAVORITES[user]=favs
    safe_save(FAV_FILE,FAVORITES)

def remove_favorite(user,aid):
    favs = FAVORITES.get(user,[])
    if aid in favs: favs.remove(aid)
    FAVORITES[user]=favs
    safe_save(FAV_FILE,FAVORITES)

def user_favorites(user):
    return FAVORITES.get(user,[])

# ----------------------------
# News fetching
# ----------------------------
API_KEY = "64457577c9a14eb9a846b69dcae0d659"
def fetch_news():
    url=f"https://newsapi.org/v2/top-headlines?language=en&pageSize=20&apiKey={API_KEY}"
    try:
        r = requests.get(url,timeout=10)
        data = r.json()
        if data.get("status")=="ok" and "articles" in data:
            articles=[]
            for a in data["articles"]:
                articles.append({
                    "id":a.get("url"),
                    "title":a.get("title"),
                    "description":a.get("description") or "",
                    "content":a.get("content") or "",
                    "source":a.get("source",{}).get("name",""),
                    "date":a.get("publishedAt","")[:10],
                    "category":"Allgemein"
                })
            CACHE["articles"]=articles
            CACHE["last_update"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            safe_save(CACHE_FILE,CACHE)
            return articles
    except:
        st.warning("API konnte nicht geladen werden.")
    return CACHE.get("articles",[])

NEWS = fetch_news()

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v4.0",layout="wide")

# Theme CSS
LIGHT_CSS="""
body { background-color: #f7f9fc; color:#0b1a2b; }
.card { background:white; border-radius:8px;padding:12px;margin-bottom:12px; }
.header { color:#004aad; }
.small { color:#666;font-size:12px; }
"""
DARK_CSS="""
body { background-color:#0b1220; color:#e6eef8; }
.card { background:#0f1724;border-radius:8px;padding:12px;margin-bottom:12px; }
.header { color:#66b2ff; }
.small { color:#9fb7d9;font-size:12px; }
"""
def inject_css():
    css = LIGHT_CSS if st.session_state.theme=="light" else DARK_CSS
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)
inject_css()

# Topbar
col1,col2=st.columns([3,1])
with col1: st.markdown("<h1 class='header'>🌐 Lumina News v4.0</h1>",unsafe_allow_html=True)
with col2:
    theme_choice = st.selectbox("Theme",["light","dark"],index=0 if st.session_state.theme=="light" else 1)
    if theme_choice != st.session_state.theme:
        st.session_state.theme=theme_choice
        SETTINGS["theme"]=theme_choice
        safe_save(SETTINGS_FILE,SETTINGS)
        inject_css()

st.markdown("---")

# Login/Register
if not st.session_state.logged_in:
    lcol,rcol=st.columns(2)
    with lcol:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            uname = st.text_input("Benutzername", key="login_user")
            pwd = st.text_input("Passwort", type="password", key="login_pass")
            submit = st.form_submit_button("Einloggen")
            if submit:
                users = safe_load(USERS_FILE, {"admin":"1234"})
                if users.get(uname)==pwd:
                    st.session_state.logged_in=True
                    st.session_state.username=uname
                    st.success(f"Willkommen {uname}!")
                else:
                    st.error("Falsche Zugangsdaten")
    with rcol:
        st.subheader("🆕 Registrierung")
        with st.form("reg_form"):
            r_uname = st.text_input("Neuer Benutzername", key="reg_user")
            r_pwd = st.text_input("Neues Passwort", type="password", key="reg_pass")
            reg_submit = st.form_submit_button("Registrieren")
            if reg_submit:
                users = safe_load(USERS_FILE, {"admin":"1234"})
                if not r_uname or not r_pwd: st.warning("Bitte Name & Passwort")
                elif r_uname in users: st.warning("Benutzer existiert bereits")
                else:
                    users[r_uname]=r_pwd
                    safe_save(USERS_FILE,users)
                    st.success("Registrierung erfolgreich! Bitte anmelden")
    st.stop()

username = st.session_state.username

# Sidebar
st.sidebar.title(f"👤 {username}")
page = st.sidebar.radio("Navigation",["🏠 Home","📚 Kategorien","⭐ Favoriten","⚙️ Profil / Einstellungen"])

# Sprache wählen
st.sidebar.subheader("Sprache Zusammenfassungen")
lang_choice = st.sidebar.selectbox("Sprache",["Englisch","Deutsch"], index=0 if st.session_state.language=="en" else 1)
st.session_state.language = "en" if lang_choice=="Englisch" else "de"

# Hilfsfunktion: Render Card
def render_card(article):
    if st.session_state.language=="de":
        summary = extractive_summary(article.get("description","")+" "+article.get("content",""))
        # einfache Übersetzung mock (API oder deepl kann hier verwendet werden)
        summary = " ".join([s+" (DE)" for s in summary.split(".") if s])
    else:
        summary = extractive_summary(article.get("description","")+" "+article.get("content",""))
    st.markdown(f"<div class='card'>",unsafe_allow_html=True)
    st.markdown(f"**{article.get('title','')}** <span class='small'>{article.get('date')}</span>")
    st.markdown(summary)
    cols=st.columns([1,1])
    with cols[0]:
        if st.button("★ Favorit", key=f"fav-{article.get('id')}"):
            add_favorite(username,article.get("id"))
    with cols[1]:
        if st.button("✖ Entfernen", key=f"unfav-{article.get('id')}"):
            remove_favorite(username,article.get("id"))
    st.markdown("</div>",unsafe_allow_html=True)

# ---------- Page Logic ----------
if page=="🏠 Home":
    st.header("🏠 Home — Top News")
    # je 1 Artikel
    categories = list(set([a.get("category","Allgemein") for a in NEWS]))
    for cat in categories:
        cat_news = [a for a in NEWS if a.get("category")==cat]
        if cat_news:
            render_card(cat_news[0])

elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    cats = list(set([a.get("category","Allgemein") for a in NEWS]))
    sel_cat = st.selectbox("Kategorie wählen", cats)
    cat_articles = [a for a in NEWS if a.get("category")==sel_cat]
    for a in cat_articles:
        render_card(a)

elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs = user_favorites(username)
    if not favs: st.info("Keine Favoriten")
    else:
        for aid in favs:
            art = next((a for a in NEWS if a.get("id")==aid), None)
            if art: render_card(art)

elif page=="⚙️ Profil / Einstellungen":
    st.header("⚙️ Profil / Einstellungen")
    st.write(f"Benutzername: **{username}**")
    st.write(f"Passwort: **{USERS.get(username,'')}**")
