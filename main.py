# -*- coding: utf-8 -*-
"""
Lumina News v2.7 - Offline Streamlit Edition mit Demo-News
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
# JSON helpers
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
# Offline News DB - Demo Nachrichten
# ----------------------------
NEWS_DB = {
    "Powi": [
        {"id":"powi1","title":"Neue Bildungsinitiative gestartet","desc":"Bundesweit starten Programme für Medienkompetenz in Schulen.","date":"2025-11-01","importance":5},
        {"id":"powi2","title":"Schulsozialarbeit gestärkt","desc":"Mehr Ressourcen für psychosoziale Unterstützung in Bildungseinrichtungen.","date":"2025-10-15","importance":4},
    ],
    "Wirtschaft": [
        {"id":"wi1","title":"Startups boomen in der Region","desc":"Innovative Projekte erhalten Förderungen und Investitionen.","date":"2025-10-20","importance":4},
        {"id":"wi2","title":"Exportbranche wächst","desc":"Unternehmen berichten von steigender Nachfrage im Ausland.","date":"2025-09-30","importance":3},
    ],
    "Politik": [
        {"id":"po1","title":"Koalitionsgespräche erfolgreich","desc":"Parteien einigen sich auf neue Klimaziele.","date":"2025-11-02","importance":5},
        {"id":"po2","title":"Transparenzgesetz in Diskussion","desc":"Neue Regeln für Lobbykontakte sollen verabschiedet werden.","date":"2025-10-25","importance":4},
    ],
    "Sport": [
        {"id":"sp1","title":"Nationalteam gewinnt Qualifikation","desc":"Ein spannendes Spiel endet mit knapper Führung.","date":"2025-10-31","importance":5},
        {"id":"sp2","title":"Bundesligist investiert in Nachwuchs","desc":"Akademieprogramme werden ausgebaut und modernisiert.","date":"2025-09-12","importance":3},
    ],
    "Technologie": [
        {"id":"te1","title":"Neuer KI-Chip vorgestellt","desc":"Effizienzsteigerung für Cloud- und Edge-Anwendungen.","date":"2025-10-30","importance":5},
        {"id":"te2","title":"5G Privatnetze für Industrie","desc":"Schnelle und sichere Produktionsanwendungen werden möglich.","date":"2025-08-20","importance":4},
    ],
    "Weltweit": [
        {"id":"we1","title":"Gipfeltreffen zu Klimazielen","desc":"Internationale Staaten vereinbaren Maßnahmen gegen Emissionen.","date":"2025-10-05","importance":5},
        {"id":"we2","title":"Friedensgespräche beginnen","desc":"Diplomaten initiieren Gespräche für Deeskalation in Krisengebieten.","date":"2025-09-22","importance":4},
    ],
    "Allgemein": [
        {"id":"al1","title":"Bahn verbessert Pünktlichkeit","desc":"Wartungszyklen führen zu leicht besseren Werten bei Zügen.","date":"2025-10-01","importance":3},
        {"id":"al2","title":"Grünflächen in Städten erweitert","desc":"Kommunen investieren in Parks und städtische Begrünung.","date":"2025-09-15","importance":2},
    ],
}

CATEGORIES = list(NEWS_DB.keys())

# ----------------------------
# Text Analyzer
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+", flags=re.UNICODE)
STOPWORDS = set(["und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei","hat","haben","wird","werden","nicht","oder","aber","wir","ich","du","er","sie","es","dem","den","des"])

def tokenize(text):
    return [t.lower() for t in WORD_RE.findall(text) if t.lower() not in STOPWORDS and len(t)>2]

def extractive_summary(text,max_sentences=2):
    sentences=re.split(r'(?<=[.!?])\s+',text.strip())
    tokens=tokenize(text)
    freq=Counter(tokens)
    scored=[]
    for s in sentences: scored.append((sum(freq.get(w,0) for w in tokenize(s)),s))
    scored.sort(key=lambda x:x[0],reverse=True)
    return " ".join([s for _,s in scored[:max_sentences]])

def sentiment_score(text):
    pos=neg=0
    t=text.lower()
    POS=["erfolgreich","gewinnt","stark","besser","stabil","positiv","lob","begeistert","sieg","förder"]
    NEG=["krise","verlust","scheit","problem","kritik","sorgen","unsicher","verzöger","einbruch","attack"]
    for p in POS: pos+=t.count(p)
    for n in NEG: neg+=t.count(n)
    if pos+neg==0: return 0.0
    return round((pos-neg)/(pos+neg),3)

def classify_sentiment_label(score):
    if score>0.2: return "Positiv"
    if score<-0.2: return "Negativ"
    return "Neutral"

def headline_score(article):
    base=article.get("importance",3)*15
    s=sentiment_score(article.get("title","")+" "+article.get("desc",""))
    base+=s*10
    l=len(tokenize(article.get("title","")))
    base+=max(0,8-abs(l-10))
    return int(max(0,min(100,base)))

# ----------------------------
# Favorites
# ----------------------------
def add_favorite(user,aid):
    favs=FAVORITES.get(user,[])
    if aid not in favs: favs.append(aid)
    FAVORITES[user]=favs
    safe_save(FAV_FILE,FAVORITES)

def remove_favorite(user,aid):
    favs=FAVORITES.get(user,[])
    if aid in favs: favs.remove(aid)
    FAVORITES[user]=favs
    safe_save(FAV_FILE,FAVORITES)

def user_favorites(user):
    return FAVORITES.get(user,[])

def user_profile_stats(user):
    favs=user_favorites(user)
    cat_counter=Counter()
    for fid in favs:
        for cat,lst in NEWS_DB.items():
            for a in lst:
                if a.get("id")==fid: cat_counter[cat]+=1
    return {"favorites_total":len(favs),"fav_by_category":dict(cat_counter)}

# ----------------------------
# Streamlit Config
# ----------------------------
st.set_page_config(page_title="Lumina News v2.7", layout="wide")
if "username" not in st.session_state: st.session_state.username=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "theme" not in st.session_state: st.session_state.theme=SETTINGS.get("theme","light")
if "last_read" not in st.session_state: st.session_state.last_read=[]

# ----------------------------
# Themes & CSS
# ----------------------------
THEMES={
    "light":{"bg":"#f7f9fc","text":"#0b1a2b","card":"white","header":"#004aad"},
    "dark":{"bg":"#0b1220","text":"#e6eef8","card":"#0f1724","header":"#66b2ff"},
    "neon":{"bg":"#0b0c1a","text":"#fff","card":"#1a0033","header":"#ff00ff"},
}

def inject_css():
    t=THEMES.get(st.session_state.theme,THEMES["light"])
    css=f"""
    body{{background-color:{t['bg']};color:{t['text']};}}
    .card{{background:{t['card']};border-radius:10px;padding:12px;margin-bottom:12px;box-shadow:0 0 15px rgba(0,0,0,0.4);transition:0.3s;}}
    .card:hover{{box-shadow:0 0 25px rgba(255,0,255,0.7);transform:scale(1.02);}}
    .header{{color:{t['header']};font-size:28px;font-weight:bold;}}
    .small{{color:#aaa;font-size:12px;}}
    .banner{{font-size:36px;font-weight:bold;color:#ff00ff;text-shadow:0 0 10px #ff00ff,0 0 20px #ff00ff;overflow-x:auto;white-space:nowrap;}}
    """
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)

inject_css()

# ----------------------------
# Authentication
# ----------------------------
if not st.session_state.logged_in:
    col1,col2=st.columns(2)
    with col1:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            uname=st.text_input("Benutzername",key="login_user")
            pwd=st.text_input("Passwort",type="password",key="login_pass")
            if st.form_submit_button("Einloggen"):
                users=safe_load(USERS_FILE,{"admin":"1234"})
                if users.get(uname)==pwd:
                    st.session_state.logged_in=True
                    st.session_state.username=uname
                    st.success(f"Willkommen {uname}!")
                else: st.error("Falsche Zugangsdaten.")
    with col2:
        st.subheader("🆕 Registrierung")
        with st.form("reg_form"):
            r_uname=st.text_input("Neuer Benutzername",key="reg_user")
            r_pwd=st.text_input("Passwort",type="password",key="reg_pass")
            if st.form_submit_button("Registrieren"):
                users=safe_load(USERS_FILE,{"admin":"1234"})
                if not r_uname or not r_pwd: st.warning("Benutzername & Passwort eingeben.")
                elif r_uname in users: st.warning("Benutzer existiert bereits.")
                else:
                    users[r_uname]=r_pwd
                    safe_save(USERS_FILE,users)
                    st.success("Registrierung erfolgreich! Bitte anmelden.")
    st.stop()

username=st.session_state.username

# ----------------------------
# Sidebar Navigation
# ----------------------------
st.sidebar.title(f"👤 {username}")
pages=["🏠 Home","🔎 Suche","📚 Kategorien","⭐ Favoriten","⚙️ Einstellungen"]
page=st.sidebar.radio("Navigation",pages)

# ----------------------------
# Helper: render news
# ----------------------------
def render_news_card(article,category):
    aid=article.get("id")
    favs=user_favorites(username)
    is_fav=aid in favs
    s_score=sentiment_score(article.get("desc",""))
    s_label=classify_sentiment_label(s_score)
    summary=extractive_summary(article.get("desc",""))
    st.markdown(f"<div class='card'>**{article['title']}** <span class='small'>{article['date']} • Kategorie: {category} • Wichtigkeit: {article['importance']} • Sentiment: {s_label}</span>",unsafe_allow_html=True)
    st.markdown(f"{summary}",unsafe_allow_html=True)
    cols=st.columns([1,1])
    with cols[0]:
        if st.button("★ Favorit" if not is_fav else "✖ Entfernen",key=f"fav-{aid}"):
            if not is_fav: add_favorite(username,aid)
            else: remove_favorite(username,aid)
            st.experimental_rerun()
    with cols[1]:
        if st.button("Lesen",key=f"read-{aid}"):
            st.session_state.last_read.insert(0,aid)
            if len(st.session_state.last_read)>50: st.session_state.last_read=st.session_state.last_read[:50]
            st.experimental_rerun()
    st.markdown("</div>",unsafe_allow_html=True)

# ----------------------------
# Pages
# ----------------------------
if page=="🏠 Home":
    st.markdown("<div class='banner'>🌟 Willkommen bei Lumina News v2.7 🌟</div>",unsafe_allow_html=True)
    st.subheader("Top Nachrichten")
    for cat in CATEGORIES:
        for a in NEWS_DB[cat][:SETTINGS.get("home_count_each",2)]: render_news_card(a,cat)
    st.subheader("Empfohlene für dich")
    favcats=list(user_profile_stats(username).get("fav_by_category",{}).keys())
    recommended=[]
    if favcats:
        for fc in favcats:
            recommended.extend([(a,fc) for a in NEWS_DB.get(fc,[])])
    for a,c in recommended[:6]: render_news_card(a,c)

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
    top_count=st.number_input("Top-News pro Kategorie",1,10,value=SETTINGS.get("home_count_each",2))
    if st.button("Speichern"):
        SETTINGS["theme"]=theme_sel
        SETTINGS["home_count_each"]=top_count
        safe_save(SETTINGS_FILE,SETTINGS)
        st.session_state.theme=theme_sel
        inject_css()
        st.success("Gespeichert")
        st.experimental_rerun()
