# -*- coding: utf-8 -*-
"""
Lumina News v3.0 - Streamlit Edition mit Echt-News & Offline-Fallback
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
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei","hat","haben","wird","werden","nicht","oder","aber"])

def tokenize(text):
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t)>2]

def extractive_summary(text,max_sentences=2):
    sentences = re.split(r'(?<=[.!?])\s+',text.strip())
    tokens = tokenize(text)
    freq = Counter(tokens)
    scored = [(sum(freq.get(w,0) for w in tokenize(s)),s) for s in sentences]
    scored.sort(key=lambda x:x[0],reverse=True)
    chosen = [s for _,s in scored[:max_sentences]]
    return " ".join(chosen)

def sentiment_score(text):
    pos_words = ["erfolgreich","gewinnt","stark","besser","stabil","positiv","lob","begeistert","sieg","förder"]
    neg_words = ["krise","verlust","scheit","problem","kritik","sorgen","unsicher","verzöger","einbruch","attack"]
    text_l = text.lower()
    pos = sum(text_l.count(w) for w in pos_words)
    neg = sum(text_l.count(w) for w in neg_words)
    if pos+neg==0: return 0.0
    return round((pos-neg)/(pos+neg),3)

def classify_sentiment_label(score):
    if score>0.2: return "Positiv"
    if score<-0.2: return "Negativ"
    return "Neutral"

def headline_score(article):
    base = article.get("importance",3)*15
    s = sentiment_score(article.get("title","")+article.get("description",""))
    base += s*10
    l = len(tokenize(article.get("title","")))
    base += max(0,8-abs(l-10))
    return int(max(0,min(100,base)))

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
API_KEY = st.secrets["newsapi"]["api_key"]
def fetch_news():
    url=f"https://newsapi.org/v2/everything?q=politics OR business OR sports OR technology OR world&language=en&pageSize=20&apiKey={API_KEY}"
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
                    "source":a.get("source",{}).get("name",""),
                    "date":a.get("publishedAt","")[:10],
                    "importance":3
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
st.set_page_config(page_title="Lumina News v3.0",layout="wide")

if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=SETTINGS.get("theme","light")
if "last_read" not in st.session_state: st.session_state.last_read=[]

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
with col1: st.markdown("<h1 class='header'>🌐 Lumina News v3.0</h1>",unsafe_allow_html=True)
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
page = st.sidebar.radio("Navigation",["🏠 Home","⭐ Favoriten","⚙️ Einstellungen"])

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
    if not NEWS:
        st.warning("Keine News verfügbar")
    for art in NEWS[:10]:
        render_card(art)

elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs = user_favorites(username)
    if not favs: st.info("Keine Favoriten")
    for aid in favs:
        art = next((a for a in NEWS if a.get("id")==aid),None)
        if art: render_card(art)

elif page=="⚙️ Einstellungen":
    st.header("⚙️ Einstellungen")
    st.write(f"Letztes API-Update: {CACHE.get('last_update','Nie')}")
    home_count = st.number_input("Anzahl Top-News Home",1,10,value=SETTINGS.get("home_count_each",2))
    if st.button("Speichern"):
        SETTINGS["home_count_each"]=home_count
        safe_save(SETTINGS_FILE,SETTINGS)
        st.success("Gespeichert")
