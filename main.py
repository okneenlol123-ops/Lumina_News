# -*- coding: utf-8 -*-
"""
Lumina News v4.0 - Streamlit Edition mit NewsAPI.org
Features:
 - Login / Registrierung (users.json)
 - Theme (light/dark)
 - Home mit Kategorien
 - News via NewsAPI.org
 - Headline + 10-Wort Zusammenfassung
 - Favoriten / Lesezeichen
"""
import streamlit as st
import json, os, requests, re
from datetime import datetime
from collections import Counter

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
# Initialize persistent files
# ----------------------------
if not os.path.exists(USERS_FILE):
    safe_save(USERS_FILE, {"admin":"1234"})
if not os.path.exists(FAV_FILE):
    safe_save(FAV_FILE,{})
if not os.path.exists(SETTINGS_FILE):
    safe_save(SETTINGS_FILE, {"theme":"light","home_count_each":2})
if not os.path.exists(CACHE_FILE):
    safe_save(CACHE_FILE, {"articles":[],"last_update":""})

USERS = safe_load(USERS_FILE, {"admin":"1234"})
FAVORITES = safe_load(FAV_FILE,{})
SETTINGS = safe_load(SETTINGS_FILE, {"theme":"light","home_count_each":2})
CACHE = safe_load(CACHE_FILE, {"articles":[],"last_update":""})

# ----------------------------
# Text utils
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
def summarize_10_words(text):
    tokens = text.split()
    return " ".join(tokens[:10]) + ("..." if len(tokens)>10 else "")

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
# News fetching (NewsAPI.org)
# ----------------------------
API_KEY = "64457577c9a14eb9a846b69dcae0d659"  # dein API-Key direkt eingefügt
CATEGORIES = ["business","technology","sports","world","politics","health","entertainment"]

def fetch_news():
    articles = []
    for cat in CATEGORIES:
        url=f"https://newsapi.org/v2/top-headlines?category={cat}&language=en&pageSize=10&apiKey={API_KEY}"
        try:
            r = requests.get(url,timeout=10)
            data = r.json()
            if data.get("status")=="ok":
                for a in data.get("articles",[]):
                    articles.append({
                        "id":a.get("url"),
                        "title":a.get("title",""),
                        "description":a.get("description") or "",
                        "category":cat,
                        "date":a.get("publishedAt","")[:10]
                    })
        except:
            st.warning(f"NewsAPI konnte Kategorie {cat} nicht laden")
    # update cache
    CACHE["articles"]=articles
    CACHE["last_update"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_save(CACHE_FILE,CACHE)
    return articles

# Use cached if recent
NEWS = CACHE.get("articles",[])
if not NEWS or (datetime.now() - datetime.strptime(CACHE.get("last_update","1970-01-01"), "%Y-%m-%d %H:%M:%S")).days >= 1:
    NEWS = fetch_news()

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v4.0",layout="wide")

if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=SETTINGS.get("theme","light")

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
page = st.sidebar.radio("Navigation",["🏠 Home","⭐ Favoriten"])

# Render news card
def render_card(article):
    aid = article.get("id")
    st.markdown(f"<div class='card'>",unsafe_allow_html=True)
    st.markdown(f"**{article.get('title','')}**")
    st.markdown(f"<div>{summarize_10_words(article.get('description',''))}</div>",unsafe_allow_html=True)
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("★ Favorit", key=f"fav-{aid}"):
            add_favorite(username,aid)
            st.success("Hinzugefügt")
    with cols[1]:
        if st.button("✖ Entfernen", key=f"unfav-{aid}"):
            remove_favorite(username,aid)
            st.info("Entfernt")
    st.markdown("</div>",unsafe_allow_html=True)

# Pages
if page=="🏠 Home":
    st.header("🏠 Home — Neueste News nach Kategorie")
    for cat in CATEGORIES:
        st.subheader(cat.capitalize())
        cat_news = [a for a in NEWS if a.get("category")==cat]
        for art in cat_news:
            render_card(art)

elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs = user_favorites(username)
    if not favs: st.info("Keine Favoriten")
    for aid in favs:
        art = next((a for a in NEWS if a.get("id")==aid),None)
        if art: render_card(art)
