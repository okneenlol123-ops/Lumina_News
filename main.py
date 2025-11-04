# -*- coding: utf-8 -*-
"""
Lumina News v3.0 - Streamlit Edition mit NewsAPI
Features:
 - Login / Registrierung (users.json)
 - Theme (light/dark) Umschaltbar (settings.json)
 - Home mit wichtigsten Artikeln & personalisiertem Feed
 - Kategorien & News-Karten
 - Offline KI: Extractive Summary, Sentiment, Headline-Scoring
 - Favoriten / Lesezeichen (favorites.json, pro user)
 - Suche + Filter (Stimmung, Wichtigkeit)
 - Profilseite mit Statistiken
 - Englische News via NewsAPI, täglich automatisch aktualisiert
"""
import streamlit as st
import json, os, re, requests
from datetime import datetime, date
from collections import Counter

# ----------------------------
# File paths
# ----------------------------
USERS_FILE = "users.json"
FAV_FILE = "favorites.json"
SETTINGS_FILE = "settings.json"
NEWS_CACHE_FILE = "newsapi_cache.json"

# ----------------------------
# Safe JSON helpers
# ----------------------------
def safe_load(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return default

def safe_save(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: st.error(f"Fehler beim Speichern von {path}")

# ----------------------------
# Initialize persistent files
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
# NewsAPI Integration
# ----------------------------
API_KEY = st.secrets["newsapi"]["api_key"]
CATEGORIES_API = ["business","entertainment","general","health","science","sports","technology"]

def load_news_cache():
    if os.path.exists(NEWS_CACHE_FILE):
        try:
            with open(NEWS_CACHE_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"last_update":"","articles":[]}

def save_news_cache(data):
    with open(NEWS_CACHE_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def fetch_newsapi():
    all_articles = []
    for cat in CATEGORIES_API:
        url = f"https://newsapi.org/v2/top-headlines?category={cat}&pageSize=10&language=en&apiKey={API_KEY}"
        try:
            resp = requests.get(url,timeout=10).json()
            if resp.get("status")=="ok":
                for a in resp.get("articles",[]):
                    all_articles.append({
                        "id": a.get("url"),
                        "title": a.get("title",""),
                        "desc": a.get("description") or "",
                        "date": a.get("publishedAt","")[:10],
                        "category": cat.capitalize(),
                        "importance":3
                    })
        except:
            st.warning(f"NewsAPI Kategorie {cat} konnte nicht geladen werden")
    cache = {"last_update": str(date.today()), "articles": all_articles}
    save_news_cache(cache)
    return all_articles

def get_newsapi(force_update=False):
    cache = load_news_cache()
    if cache.get("last_update") != str(date.today()) or force_update:
        return fetch_newsapi()
    return cache.get("articles",[])

# ----------------------------
# Offline News DB (deutsche Beispiel-News)
# ----------------------------
def build_news_db():
    db = {
        "Politik":[
            {"id":"po-1","title":"Koalitionsgespräche gehen in finale Phase","desc":"Verhandlungen zu Klima und Finanzen erreichen Schlüsselmomente.","date":"2025-11-01","importance":5},
            {"id":"po-2","title":"Datenschutz und KI: neue Regeln","desc":"Parlamentarische Beratungen zu Datenschutzanpassungen im KI-Kontext beginnen.","date":"2025-05-19","importance":5}
        ],
        "Wirtschaft":[
            {"id":"wi-1","title":"Industrieproduktion verzeichnet Aufschwung","desc":"Die Industrie meldet ein moderates Wachstum.","date":"2025-10-20","importance":4}
        ],
        "Sport":[
            {"id":"sp-1","title":"Nationalteam gewinnt wichtiges Qualifikationsspiel","desc":"Das Team feierte einen knappen Sieg.","date":"2025-10-31","importance":5}
        ],
        "Technologie":[
            {"id":"te-1","title":"Neuer KI-Chip verspricht Effizienz","desc":"Ein Halbleiterhersteller kündigt einen energieeffizienten KI-Chip an.","date":"2025-10-30","importance":5}
        ]
    }
    return db

NEWS_DB = build_news_db()
CATEGORIES = list(NEWS_DB.keys())

# ----------------------------
# Text utils
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+")
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
    s = sentiment_score(article.get("title","")+article.get("desc",""))
    base += s*10
    l = len(tokenize(article.get("title","")))
    base += max(0,8-abs(l-10))
    return int(max(0,min(100,base)))

# ----------------------------
# Favorites management
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
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v3.0",layout="wide")

if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=GLOBAL_SETTINGS.get("theme","light")
if "last_read" not in st.session_state: st.session_state.last_read=[]

# Theme CSS
LIGHT_CSS="body { background-color: #f7f9fc; color:#0b1a2b; } .card { background:white; border-radius:8px;padding:12px;margin-bottom:12px; } .header { color:#004aad; } .small { color:#666;font-size:12px; }"
DARK_CSS="body { background-color: #0b1220; color:#e6eef8; } .card { background:#0f1724; border-radius:8px;padding:12px;margin-bottom:12px; } .header { color:#66b2ff; } .small { color:#9fb7d9;font-size:12px; }"

def inject_css():
    css = LIGHT_CSS if st.session_state.theme=="light" else DARK_CSS
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)

inject_css()

# Topbar
col1,col2=st.columns([3,1])
with col1: st.markdown("<h1 class='header'>🌐 Lumina News v3.0</h1>",unsafe_allow_html=True)
with col2:
    theme_choice=st.selectbox("Theme",["light","dark"],index=0 if st.session_state.theme=="light" else 1)
    if theme_choice != st.session_state.theme:
        st.session_state.theme=theme_choice
        GLOBAL_SETTINGS["theme"]=theme_choice
        safe_save(SETTINGS_FILE,GLOBAL_SETTINGS)
        inject_css()

st.markdown("---")

# Authentication
if not st.session_state.logged_in:
    lcol,rcol=st.columns(2)
    with lcol:
        st.subheader("🔐 Anmelden")
        with st.form("login_form"):
            uname = st.text_input("Benutzername")
            pwd = st.text_input("Passwort",type="password")
            submit=st.form_submit_button("Einloggen")
            if submit:
                users=safe_load(USERS_FILE,{"admin":"1234"})
                if users.get(uname)==pwd:
                    st.session_state.logged_in=True
                    st.session_state.username=uname
                    st.success(f"Willkommen, {uname}!")
                else: st.error("Falsche Zugangsdaten.")
    with rcol:
        st.subheader("🆕 Registrieren")
        with st.form("reg_form"):
            r_uname=st.text_input("Neuer Benutzername")
            r_pwd=st.text_input("Neues Passwort",type="password")
            reg_submit=st.form_submit_button("Registrieren")
            if reg_submit:
                users=safe_load(USERS_FILE,{"admin":"1234"})
                if not r_uname or not r_pwd:
                    st.warning("Bitte Benutzernamen und Passwort angeben.")
                elif r_uname in users:
                    st.warning("Benutzer existiert bereits.")
                else:
                    users[r_uname]=r_pwd
                    safe_save(USERS_FILE,users)
                    st.success("Registrierung erfolgreich! Bitte anmelden.")
    st.stop()

username=st.session_state.username

# Sidebar
st.sidebar.title(f"👤 {username}")
pages=["🏠 Home","🔎 Suche","📚 Kategorien","⭐ Favoriten","⚙️ Profil / Einstellungen"]
page=st.sidebar.radio("Navigation",pages)

# Helper to render card
def render_news_card(article,category,show_actions=True):
    title=article.get("title","")
    desc=article.get("desc","")
    date_art=article.get("date","")
    imp=article.get("importance",3)
    aid=article.get("id")
    score=headline_score(article)
    s_score=sentiment_score(desc)
    s_label=classify_sentiment_label(s_score)
    summary=extractive_summary(desc,2)
    favs=user_favorites(username)
    is_fav=aid in favs
    st.markdown(f"<div class='card'>",unsafe_allow_html=True)
    st.markdown(f"**{title}**  <span class='small'>{date_art} • Wichtigkeit:{imp} • Score:{score} • Stimmung:{s_label}</span>")
    st.markdown(f"<div style='margin-top:8px'>{summary}</div>",unsafe_allow_html=True)
    st.markdown(f"<div style='margin-top:8px;color:#888;'>Volltext: {desc}</div>",unsafe_allow_html=True)
    cols=st.columns([1,1,1,6])
    with cols[0]:
        if show_actions and st.button("Lesen",key=f"read-{aid}"):
            st.session_state.last_read.insert(0,aid)
            if len(st.session_state.last_read)>50: st.session_state.last_read=st.session_state.last_read[:50]
            st.experimental_rerun()
    with cols[1]:
        if show_actions and not is_fav and st.button("★ Favorit",key=f"fav-{aid}"):
            add_favorite(username,aid)
            st.success("Zur Favoritenliste hinzugefügt")
            st.experimental_rerun()
    with cols[2]:
        if show_actions and is_fav and st.button("✖ Entfernen",key=f"unfav-{aid}"):
            remove_favorite(username,aid)
            st.info("Aus Favoriten entfernt")
            st.experimental_rerun()
    st.markdown("</div>",unsafe_allow_html=True)

# ---------- Load ALL News ----------
API_NEWS=get_newsapi()
ALL_NEWS=[]
for cat in CATEGORIES:
    for a in NEWS_DB[cat]:
        a["category"]=cat
        ALL_NEWS.append(a)
for a in API_NEWS: ALL_NEWS.append(a)

# ---------- Page: Home ----------
if page=="🏠 Home":
    st.header("🏠 Home — Wichtige & personalisierte News")
    ALL_NEWS_SORTED=sorted(ALL_NEWS,key=lambda x:(x.get("importance",3),x.get("date","")),reverse=True)
    for art in ALL_NEWS_SORTED[:10]: render_news_card(art,art.get("category","Allgemein"))

# ---------- Page: Suche ----------
elif page=="🔎 Suche":
    st.header("🔎 Suche")
    q=st.text_input("Suchbegriff")
    mood=st.selectbox("Stimmung filtern",["Alle","Positiv","Neutral","Negativ"])
    min_imp=st.slider("Minimale Wichtigkeit",1,5,1)
    if st.button("Suchen"):
        hits=[]
        for a in ALL_NEWS:
            txt=(a.get("title","")+a.get("desc","")).lower()
            if q.lower() in txt:
                sscore=sentiment_score(txt)
                label=classify_sentiment_label(sscore)
                if mood!="Alle" and label!=mood: continue
                if a.get("importance",0)<min_imp: continue
                hits.append((headline_score(a),a,label))
        hits.sort(key=lambda x:x[0],reverse=True)
        st.write(f"{len(hits)} Treffer")
        for _,a,label in hits: render_news_card(a,a.get("category","Allgemein"))

# ---------- Page: Kategorien ----------
elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    sel_cat=st.selectbox("Kategorie wählen",["Alle"]+CATEGORIES_API+CATEGORIES)
    filter_mood=st.selectbox("Filter Stimmung",["Alle","Positiv","Neutral","Negativ"])
    filter_imp=st.slider("Min. Wichtigkeit",1,5,1)
    items=[]
    cats_to_show=[sel_cat] if sel_cat!="Alle" else list(set([a.get("category","Allgemein") for a in ALL_NEWS]))
    for a in ALL_NEWS:
        if a.get("category","Allgemein") not in cats_to_show: continue
        label=classify_sentiment_label(sentiment_score(a.get("desc","")))
        if filter_mood!="Alle" and label!=filter_mood: continue
        if a.get("importance",0)<filter_imp: continue
        items.append((a,headline_score(a)))
    items.sort(key=lambda x:x[1],reverse=True)
    for a,_ in items: render_news_card(a,a.get("category","Allgemein"))

# ---------- Page: Favoriten ----------
elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs=user_favorites(username)
    if not favs: st.info("Keine Favoriten. ★ zum Speichern nutzen")
    else:
        for aid in favs:
            for a in ALL_NEWS:
                if a.get("id")==aid: render_news_card(a,a.get("category","Allgemein"))

# ---------- Page: Profil / Einstellungen ----------
elif page=="⚙️ Profil / Einstellungen":
    st.header("⚙️ Profil & Einstellungen")
    st.subheader("Benutzerinfo")
    st.write(f"Benutzername: **{username}**")
    st.write("Favoriten insgesamt:",len(user_favorites(username)))
    st.subheader("Einstellungen")
    home_count=st.number_input("Anzahl Top-News pro Kategorie auf Home",min_value=1,max_value=5,value=GLOBAL_SETTINGS.get("home_count_each",2))
    if st.button("Speichern Home-Einstellung"):
        GLOBAL_SETTINGS["home_count_each"]=home_count
        safe_save(SETTINGS_FILE,GLOBAL_SETTINGS)
        st.success("Gespeichert")
