# -*- coding: utf-8 -*-
"""
Lumina News v3.0 - Streamlit Echtzeit & Offline Edition
Features:
 - Login / Registrierung
 - Theme (hell/dunkel) Umschaltbar
 - Home mit Top-News & personalisiertem Feed
 - Kategorien, Favoriten, Suche
 - Echtzeit-News via NewsAPI (API Key bereits integriert)
 - Offline Cache für schnelle Ladezeiten
 - Analyzer: Sentiment, Schlagzeilen-Score, Top-Wörter
"""

import streamlit as st
import json, os, requests, re
from datetime import datetime
from collections import Counter

# ----------------------------
# Config / Files / API
# ----------------------------
API_KEY = "64457577c9a14eb9a846b69dcae0d659"
NEWS_FILE = "news_today.json"
USERS_FILE = "users.json"
FAV_FILE = "favorites.json"
SETTINGS_FILE = "settings.json"

# ----------------------------
# Helper functions
# ----------------------------
def safe_load(path, default):
    try:
        if os.path.exists(path):
            with open(path,"r",encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return default

def safe_save(path,data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
    except Exception as e:
        st.error(f"Fehler beim Speichern {path}: {e}")

# ----------------------------
# Initialize persistent files
# ----------------------------
if not os.path.exists(USERS_FILE):
    safe_save(USERS_FILE,{"admin":"1234"})

if not os.path.exists(FAV_FILE):
    safe_save(FAV_FILE,{})

if not os.path.exists(SETTINGS_FILE):
    safe_save(SETTINGS_FILE,{"theme":"light","home_count_each":2})

USERS = safe_load(USERS_FILE,{"admin":"1234"})
FAVORITES = safe_load(FAV_FILE,{})
GLOBAL_SETTINGS = safe_load(SETTINGS_FILE,{"theme":"light","home_count_each":2})

# ----------------------------
# News Fetch & Cache
# ----------------------------
def fetch_news():
    url = "https://newsapi.org/v2/top-headlines"
    params = {"language":"de","pageSize":50,"apiKey":API_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        articles = data.get("articles",[])
        # Simplify article fields
        news_list = []
        for idx,a in enumerate(articles):
            news_list.append({
                "id": f"api-{idx}",
                "title": a.get("title",""),
                "desc": a.get("description","") or "",
                "url": a.get("url",""),
                "date": a.get("publishedAt","")[:10],
                "importance": 3
            })
        safe_save(NEWS_FILE,news_list)
        return news_list
    except Exception as e:
        st.warning(f"NewsAPI nicht erreichbar. Offline Cache wird verwendet. ({e})")
        return safe_load(NEWS_FILE,[])

NEWS_DB = fetch_news()
CATEGORIES = ["Home","Politik","Wirtschaft","Sport","Technologie","Weltweit","Allgemein"]

# ----------------------------
# Text Analysis
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+", flags=re.UNICODE)
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei",
    "hat","haben","wird","werden","nicht","oder","aber","wir","ich","du","er","sie","es","dem","den","des"])

def tokenize(text):
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t)>2]

def extractive_summary(text, max_sentences=2):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences: return ""
    tokens = tokenize(text)
    freq = Counter(tokens)
    scored = []
    for s in sentences:
        s_tokens = tokenize(s)
        score = sum(freq.get(w,0) for w in s_tokens)
        scored.append((score,s))
    scored.sort(key=lambda x:x[0],reverse=True)
    return " ".join([s for _,s in scored[:max_sentences]])

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
    base = article.get("importance",3)*15
    txt = (article.get("title","")+" "+article.get("desc",""))
    base += sentiment_score(txt)*10
    l = len(tokenize(article.get("title","")))
    base += max(0,8-abs(l-10))
    return int(max(0,min(100,base)))

# ----------------------------
# Favorites
# ----------------------------
def add_favorite(user, article_id):
    favs = FAVORITES.get(user,[])
    if article_id not in favs: favs.append(article_id)
    FAVORITES[user]=favs
    safe_save(FAV_FILE,FAVORITES)

def remove_favorite(user, article_id):
    favs = FAVORITES.get(user,[])
    if article_id in favs: favs.remove(article_id)
    FAVORITES[user]=favs
    safe_save(FAV_FILE,FAVORITES)

def user_favorites(user):
    return FAVORITES.get(user,[])

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v3.0", layout="wide")

if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=GLOBAL_SETTINGS.get("theme","light")

# Theme
LIGHT_CSS = """
body{background-color:#f7f9fc;color:#0b1a2b;}
.card{background:white;border-radius:8px;padding:12px;margin-bottom:12px;box-shadow:0 1px 6px rgba(10,20,40,0.08);}
.header{color:#004aad;}
.small{color:#666;font-size:12px;}
"""
DARK_CSS = """
body{background-color:#0b1220;color:#e6eef8;}
.card{background:#0f1724;border-radius:8px;padding:12px;margin-bottom:12px;box-shadow:0 1px 10px rgba(0,0,0,0.5);}
.header{color:#66b2ff;}
.small{color:#9fb7d9;font-size:12px;}
"""
def inject_css():
    st.markdown(f"<style>{LIGHT_CSS if st.session_state.theme=='light' else DARK_CSS}</style>",unsafe_allow_html=True)
inject_css()

# Topbar
col1,col2 = st.columns([3,1])
with col1:
    st.markdown("<h1 class='header'>🌐 Lumina News v3.0</h1>",unsafe_allow_html=True)
with col2:
    theme_choice = st.selectbox("Theme",["light","dark"],index=0 if st.session_state.theme=="light" else 1)
    if theme_choice != st.session_state.theme:
        st.session_state.theme=theme_choice
        GLOBAL_SETTINGS["theme"]=theme_choice
        safe_save(SETTINGS_FILE,GLOBAL_SETTINGS)
        inject_css()

st.markdown("---")

# Authentication
if not st.session_state.logged_in:
    lcol,rcol = st.columns(2)
    with lcol:
        st.subheader("🔐 Anmelden")
        with st.form("login"):
            uname = st.text_input("Benutzername")
            pwd = st.text_input("Passwort",type="password")
            if st.form_submit_button("Einloggen"):
                if USERS.get(uname)==pwd:
                    st.session_state.logged_in=True
                    st.session_state.username=uname
                    st.success(f"Willkommen {uname}")
                else:
                    st.error("Falsche Zugangsdaten")
    with rcol:
        st.subheader("🆕 Registrieren")
        with st.form("register"):
            r_uname = st.text_input("Neuer Benutzername")
            r_pwd = st.text_input("Neues Passwort",type="password")
            if st.form_submit_button("Registrieren"):
                if not r_uname or not r_pwd:
                    st.warning("Benutzername + Passwort angeben")
                elif r_uname in USERS:
                    st.warning("Benutzer existiert bereits")
                else:
                    USERS[r_uname]=r_pwd
                    safe_save(USERS_FILE,USERS)
                    st.success("Registrierung erfolgreich! Bitte anmelden.")
    st.stop()

username = st.session_state.username

# Sidebar
st.sidebar.title(f"👤 {username}")
pages = ["🏠 Home","📚 Kategorien","🔎 Suche","📊 Analyse","⭐ Favoriten"]
page = st.sidebar.radio("Navigation",pages)

# Helper: render news card
def render_news_card(article):
    aid = article.get("id")
    st.markdown(f"<div class='card'>",unsafe_allow_html=True)
    st.markdown(f"**{article.get('title','')}**  <span class='small'>{article.get('date','')} • Score: {headline_score(article)}</span>")
    st.markdown(f"<div style='margin-top:8px'>{extractive_summary(article.get('desc',''))}</div>",unsafe_allow_html=True)
    st.markdown(f"<div style='margin-top:8px; color:#888;'>Volltext: {article.get('desc','')}</div>",unsafe_allow_html=True)
    cols=st.columns([1,1])
    with cols[0]:
        if st.button("★ Favorit", key=f"fav-{aid}"):
            add_favorite(username,aid)
            st.success("Hinzugefügt")
    with cols[1]:
        if st.button("✖ Entfernen", key=f"unfav-{aid}"):
            remove_favorite(username,aid)
            st.info("Entfernt")
    st.markdown("</div>",unsafe_allow_html=True)

# ---------- Page logic ----------
if page=="🏠 Home":
    st.header("🏠 Home")
    top_news = sorted(NEWS_DB,key=lambda x:x.get("importance",3),reverse=True)[:10]
    for n in top_news:
        render_news_card(n)

elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    cat = st.selectbox("Kategorie wählen",CATEGORIES)
    cat_news = NEWS_DB
    for n in cat_news:
        render_news_card(n)

elif page=="🔎 Suche":
    st.header("🔎 Suche")
    q = st.text_input("Suchbegriff")
    if st.button("Suchen"):
        hits = [a for a in NEWS_DB if q.lower() in (a.get("title","")+a.get("desc","")).lower()]
        st.write(f"{len(hits)} Treffer")
        for n in hits: render_news_card(n)

elif page=="📊 Analyse":
    st.header("📊 Analyse")
    from matplotlib import pyplot as plt
    sentiments = [classify_sentiment_label(sentiment_score(a.get("desc","")+a.get("title",""))) for a in NEWS_DB]
    pos = sentiments.count("Positiv")
    neu = sentiments.count("Neutral")
    neg = sentiments.count("Negativ")
    fig,ax = plt.subplots()
    ax.bar(["Positiv","Neutral","Negativ"],[pos,neu,neg],color=["#2ecc71","#3498db","#e74c3c"])
    ax.set_ylabel("Anzahl Artikel")
    st.pyplot(fig)

    # Top Wörter
    twords = Counter()
    for a in NEWS_DB:
        for w in tokenize(a.get("desc","")):
            twords[w]+=1
    top_words = twords.most_common(10)
    st.write("Top Wörter:",top_words)
    if top_words:
        words,counts = zip(*top_words)
        fig2,ax2 = plt.subplots()
        ax2.barh(words,counts,color="#9b59b6")
        ax2.invert_yaxis()
        st.pyplot(fig2)

elif page=="⭐ Favoriten":
    st.header("⭐ Favoriten")
    favs = user_favorites(username)
    if not favs: st.info("Keine Favoriten")
    else:
        for fid in favs:
            a = next((x for x in NEWS_DB if x.get("id")==fid),None)
            if a: render_news_card(a)
