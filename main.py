# -*- coding: utf-8 -*-
"""
Lumina News v3.0 - Streamlit Edition
Echte News, automatisches Caching, Offline-Analyzer
"""

import streamlit as st
import json, os, re, requests
from datetime import datetime
from collections import Counter

# ----------------------------
# Files
# ----------------------------
USERS_FILE = "users.json"
FAV_FILE = "favorites.json"
SETTINGS_FILE = "settings.json"
CACHE_FILE = "news_cache.json"

# ----------------------------
# Safe JSON helpers
# ----------------------------
def safe_load(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def safe_save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------
# Initialize files
# ----------------------------
if not os.path.exists(USERS_FILE):
    safe_save(USERS_FILE, {"admin":"1234"})
if not os.path.exists(FAV_FILE):
    safe_save(FAV_FILE, {})
if not os.path.exists(SETTINGS_FILE):
    safe_save(SETTINGS_FILE, {"theme":"light","home_count_each":2})

USERS = safe_load(USERS_FILE, {"admin":"1234"})
FAVORITES = safe_load(FAV_FILE, {})
GLOBAL_SETTINGS = safe_load(SETTINGS_FILE, {"theme":"light","home_count_each":2})

# ----------------------------
# Analyzer helpers
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+", flags=re.UNICODE)
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei","hat","haben","wird","werden","nicht","oder","aber","wir","ich","du","er","sie","es","dem","den","des"])

def tokenize(text):
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

def extractive_summary(text,max_sentences=2):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    tokens = tokenize(text)
    freq = Counter(tokens)
    scores = []
    for s in sentences:
        s_tokens = tokenize(s)
        score = sum(freq.get(w,0) for w in s_tokens)
        scores.append((score,s))
    scores.sort(key=lambda x:x[0],reverse=True)
    chosen = [s for _,s in scores[:max_sentences]]
    return " ".join(chosen)

def sentiment_score(text):
    pos_words = ["erfolgreich","gewinnt","stark","besser","stabil","positiv","lob","begeistert","sieg","förder"]
    neg_words = ["krise","verlust","scheit","problem","kritik","sorgen","unsicher","verzöger","einbruch","attack"]
    t=text.lower();p=0;n=0
    for w in pos_words: p+=t.count(w)
    for w in neg_words: n+=t.count(w)
    if p+n==0: return 0.0
    return round((p-n)/(p+n),3)

def classify_sentiment_label(score):
    if score>0.2: return "Positiv"
    if score<-0.2: return "Negativ"
    return "Neutral"

def headline_score(article):
    base = article.get("importance",3)*15
    txt = article.get("title","")+" "+article.get("desc","")
    s = sentiment_score(txt)
    base += s*10
    l = len(tokenize(article.get("title","")))
    base += max(0,8-abs(l-10))
    return int(max(0,min(100,base)))

# ----------------------------
# Favorites
# ----------------------------
def add_favorite(user,article_id):
    favs = FAVORITES.get(user,[])
    if article_id not in favs:
        favs.append(article_id)
    FAVORITES[user]=favs
    safe_save(FAV_FILE,FAVORITES)

def remove_favorite(user,article_id):
    favs = FAVORITES.get(user,[])
    if article_id in favs:
        favs.remove(article_id)
    FAVORITES[user]=favs
    safe_save(FAV_FILE,FAVORITES)

def user_favorites(user):
    return FAVORITES.get(user,[])

# ----------------------------
# Streamlit setup
# ----------------------------
st.set_page_config("Lumina News v3","wide")
if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=GLOBAL_SETTINGS.get("theme","light")
if "last_read" not in st.session_state: st.session_state.last_read=[]

# ----------------------------
# Theme CSS
# ----------------------------
LIGHT_CSS = """
body {background:#f7f9fc;color:#0b1a2b;}
.card {background:white;border-radius:8px;padding:12px;margin-bottom:12px;box-shadow:0 1px 6px rgba(10,20,40,0.08);}
.header {color:#004aad;}
.small {color:#666;font-size:12px;}
"""
DARK_CSS = """
body {background:#0b1220;color:#e6eef8;}
.card {background:#0f1724;border-radius:8px;padding:12px;margin-bottom:12px;box-shadow:0 1px 10px rgba(0,0,0,0.5);}
.header {color:#66b2ff;}
.small {color:#9fb7d9;font-size:12px;}
"""
def inject_css():
    css = LIGHT_CSS if st.session_state.theme=="light" else DARK_CSS
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)
inject_css()

# ----------------------------
# Authentication
# ----------------------------
if not st.session_state.logged_in:
    lcol,rcol=st.columns(2)
    with lcol:
        st.subheader("🔐 Login")
        with st.form("login"):
            uname=st.text_input("Benutzername")
            pwd=st.text_input("Passwort",type="password")
            submit=st.form_submit_button("Einloggen")
            if submit:
                if USERS.get(uname)==pwd:
                    st.session_state.logged_in=True
                    st.session_state.username=uname
                    st.success(f"Willkommen {uname}!")
                else: st.error("Falsche Zugangsdaten")
    with rcol:
        st.subheader("🆕 Registrierung")
        with st.form("register"):
            r_uname=st.text_input("Neuer Benutzername",key="reg_user")
            r_pwd=st.text_input("Neues Passwort",type="password",key="reg_pass")
            reg_submit=st.form_submit_button("Registrieren")
            if reg_submit:
                if not r_uname or not r_pwd: st.warning("Benutzername und Passwort angeben")
                elif r_uname in USERS: st.warning("Benutzer existiert bereits")
                else:
                    USERS[r_uname]=r_pwd
                    safe_save(USERS_FILE,USERS)
                    st.success("Registrierung erfolgreich!")
    st.stop()

username=st.session_state.username

# ----------------------------
# Load news from API with caching
# ----------------------------
def fetch_news():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        except: pass
    # Fetch from API
    api_key = st.secrets["newsapi"]["api_key"]
    url=f"https://newsapi.org/v2/top-headlines?language=de&pageSize=20&apiKey={api_key}"
    r=requests.get(url)
    data=r.json()
    articles=[]
    if data.get("status")=="ok":
        for a in data.get("articles",[]):
            articles.append({
                "id":a.get("url",""),
                "title":a.get("title",""),
                "desc":a.get("description","") or "",
                "date":a.get("publishedAt","")[:10],
                "importance":3
            })
    safe_save(CACHE_FILE,articles)
    return articles

NEWS_DB = {"Top":fetch_news()}
CATEGORIES=list(NEWS_DB.keys())

# ----------------------------
# Render card
# ----------------------------
def render_news_card(article,show_actions=True):
    title=article.get("title","")
    desc=article.get("desc","")
    date=article.get("date","")
    aid=article.get("id")
    score=headline_score(article)
    s_score=sentiment_score(desc)
    s_label=classify_sentiment_label(s_score)
    summary=extractive_summary(desc,2)
    favs=user_favorites(username)
    is_fav=aid in favs

    st.markdown(f"<div class='card'>",unsafe_allow_html=True)
    st.markdown(f"**{title}** <span class='small'>{date} • Score:{score} • Stimmung:{s_label}</span>")
    st.markdown(f"<div>{summary}</div>",unsafe_allow_html=True)
    st.markdown(f"<div style='color:#888;'>Volltext: {desc}</div>",unsafe_allow_html=True)
    if show_actions:
        c1,c2=st.columns([1,1])
        with c1:
            if st.button("★ Favorit" if not is_fav else "✖ Entfernen",key=aid):
                if not is_fav: add_favorite(username,aid)
                else: remove_favorite(username,aid)
                st.experimental_rerun()
    st.markdown("</div>",unsafe_allow_html=True)

# ----------------------------
# Sidebar & Pages
# ----------------------------
st.sidebar.title(f"👤 {username}")
page=st.sidebar.radio("Navigation",["🏠 Home","📚 Kategorien","⭐ Favoriten","⚙️ Profil/Einstellungen"])

# ---------- Home ----------
if page=="🏠 Home":
    st.header("🏠 Top News")
    for a in NEWS_DB["Top"][:10]:
        render_news_card(a)

# ---------- Kategorien ----------
elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    sel_cat=st.selectbox("Kategorie wählen",CATEGORIES)
    for a in NEWS_DB[sel_cat]:
        render_news_card(a)

# ---------- Favoriten ----------
elif page=="⭐ Favoriten":
    st.header("⭐ Favoriten")
    favs=user_favorites(username)
    if not favs: st.info("Keine Favoriten")
    else:
        for aid in favs:
            a=next((x for x in NEWS_DB["Top"] if x["id"]==aid),None)
            if a: render_news_card(a)

# ---------- Profil ----------
elif page=="⚙️ Profil/Einstellungen":
    st.header("⚙️ Profil")
    st.write(f"Benutzername: **{username}**")
    st.write(f"Favoriten insgesamt: {len(user_favorites(username))}")
    theme=st.selectbox("Theme",["light","dark"],index=0 if st.session_state.theme=="light" else 1)
    if theme!=st.session_state.theme:
        st.session_state.theme=theme
        GLOBAL_SETTINGS["theme"]=theme
        safe_save(SETTINGS_FILE,GLOBAL_SETTINGS)
        inject_css()
