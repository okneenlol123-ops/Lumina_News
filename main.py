# -*- coding: utf-8 -*-
"""
Lumina News v4.0 - Streamlit mit Kategorien & KI-Analyse für echte News
"""
import streamlit as st
import requests, json, os, re
from datetime import datetime
from collections import Counter

# ----------------------------
# File paths
# ----------------------------
CACHE_FILE = "news_cache.json"
SETTINGS_FILE = "settings.json"
USERS_FILE = "users.json"
FAV_FILE = "favorites.json"

# ----------------------------
# JSON Helpers
# ----------------------------
def safe_load(path, default):
    try:
        if os.path.exists(path):
            with open(path,"r",encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return default

def safe_save(path, data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
    except:
        st.error(f"Fehler beim Speichern: {path}")

# ----------------------------
# Initialize files
# ----------------------------
if not os.path.exists(CACHE_FILE):
    safe_save(CACHE_FILE, {"articles": [], "last_update": ""})

if not os.path.exists(SETTINGS_FILE):
    safe_save(SETTINGS_FILE, {"theme":"light","home_count_each":2})

if not os.path.exists(USERS_FILE):
    safe_save(USERS_FILE, {"admin":"1234"})

if not os.path.exists(FAV_FILE):
    safe_save(FAV_FILE, {})

CACHE = safe_load(CACHE_FILE, {"articles": [], "last_update": ""})
SETTINGS = safe_load(SETTINGS_FILE, {"theme":"light","home_count_each":2})
USERS = safe_load(USERS_FILE, {"admin":"1234"})
FAVORITES = safe_load(FAV_FILE, {})

# ----------------------------
# Text/KI Utilities
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei","hat","haben","wird","werden","nicht","oder","aber"])

def tokenize(text):
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t)>2]

def extractive_summary(text, max_sentences=2):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    freq = Counter(tokenize(text))
    scored = [(sum(freq.get(w,0) for w in tokenize(s)), s) for s in sentences]
    scored.sort(key=lambda x: x[0], reverse=True)
    chosen = [s for _, s in scored[:max_sentences]]
    return " ".join(chosen)

def sentiment_score(text):
    pos_words = ["erfolgreich","gewinnt","stark","besser","stabil","positiv","lob","begeistert","sieg","förder"]
    neg_words = ["krise","verlust","scheit","problem","kritik","sorgen","unsicher","verzöger","einbruch","attack"]
    t = text.lower()
    pos = sum(t.count(w) for w in pos_words)
    neg = sum(t.count(w) for w in neg_words)
    if pos+neg==0: return 0.0
    return round((pos-neg)/(pos+neg),3)

def classify_sentiment_label(score):
    if score>0.2: return "Positiv"
    if score<-0.2: return "Negativ"
    return "Neutral"

def headline_score(article):
    base = 3*15  # default importance
    s = sentiment_score(article.get("title","")+" "+article.get("description",""))
    base += s*10
    l = len(tokenize(article.get("title","")))
    base += max(0,8-abs(l-10))
    return int(max(0,min(100,base)))

# ----------------------------
# Favorites
# ----------------------------
def add_favorite(user,aid):
    favs = FAVORITES.get(user, [])
    if aid not in favs: favs.append(aid)
    FAVORITES[user] = favs
    safe_save(FAV_FILE, FAVORITES)

def remove_favorite(user,aid):
    favs = FAVORITES.get(user, [])
    if aid in favs: favs.remove(aid)
    FAVORITES[user] = favs
    safe_save(FAV_FILE, FAVORITES)

def user_favorites(user):
    return FAVORITES.get(user, [])

# ----------------------------
# NewsAPI Fetch
# ----------------------------
API_KEY = st.secrets["newsapi"]["api_key"]

CATEGORIES = ["Politics","Business","Technology","Sports","World","Health","Science"]

def fetch_news():
    # Build request for multiple categories
    articles=[]
    for cat in CATEGORIES:
        url = f"https://newsapi.org/v2/top-headlines?category={cat.lower()}&pageSize=10&apiKey={API_KEY}&language=en"
        try:
            r = requests.get(url,timeout=10)
            data = r.json()
            if data.get("status")=="ok" and "articles" in data:
                for a in data["articles"]:
                    articles.append({
                        "id": a.get("url"),
                        "title": a.get("title"),
                        "description": a.get("description") or "",
                        "source": a.get("source",{}).get("name",""),
                        "date": a.get("publishedAt","")[:10],
                        "category": cat
                    })
        except:
            st.warning(f"API für {cat} konnte nicht geladen werden")
    CACHE["articles"] = articles
    CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_save(CACHE_FILE, CACHE)
    return articles

def get_news(force_update=False):
    # Update 2x täglich
    if force_update or not CACHE.get("articles") or CACHE.get("last_update")=="":
        return fetch_news()
    return CACHE.get("articles",[])

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v4.0", layout="wide")
if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=SETTINGS.get("theme","light")

# Theme CSS
LIGHT_CSS="""
body{background:#f7f9fc;color:#0b1a2b;}
.card{background:white;padding:12px;margin-bottom:12px;border-radius:8px;}
.header{color:#004aad;}
.small{font-size:12px;color:#666;}
"""
DARK_CSS="""
body{background:#0b1220;color:#e6eef8;}
.card{background:#0f1724;padding:12px;margin-bottom:12px;border-radius:8px;}
.header{color:#66b2ff;}
.small{font-size:12px;color:#9fb7d9;}
"""
def inject_css():
    css = LIGHT_CSS if st.session_state.theme=="light" else DARK_CSS
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)
inject_css()

# Topbar
col1,col2=st.columns([3,1])
with col1: st.markdown("<h1 class='header'>🌐 Lumina News v4.0</h1>",unsafe_allow_html=True)
with col2:
    theme_choice = st.selectbox("Theme",["light","dark"], index=0 if st.session_state.theme=="light" else 1)
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        SETTINGS["theme"] = theme_choice
        safe_save(SETTINGS_FILE, SETTINGS)
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
                if USERS.get(uname)==pwd:
                    st.session_state.logged_in=True
                    st.session_state.username=uname
                    st.success(f"Willkommen {uname}!")
                else: st.error("Falsche Zugangsdaten")
    with rcol:
        st.subheader("🆕 Registrierung")
        with st.form("reg_form"):
            r_uname = st.text_input("Neuer Benutzername", key="reg_user")
            r_pwd = st.text_input("Neues Passwort", type="password", key="reg_pass")
            reg_submit = st.form_submit_button("Registrieren")
            if reg_submit:
                if not r_uname or not r_pwd: st.warning("Bitte Name & Passwort")
                elif r_uname in USERS: st.warning("Benutzer existiert bereits")
                else:
                    USERS[r_uname]=r_pwd
                    safe_save(USERS_FILE, USERS)
                    st.success("Registrierung erfolgreich! Bitte anmelden")
    st.stop()

username = st.session_state.username

# Sidebar Navigation & Kategorien
st.sidebar.title(f"👤 {username}")
page = st.sidebar.radio("Navigation",["🏠 Home","⭐ Favoriten","⚙️ Einstellungen"])
selected_cat = st.sidebar.selectbox("Kategorie wählen", ["Alle"] + CATEGORIES)

# Load news
NEWS = get_news()

# Render news card
def render_card(article):
    aid = article.get("id")
    st.markdown(f"<div class='card'>",unsafe_allow_html=True)
    st.markdown(f"**{article.get('title')}**  <span class='small'>{article.get('date')}</span>")
    st.markdown(f"<div>{extractive_summary(article.get('description',''))}</div>",unsafe_allow_html=True)
    sscore = sentiment_score(article.get('description',''))
    st.markdown(f"<span class='small'>Sentiment: {classify_sentiment_label(sscore)}</span>")
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
    st.header("🏠 Home — Neueste News")
    displayed = [a for a in NEWS if selected_cat=="Alle" or a.get("category")==selected_cat]
    if not displayed: st.warning("Keine News verfügbar")
    for art in displayed[:SETTINGS.get("home_count_each",5)]:
        render_card(art)

elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs = user_favorites(username)
    displayed = [a for a in NEWS if a.get("id") in favs]
    if not displayed: st.info("Keine Favoriten")
    for art in displayed:
        render_card(art)

elif page=="⚙️ Einstellungen":
    st.header("⚙️ Einstellungen")
    st.write(f"Letztes API-Update: {CACHE.get('last_update','Nie')}")
    home_count = st.number_input("Anzahl Top-News Home",1,10,value=SETTINGS.get("home_count_each",2))
    if st.button("Speichern"):
        SETTINGS["home_count_each"]=home_count
        safe_save(SETTINGS_FILE, SETTINGS)
        st.success("Gespeichert")
