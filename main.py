# -*- coding: utf-8 -*-
"""
Lumina News v5.0 - Streamlit Edition mit NewsAPI.org & längere Zusammenfassungen
"""
import streamlit as st
import requests, json, re
from datetime import datetime
from collections import Counter

# ----------------------------
# API Key (NewsAPI.org)
# ----------------------------
API_KEY = "64457577c9a14eb9a846b69dcae0d659"

# ----------------------------
# Kategorien
# ----------------------------
CATEGORIES = ["business", "technology", "sports", "politics", "world", "health", "science"]

# ----------------------------
# Cache & Favoriten
# ----------------------------
CACHE_FILE = "news_cache.json"
FAV_FILE = "favorites.json"

def load_cache():
    try:
        with open(CACHE_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"articles": {}, "last_update": ""}

def save_cache(data):
    try:
        with open(CACHE_FILE,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False, indent=2)
    except:
        st.warning("Cache konnte nicht gespeichert werden.")

def load_favorites():
    try:
        with open(FAV_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_favorites(favs):
    try:
        with open(FAV_FILE,"w",encoding="utf-8") as f:
            json.dump(favs,f,ensure_ascii=False, indent=2)
    except:
        st.warning("Favoriten konnten nicht gespeichert werden.")

CACHE = load_cache()
FAVORITES = load_favorites()

# ----------------------------
# Zusammenfassung: 6-7 Sätze
# ----------------------------
SENTENCE_RE = re.compile(r'(?<=[.!?]) +')

def summarize_long(text, max_sentences=7):
    if not text:
        return "Keine Beschreibung verfügbar."
    sentences = SENTENCE_RE.split(text)
    return " ".join(sentences[:max_sentences])

# ----------------------------
# News von API
# ----------------------------
def fetch_news(category):
    url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&pageSize=10&apiKey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("status")=="ok":
            articles=[]
            for a in data.get("articles",[]):
                articles.append({
                    "title": a.get("title",""),
                    "desc": a.get("description","") or "",
                    "content": a.get("content","") or "",
                    "date": a.get("publishedAt","")[:10],
                    "url": a.get("url","")
                })
            # cache pro Kategorie
            CACHE["articles"][category] = articles
            CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_cache(CACHE)
            return articles
    except:
        st.warning("API konnte nicht geladen werden. Zeige letzte gespeicherte News.")
    return CACHE.get("articles",{}).get(category, [])

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v5.0", layout="wide")
st.title("🌐 Lumina News v5.0")

# ----------------------------
# Sidebar Navigation
# ----------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Gehe zu:", ["🏠 Home", "📚 Kategorien", "⭐ Favoriten"])

# ----------------------------
# Favoriten Management
# ----------------------------
def add_favorite(article):
    aid = article["url"]
    if aid not in FAVORITES:
        FAVORITES[aid] = article
        save_favorites(FAVORITES)
        st.success("Zur Favoritenliste hinzugefügt!")

def remove_favorite(article):
    aid = article["url"]
    if aid in FAVORITES:
        del FAVORITES[aid]
        save_favorites(FAVORITES)
        st.info("Aus Favoriten entfernt!")

# ----------------------------
# Helper: render News Card
# ----------------------------
def render_card(article, show_fav=True):
    st.markdown(f"**[{article['title']}]({article['url']})**")
    desc_text = article.get("desc","") or article.get("content","")
    st.markdown(summarize_long(desc_text))
    if show_fav:
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("★ Favorit", key=f"fav-{article['url']}"):
                add_favorite(article)
                st.experimental_rerun()
        with col2:
            if st.button("✖ Entfernen", key=f"unfav-{article['url']}"):
                remove_favorite(article)
                st.experimental_rerun()
    st.markdown("---")

# ----------------------------
# Page: Home
# ----------------------------
if page=="🏠 Home":
    st.header("🏠 Home — Je eine News pro Kategorie")
    for cat in CATEGORIES:
        st.subheader(cat.capitalize())
        news_list = fetch_news(cat)
        if news_list:
            render_card(news_list[0], show_fav=True)
        else:
            st.write("Keine News verfügbar.")

# ----------------------------
# Page: Kategorien
# ----------------------------
elif page=="📚 Kategorien":
    st.header("📚 Kategorien")
    selected_cat = st.selectbox("Kategorie wählen:", CATEGORIES)
    news_list = fetch_news(selected_cat)
    if news_list:
        for article in news_list:
            render_card(article)
    else:
        st.write("Keine News verfügbar.")

# ----------------------------
# Page: Favoriten
# ----------------------------
elif page=="⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    if FAVORITES:
        for aid, article in FAVORITES.items():
            render_card(article, show_fav=True)
    else:
        st.info("Keine Favoriten. Klicke auf ★ bei einer News, um sie hier zu speichern.")

st.markdown(f"*Letztes Update: {CACHE.get('last_update','Nie')}*")
