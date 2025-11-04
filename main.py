# -*- coding: utf-8 -*-
"""
Lumina News v2.6 - Offline Streamlit Edition
Funktionen:
- Login / Registrierung (offline, users.json)
- Favoriten / Lesezeichen
- Theme: Light / Dark / Neon
- Home mit animiertem Startbanner & personalisierten Empfehlungen
- Sidebar Navigation einspaltig
- Einstellungen (Top-News pro Kategorie, Theme)
- Offline Text Analyzer: Sentiment, Headline-Score, Summary
"""
import streamlit as st
import json
import os
import re
from collections import Counter

# ----------------------------
# File paths
# ----------------------------
USERS_FILE = "users.json"
FAV_FILE = "favorites.json"
SETTINGS_FILE = "settings.json"

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
# Init persistent files
# ----------------------------
if not os.path.exists(USERS_FILE):
    safe_save(USERS_FILE, {"admin": "1234"})
if not os.path.exists(FAV_FILE):
    safe_save(FAV_FILE, {})
if not os.path.exists(SETTINGS_FILE):
    safe_save(SETTINGS_FILE, {"theme": "light", "home_count_each": 2})

USERS = safe_load(USERS_FILE, {"admin": "1234"})
FAVORITES = safe_load(FAV_FILE, {})
SETTINGS = safe_load(SETTINGS_FILE, {"theme": "light", "home_count_each": 2})

# ----------------------------
# Offline News DB (placeholder)
# ----------------------------
# Du kannst hier deine Nachrichten später einfügen
NEWS_DB = {
    "Powi": [], "Wirtschaft": [], "Politik": [],
    "Sport": [], "Technologie": [], "Weltweit": [], "Allgemein": []
}
CATEGORIES = list(NEWS_DB.keys())

# ----------------------------
# Text Analyzer
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+", flags=re.UNICODE)
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei","hat","haben","wird","werden","nicht","oder","aber","wir","ich","du","er","sie","es","dem","den","des"])

def tokenize(text):
    return [t.lower() for t in WORD_RE.findall(text) if t.lower() not in STOPWORDS and len(t) > 2]

def extractive_summary(text, max_sentences=2):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    tokens = tokenize(text)
    freq = Counter(tokens)
    sent_scores = []
    for s in sentences:
        sent_scores.append((sum(freq.get(w,0) for w in tokenize(s)), s))
    sent_scores.sort(key=lambda x: x[0], reverse=True)
    return " ".join([s for _,s in sent_scores[:max_sentences]])

def sentiment_score(text):
    pos=neg=0
    t = text.lower()
    POS = ["erfolgreich","gewinnt","stark","besser","stabil","positiv","lob","begeistert","sieg","förder"]
    NEG = ["krise","verlust","scheit","problem","kritik","sorgen","unsicher","verzöger","einbruch","attack"]
    for p in POS: pos += t.count(p)
    for n in NEG: neg += t.count(n)
    if pos+neg==0: return 0.0
    return round((pos-neg)/(pos+neg),3)

def classify_sentiment_label(score):
    if score>0.2: return "Positiv"
    if score<-0.2: return "Negativ"
    return "Neutral"

def headline_score(article):
    base = article.get("importance",3)*15
    s = sentiment_score(article.get("title","")+" "+article.get("desc",""))
    base += s*10
    l = len(tokenize(article.get("title","")))
    base += max(0,8-abs(l-10))
    return int(max(0,min(100,base)))

# ----------------------------
# Favorites
# ----------------------------
def add_favorite(user, aid):
    favs = FAVORITES.get(user,[])
    if aid not in favs: favs.append(aid)
    FAVORITES[user] = favs
    safe_save(FAV_FILE,FAVORITES)

def remove_favorite(user, aid):
    favs = FAVORITES.get(user,[])
    if aid in favs: favs.remove(aid)
    FAVORITES[user] = favs
    safe_save(FAV_FILE,FAVORITES)

def user_favorites(user):
    return FAVORITES.get(user,[])

def user_profile_stats(user):
    favs = user_favorites(user)
    cat_counter = Counter()
    for fid in favs:
        for cat,lst in NEWS_DB.items():
            for a in lst:
                if a.get("id")==fid: cat_counter[cat]+=1
    return {"favorites_total":len(favs),"fav_by_category":dict(cat_counter)}

# ----------------------------
# Streamlit Config
# ----------------------------
st.set_page_config(page_title="Lumina News v2.6", layout="wide")
if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=SETTINGS.get("theme","light")
if "last_read" not in st.session_state: st.session_state.last_read=[]

# ----------------------------
# Themes
# ----------------------------
THEMES={
    "light":{"bg":"#f7f9fc","text":"#0b1a2b","card":"white","header":"#004aad"},
    "dark":{"bg":"#0b1220","text":"#e6eef8","card":"#0f1724","header":"#66b2ff"},
    "neon":{"bg":"#0b0c1a","text":"#39ff14","card":"#111133","header":"#ff00ff","glow":"0 0 8px #ff00ff,0 0 12px #39ff14"}
}

def inject_css():
    t=THEMES.get(st.session_state.theme, THEMES["light"])
    glow=t.get("glow","0 0 2px rgba(0,0,0,0.2)")
    css=f"""
    body {{background-color:{t['bg']}; color:{t['text']}}}
    .card {{background:{t['card']}; border-radius:8px; padding:12px; margin-bottom:12px; box-shadow:{glow}}}
    .header {{color:{t['header']}; text-shadow:{glow}}}
    .small {{color:#888; font-size:12px;}}
    .button-primary {{background-color:{t['header']}; color:white; border-radius:6px; padding:6px 12px;}}
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

inject_css()

# ----------------------------
# Authentication
# ----------------------------
if not st.session_state.logged_in:
    st.title("Lumina News v2.6 🔐 Login/Register")
    lcol,rcol=st.columns(2)
    with lcol:
        st.subheader("Anmelden")
        with st.form("login_form"):
            uname=st.text_input("Benutzername")
            pwd=st.text_input("Passwort", type="password")
            submit=st.form_submit_button("Einloggen")
            if submit:
                users=safe_load(USERS_FILE,{"admin":"1234"})
                if users.get(uname)==pwd:
                    st.session_state.logged_in=True
                    st.session_state.username=uname
                    st.success(f"Willkommen, {uname}!")
                    st.experimental_rerun()
                else:
                    st.error("Falsche Zugangsdaten.")
    with rcol:
        st.subheader("Registrieren")
        with st.form("reg_form"):
            r_uname=st.text_input("Neuer Benutzername")
            r_pwd=st.text_input("Neues Passwort", type="password")
            reg_submit=st.form_submit_button("Registrieren")
            if reg_submit:
                users=safe_load(USERS_FILE,{"admin":"1234"})
                if not r_uname or not r_pwd:
                    st.warning("Bitte Benutzername und Passwort angeben.")
                elif r_uname in users:
                    st.warning("Benutzer existiert bereits.")
                else:
                    users[r_uname]=r_pwd
                    safe_save(USERS_FILE,users)
                    st.success("Registrierung erfolgreich! Bitte anmelden.")
    st.stop()

# ----------------------------
# Sidebar Navigation
# ----------------------------
username=st.session_state.username
st.sidebar.title(f"👤 {username}")
pages=["🏠 Home","🔎 Suche","📚 Kategorien","⭐ Favoriten","⚙️ Einstellungen"]
page=st.sidebar.radio("Navigation", pages)

# ----------------------------
# Helper: render news card
# ----------------------------
def render_news_card(article, category, show_actions=True):
    title=article.get("title","")
    desc=article.get("desc","")
    date=article.get("date","")
    imp=article.get("importance",3)
    aid=article.get("id","")
    score=headline_score(article)
    s_score=sentiment_score(desc)
    s_label=classify_sentiment_label(s_score)
    summary=extractive_summary(desc)
    favs=user_favorites(username)
    is_fav=aid in favs
    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"**{title}** <span class='small'>{date} • Wichtigkeit: {imp} • Score: {score} • Stimmung: {s_label}</span>")
    st.markdown(f"<div>{summary}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='margin-top:4px;color:#888;'>Volltext: {desc}</div>", unsafe_allow_html=True)
    if show_actions:
        cols=st.columns([1,1,1,6])
        with cols[0]:
            if st.button("Lesen", key=f"read-{aid}"):
                st.session_state.last_read.insert(0,aid)
                if len(st.session_state.last_read)>50: st.session_state.last_read=st.session_state.last_read[:50]
                st.experimental_rerun()
        with cols[1]:
            if not is_fav and st.button("★ Favorit", key=f"fav-{aid}"):
                add_favorite(username,aid)
                st.success("Zur Favoritenliste hinzugefügt")
                st.experimental_rerun()
        with cols[2]:
            if is_fav and st.button("✖ Entfernen", key=f"unfav-{aid}"):
                remove_favorite(username,aid)
                st.info("Aus Favoriten entfernt")
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# Pages
# ----------------------------
if page=="🏠 Home":
    st.header("🏠 Home — Top & Empfohlene News")
    st.subheader("Startbanner (animiert, Neon Cards)")
    # Beispiel-Animation: horizontale scrollbare Top-Cards
    st.markdown("""
    <div style='display:flex; overflow-x:auto; gap:12px; padding:8px;'>
        <div class='card' style='min-width:220px;'>🚀 News 1</div>
        <div class='card' style='min-width:220px;'>🌐 News 2</div>
        <div class='card' style='min-width:220px;'>📈 News 3</div>
        <div class='card' style='min-width:220px;'>⚡ News 4</div>
        <div class='card' style='min-width:220px;'>🎯 News 5</div>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("Empfohlene für dich")
    # Personalisiert: letzte Favoriten oder zuletzt gelesen
    recs=[]
    for aid in st.session_state.last_read[:10]:
        for cat,lst in NEWS_DB.items():
            for a in lst:
                if a.get("id")==aid: recs.append((a,cat))
    for a,c in recs: render_news_card(a,c)

elif page=="🔎 Suche":
    st.header("🔎 Suche")
    query=st.text_input("Suchbegriff")
    mood=st.selectbox("Stimmung filtern",["Alle","Positiv","Neutral","Negativ"])
    min_imp=st.slider("Min. Wichtigkeit",1,5,1)
    if query:
        results=[]
        for cat,lst in NEWS_DB.items():
            for a in lst:
                text=a.get("title","")+" "+a.get("desc","")
                if query.lower() in text.lower() and a.get("importance",3)>=min_imp:
                    s_label=classify_sentiment_label(sentiment_score(text))
                    if mood=="Alle" or mood==s_label: results.append((a,cat))
        if results:
            st.subheader(f"{len(results)} Ergebnisse")
            for a,c in results: render_news_card(a,c)
        else:
            st.info("Keine Ergebnisse gefunden.")

elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    cat_sel=st.selectbox("Kategorie wählen", CATEGORIES)
    lst=NEWS_DB.get(cat_sel,[])
    if lst:
        for a in lst: render_news_card(a,cat_sel)
    else:
        st.info("Keine Nachrichten in dieser Kategorie.")

elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs=user_favorites(username)
    if favs:
        for fid in favs:
            found=False
            for cat,lst in NEWS_DB.items():
                for a in lst:
                    if a.get("id")==fid: render_news_card(a,cat); found=True
            if not found:
                st.markdown(f"<div class='card'>Artikel {fid} nicht gefunden.</div>", unsafe_allow_html=True)
    else:
        st.info("Keine Favoriten gespeichert.")

elif page=="⚙️ Einstellungen":
    st.header("⚙️ Einstellungen")
    theme_sel=st.selectbox("Theme auswählen", ["light","dark","neon"], index=["light","dark","neon"].index(st.session_state.theme))
    top_count=st.number_input("Top-News pro Kategorie", min_value=1, max_value=10, value=SETTINGS.get("home_count_each",2))
    if st.button("Speichern"):
        SETTINGS["theme"]=theme_sel
        SETTINGS["home_count_each"]=top_count
        safe_save(SETTINGS_FILE, SETTINGS)
        st.session_state.theme=theme_sel
        st.success("Einstellungen gespeichert")
        st.experimental_rerun()
