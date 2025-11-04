# -*- coding: utf-8 -*-
"""
Lumina News v3.0 - Streamlit Edition mit echten News & Offline-Cache
Features:
 - Login / Registrierung
 - Theme (light/dark/neon)
 - Home & personalisierte News
 - Kategorien, Favoriten, Profil
 - Offline Analyzer: Sentiment, Headline-Scoring, Extractive Summary
 - Automatische News-Aktualisierung 2x täglich
 - Keine externe DB notwendig
"""
import streamlit as st
import json, os, re, requests
from datetime import datetime, timedelta
from collections import Counter
import requests

url = f"https://newsapi.org/v2/top-headlines?language=de&pageSize=5&apiKey={st.secrets['newsapi']['api_key']}"
res = requests.get(url).json()
st.write(res)

# ----------------------------
# Files
# ----------------------------
USERS_FILE = "users.json"
FAV_FILE = "favorites.json"
SETTINGS_FILE = "settings.json"
NEWS_FILE = "news_today.json"

# ----------------------------
# Safe JSON helpers
# ----------------------------
def safe_load(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return default

def safe_save(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Fehler beim Speichern von {path}: {e}")

# ----------------------------
# Init files if missing
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
# Offline text analyzer
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei","hat","haben","wird","werden","nicht","oder","aber","wir","ich","du","er","sie","es","dem","den","des"])

def tokenize(text):
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t)>2]

def extractive_summary(text,max_sentences=2):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences: return ""
    freq = Counter(tokenize(text))
    scored = []
    for s in sentences:
        s_tokens = tokenize(s)
        score = sum(freq.get(w,0) for w in s_tokens)
        scored.append((score,s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return " ".join([s for _,s in scored[:max_sentences]])

def sentiment_score(text):
    pos_words = ["erfolgreich","gewinnt","stark","besser","stabil","positiv","lob","begeistert","sieg","förder"]
    neg_words = ["krise","verlust","scheit","problem","kritik","sorgen","unsicher","verzöger","einbruch","attack"]
    t = text.lower()
    pos = sum(p in t for p in pos_words)
    neg = sum(n in t for n in neg_words)
    if pos+neg==0: return 0.0
    return round((pos-neg)/(pos+neg),3)

def classify_sentiment_label(score):
    if score>0.2: return "Positiv"
    if score<-0.2: return "Negativ"
    return "Neutral"

def headline_score(article):
    base = article.get("importance",3)*15
    txt = (article.get("title","")+" "+article.get("desc",""))
    s = sentiment_score(txt)
    base += s*10
    l = len(tokenize(article.get("title","")))
    base += max(0,8-abs(l-10))
    return int(max(0,min(100,base)))

# ----------------------------
# Favorites
# ----------------------------
def load_favorites():
    return safe_load(FAV_FILE,{})

def save_favorites(favs):
    safe_save(FAV_FILE,favs)

def add_favorite(user,aid):
    favs = FAVORITES.get(user,[])
    if aid not in favs:
        favs.append(aid)
    FAVORITES[user]=favs
    save_favorites(FAVORITES)

def remove_favorite(user,aid):
    favs = FAVORITES.get(user,[])
    if aid in favs: favs.remove(aid)
    FAVORITES[user]=favs
    save_favorites(FAVORITES)

def user_favorites(user):
    return FAVORITES.get(user,[])

# ----------------------------
# Settings
# ----------------------------
def load_settings():
    return safe_load(SETTINGS_FILE,{"theme":"light","home_count_each":2})

def save_settings(settings):
    safe_save(SETTINGS_FILE,settings)

GLOBAL_SETTINGS = load_settings()

# ----------------------------
# News fetching & caching
# ----------------------------
API_KEY = st.secrets["newsapi"]["api_key"]  # Streamlit secrets
CATEGORIES = ["Powi","Wirtschaft","Politik","Sport","Technologie","Weltweit","Allgemein"]

def need_update():
    if not os.path.exists(NEWS_FILE): return True
    mtime = datetime.fromtimestamp(os.path.getmtime(NEWS_FILE))
    return datetime.now()-mtime > timedelta(hours=12)

def fetch_news():
    all_news = {cat:[] for cat in CATEGORIES}
    for cat in CATEGORIES:
        url = f"https://newsapi.org/v2/top-headlines?language=de&category=general&pageSize=10&apiKey={API_KEY}"
        try:
            r = requests.get(url)
            if r.status_code==200:
                data = r.json().get("articles",[])
                for idx,art in enumerate(data):
                    all_news[cat].append({
                        "id":f"{cat.lower()}-{idx}",
                        "title":art.get("title",""),
                        "desc":art.get("description","") or "",
                        "date":art.get("publishedAt",""),
                        "importance":3
                    })
        except:
            pass
    safe_save(NEWS_FILE,all_news)
    return all_news

def load_local_news():
    if need_update():
        return fetch_news()
    return safe_load(NEWS_FILE,{cat:[] for cat in CATEGORIES})

NEWS_DB = load_local_news()

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v3.0",layout="wide")

if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=GLOBAL_SETTINGS.get("theme","light")
if "last_read" not in st.session_state: st.session_state.last_read=[]

LIGHT_CSS="""
body { background-color: #f7f9fc; color: #0b1a2b; }
.card { background: white; border-radius:8px; padding:12px; box-shadow:0 1px 6px rgba(10,20,40,0.08); margin-bottom:12px; }
.header { color:#004aad; }
.small { color:#666; font-size:12px; }
"""
DARK_CSS="""
body { background-color: #0b1220; color: #e6eef8; }
.card { background:#0f1724; border-radius:8px; padding:12px; box-shadow:0 1px 10px rgba(0,0,0,0.5); margin-bottom:12px; }
.header { color:#66b2ff; }
.small { color:#9fb7d9; font-size:12px; }
"""

def inject_css():
    css = LIGHT_CSS if st.session_state.theme=="light" else DARK_CSS
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)

inject_css()

# Topbar
col1,col2=st.columns([3,1])
with col1:
    st.markdown("<h1 class='header'>🌐 Lumina News v3.0</h1>",unsafe_allow_html=True)
with col2:
    theme_choice = st.selectbox("Theme",["light","dark"],index=0 if st.session_state.theme=="light" else 1)
    if theme_choice!=st.session_state.theme:
        st.session_state.theme=theme_choice
        GLOBAL_SETTINGS["theme"]=theme_choice
        save_settings(GLOBAL_SETTINGS)
        inject_css()

st.markdown("---")

# Authentication
if not st.session_state.logged_in:
    lcol,rcol=st.columns(2)
    with lcol:
        st.subheader("🔐 Anmelden")
        with st.form("login_form"):
            uname=st.text_input("Benutzername",key="login_user")
            pwd=st.text_input("Passwort",type="password",key="login_pass")
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
            r_uname=st.text_input("Neuer Benutzername",key="reg_user")
            r_pwd=st.text_input("Neues Passwort",type="password",key="reg_pass")
            reg_submit=st.form_submit_button("Registrieren")
            if reg_submit:
                users=safe_load(USERS_FILE,{"admin":"1234"})
                if not r_uname or not r_pwd: st.warning("Bitte Benutzernamen und Passwort angeben.")
                elif r_uname in users: st.warning("Benutzer existiert bereits.")
                else:
                    users[r_uname]=r_pwd
                    safe_save(USERS_FILE,users)
                    st.success("Registrierung erfolgreich! Bitte anmelden.")
    st.stop()

username = st.session_state.username

# Sidebar navigation
st.sidebar.title(f"👤 {username}")
pages = ["🏠 Home","📚 Kategorien","⭐ Favoriten","⚙️ Profil / Einstellungen"]
page = st.sidebar.radio("Navigation",pages)

# Helper
def render_news_card(article,cat,show_actions=True):
    title=article.get("title","")
    desc=article.get("desc","")
    date=article.get("date","")
    aid=article.get("id")
    score=headline_score(article)
    s_score=sentiment_score(desc)
    s_label=classify_sentiment_label(s_score)
    summary=extractive_summary(desc)
    favs=user_favorites(username)
    is_fav=aid in favs

    st.markdown(f"<div class='card'>",unsafe_allow_html=True)
    st.markdown(f"**{title}**  <span class='small'>{date} • Score: {score} • Stimmung: {s_label}</span>")
    st.markdown(f"<div>{summary}</div>",unsafe_allow_html=True)
    st.markdown(f"<div style='color:#888;'>Volltext: {desc}</div>",unsafe_allow_html=True)
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

# ---------- Pages ----------
if page=="🏠 Home":
    st.header("🏠 Home — Wichtige & personalisierte News")
    n_each=GLOBAL_SETTINGS.get("home_count_each",2)
    top_items=[]
    for cat in CATEGORIES:
        top = NEWS_DB.get(cat,[])[:n_each]
        for t in top: top_items.append((t,cat))
    for art,cat in top_items:
        render_news_card(art,cat)

elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    sel_cat = st.selectbox("Kategorie wählen",["Alle"]+CATEGORIES)
    filter_mood = st.selectbox("Filter Stimmung",["Alle","Positiv","Neutral","Negativ"])
    items=[]
    cats_to_show=CATEGORIES if sel_cat=="Alle" else [sel_cat]
    for cat in cats_to_show:
        for a in NEWS_DB.get(cat,[]):
            s_label=classify_sentiment_label(sentiment_score(a.get("desc","")))
            if filter_mood!="Alle" and s_label!=filter_mood: continue
            items.append((a,cat))
    for a,c in items: render_news_card(a,c)

elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs=user_favorites(username)
    if not favs: st.info("Keine Favoriten.")
    else:
        for aid in favs:
            art=None
            cat=None
            for c in CATEGORIES:
                for a in NEWS_DB.get(c,[]):
                    if a.get("id")==aid: art=a; cat=c; break
            if art: render_news_card(art,cat)

elif page=="⚙️ Profil / Einstellungen":
    st.header("⚙️ Profil & Einstellungen")
    st.write(f"Benutzername: **{username}**")
    favs_count=len(user_favorites(username))
    st.write(f"Favoriten insgesamt: {favs_count}")

    c1,c2=st.columns(2)
    with c1:
        home_count=st.number_input("Anzahl Top-News pro Kategorie auf Home",min_value=1,max_value=5,value=GLOBAL_SETTINGS.get("home_count_each",2))
        if st.button("Speichern Home-Einstellung"):
            GLOBAL_SETTINGS["home_count_each"]=home_count
            save_settings(GLOBAL_SETTINGS)
            st.success("Gespeichert")
    with c2:
        if st.button("Alle Favoriten löschen"):
            FAVORITES[username]=[]
            save_favorites(FAVORITES)
            st.info("Favoriten gelöscht")
