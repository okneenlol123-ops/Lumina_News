# -*- coding: utf-8 -*-
"""
Lumina News v2.5 - Offline Streamlit Edition
"""
import streamlit as st
import json, os, math, re
from datetime import datetime
from collections import Counter

# -------------------------
# Safe File Handling
# -------------------------
FILES = {
    "users":"users.json",
    "favorites":"favorites.json",
    "settings":"settings.json",
    "read_log":"read_log.json"
}

def safe_load(path,default):
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
    except: pass

USERS = safe_load(FILES["users"],{"admin":"1234"})
FAVORITES = safe_load(FILES["favorites"],{})
SETTINGS = safe_load(FILES["settings"],{"theme":"light"})
READ_LOG = safe_load(FILES["read_log"],{})

# -------------------------
# News DB
# -------------------------
def build_news_db():
    # Abgekürzt, nur exemplarisch; nutze vorher definierten News-Content
    return safe_load("news_db.json",{})

NEWS_DB = build_news_db()
CATEGORIES = list(NEWS_DB.keys())

# -------------------------
# Text Analytics
# -------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+")
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei","hat","haben","wird","werden","nicht","oder","aber"])

def tokenize(text):
    return [t.lower() for t in WORD_RE.findall(text) if t.lower() not in STOPWORDS and len(t)>2]

def sentiment_score(text):
    pos = ["erfolgreich","gewinnt","stark","besser","stabil","positiv","lob","begeistert","sieg","förder"]
    neg = ["krise","verlust","scheit","problem","kritik","sorgen","unsicher","verzöger","einbruch","attack"]
    t = text.lower()
    p = sum(1 for w in pos if w in t)
    n = sum(1 for w in neg if w in t)
    return round((p-n)/(p+n),3) if (p+n)>0 else 0.0

def classify_sentiment(score):
    if score>0.2: return "Positiv"
    if score<-0.2: return "Negativ"
    return "Neutral"

def extract_summary(text,max_sentences=2):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    tokens = tokenize(text)
    freq = Counter(tokens)
    scored = [(sum(freq.get(w,0) for w in tokenize(s)),s) for s in sentences]
    scored.sort(key=lambda x:x[0],reverse=True)
    return " ".join([s for _,s in scored[:max_sentences]])

# -------------------------
# Favorites & Profile
# -------------------------
def add_favorite(user,aid):
    favs = FAVORITES.get(user,[])
    if aid not in favs: favs.append(aid)
    FAVORITES[user]=favs
    safe_save(FILES["favorites"],FAVORITES)

def remove_favorite(user,aid):
    favs = FAVORITES.get(user,[])
    if aid in favs: favs.remove(aid)
    FAVORITES[user]=favs
    safe_save(FILES["favorites"],FAVORITES)

def user_favorites(user): return FAVORITES.get(user,[])

def log_read(user,aid):
    READ_LOG.setdefault(user,[])
    READ_LOG[user].append({"id":aid,"ts":datetime.now().isoformat()})
    safe_save(FILES["read_log"],READ_LOG)

def user_profile(username):
    favs = user_favorites(username)
    cats = Counter()
    for fid in favs:
        for cat,arts in NEWS_DB.items():
            if any(a["id"]==fid for a in arts): cats[cat]+=1
    read_entries = READ_LOG.get(username,[])
    read_cats = Counter()
    for entry in read_entries:
        aid = entry["id"]
        for cat,arts in NEWS_DB.items():
            if any(a["id"]==aid for a in arts): read_cats[cat]+=1
    return {"favorites_total":len(favs),"fav_by_category":dict(cats),"read_by_category":dict(read_cats)}

# -------------------------
# Trend Analyzer
# -------------------------
def trend_words(top_n=10):
    counter = Counter()
    for cat,arts in NEWS_DB.items():
        for a in arts:
            counter.update(tokenize(a["title"]+" "+a["desc"]))
    return counter.most_common(top_n)

def similar_articles(aid,top_n=3):
    target = None
    for cat,arts in NEWS_DB.items():
        for a in arts:
            if a["id"]==aid: target=a
    if not target: return []
    vec1 = Counter(tokenize(target["title"]+" "+target["desc"]))
    sims=[]
    for cat,arts in NEWS_DB.items():
        for a in arts:
            if a["id"]==aid: continue
            vec2 = Counter(tokenize(a["title"]+" "+a["desc"]))
            common = sum(vec1[k]*vec2.get(k,0) for k in vec1)
            norm1 = math.sqrt(sum(v*v for v in vec1.values()))
            norm2 = math.sqrt(sum(v*v for v in vec2.values()))
            score = common/(norm1*norm2) if norm1*norm2>0 else 0
            sims.append((score,a))
    sims.sort(key=lambda x:x[0],reverse=True)
    return [a for _,a in sims[:top_n]]

# -------------------------
# Streamlit Setup
# -------------------------
st.set_page_config(page_title="Lumina News v2.5", layout="wide")
if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=SETTINGS.get("theme","light")

# -------------------------
# CSS Styling
# -------------------------
CSS_THEMES = {
    "light":"""
        body{background:#f7f9fc;color:#0b1a2b;}
        .card{background:white;padding:15px;margin-bottom:12px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
        .header{color:#004aad;}
    """,
    "dark":"""
        body{background:#0b1220;color:#e6eef8;}
        .card{background:#0f1724;padding:15px;margin-bottom:12px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.5);}
        .header{color:#66b2ff;}
    """,
    "neon":"""
        body{background:#01010f;color:#00fff0;}
        .card{background:#01010f;border:1px solid #00ffff;padding:15px;margin-bottom:12px;border-radius:8px;box-shadow:0 0 10px #00ffff88;}
        .header{color:#00ffea;}
    """
}
st.markdown(f"<style>{CSS_THEMES.get(st.session_state.theme,'')}</style>",unsafe_allow_html=True)

# -------------------------
# Authentication
# -------------------------
if not st.session_state.logged_in:
    st.subheader("🔐 Login oder Registrieren")
    lcol,rcol = st.columns(2)
    with lcol:
        with st.form("login_form"):
            uname = st.text_input("Benutzername")
            pwd = st.text_input("Passwort",type="password")
            submit = st.form_submit_button("Einloggen")
            if submit:
                if USERS.get(uname)==pwd:
                    st.session_state.username=uname
                    st.session_state.logged_in=True
                    st.success(f"Willkommen {uname}")
                else: st.error("Falsche Zugangsdaten")
    with rcol:
        with st.form("reg_form"):
            r_uname = st.text_input("Neuer Benutzername")
            r_pwd = st.text_input("Neues Passwort",type="password")
            submit_reg = st.form_submit_button("Registrieren")
            if submit_reg:
                if not r_uname or not r_pwd: st.warning("Bitte beide Felder ausfüllen")
                elif r_uname in USERS: st.warning("Benutzer existiert schon")
                else:
                    USERS[r_uname]=r_pwd
                    safe_save(FILES["users"],USERS)
                    st.success("Registrierung erfolgreich! Bitte anmelden.")
    st.stop()

username = st.session_state.username

# -------------------------
# Sidebar Navigation
# -------------------------
st.sidebar.title(f"👤 {username}")
pages = ["🏠 Home","📚 Kategorien","📊 Analyse","⭐ Favoriten","⚙️ Einstellungen"]
page = st.sidebar.radio("Navigation",pages)

# -------------------------
# Helper: Render News Card
# -------------------------
def render_card(a):
    st.markdown(f"<div class='card'><b>{a['title']}</b> <span class='small'>{a['date']} • Wichtig: {a['importance']}</span><br>{extract_summary(a['desc'])}</div>",unsafe_allow_html=True)
    col1,col2,col3 = st.columns([1,1,1])
    aid = a["id"]
    if col1.button("Lesen",key=f"read-{aid}"):
        log_read(username,aid)
        st.experimental_rerun()
    if col2.button("★ Favorit",key=f"fav-{aid}"):
        add_favorite(username,aid)
        st.experimental_rerun()
    if col3.button("✖ Entfernen",key=f"unfav-{aid}"):
        remove_favorite(username,aid)
        st.experimental_rerun()# -------------------------
# Pages Implementation
# -------------------------

# --- Helper: Show full article ---
def show_article(a):
    st.subheader(a["title"])
    st.markdown(f"*Datum: {a['date']} • Wichtig: {a['importance']}*")
    s = sentiment_score(a["title"] + " " + a["desc"])
    st.markdown(f"*Sentiment: {classify_sentiment(s)} ({s})*")
    st.write(a["desc"])
    # Show similar articles
    st.markdown("**Ähnliche Artikel:**")
    sims = similar_articles(a["id"])
    for s_a in sims:
        st.markdown(f"- {s_a['title']} ({s_a['date']})")

# --- Page: Home ---
if page=="🏠 Home":
    st.header("🏠 Lumina News - Home")
    # show top 3 important articles per category
    for cat in CATEGORIES:
        st.subheader(f"📌 {cat}")
        arts = sorted(NEWS_DB[cat], key=lambda x:x["importance"], reverse=True)
        for a in arts[:3]:
            render_card(a)

# --- Page: Kategorien ---
elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    sel_cat = st.selectbox("Kategorie wählen", CATEGORIES)
    arts = sorted(NEWS_DB[sel_cat], key=lambda x:x["date"], reverse=True)
    for a in arts:
        render_card(a)

# --- Page: Analyse ---
elif page=="📊 Analyse":
    st.header("📊 Analyse")
    st.subheader("🔥 Trend-Wörter")
    trends = trend_words()
    trend_text = ", ".join([f"{w} ({c})" for w,c in trends])
    st.write(trend_text)
    
    st.subheader("📈 Leseprofil")
    profile = user_profile(username)
    st.write(f"⭐ Favoriten insgesamt: {profile['favorites_total']}")
    st.write("Favoriten nach Kategorie:", profile["fav_by_category"])
    st.write("Gelesene Artikel nach Kategorie:", profile["read_by_category"])

# --- Page: Favoriten ---
elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs = user_favorites(username)
    if not favs:
        st.info("Du hast noch keine Favoriten.")
    else:
        for aid in favs:
            for cat,arts in NEWS_DB.items():
                for a in arts:
                    if a["id"]==aid:
                        render_card(a)

# --- Page: Einstellungen ---
elif page=="⚙️ Einstellungen":
    st.header("⚙️ Einstellungen")
    theme = st.selectbox("Theme wählen", ["light","dark","neon"], index=["light","dark","neon"].index(st.session_state.theme))
    st.session_state.theme = theme
    SETTINGS["theme"] = theme
    safe_save(FILES["settings"],SETTINGS)
    st.success("Einstellungen gespeichert. Bitte neu laden, falls nicht sofort sichtbar.")

# -------------------------
# Optional: Search functionality
# -------------------------
st.sidebar.subheader("🔍 Suche")
query = st.sidebar.text_input("Suchbegriff")
if query:
    st.sidebar.markdown("**Suchergebnisse:**")
    q_lower = query.lower()
    found = []
    for cat,arts in NEWS_DB.items():
        for a in arts:
            if q_lower in a["title"].lower() or q_lower in a["desc"].lower():
                found.append(a)
    if not found:
        st.sidebar.write("Keine Ergebnisse gefunden.")
    else:
        for a in found[:10]:
            st.sidebar.write(f"- {a['title']} ({a['date']})")
