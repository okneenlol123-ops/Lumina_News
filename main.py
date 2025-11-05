# -*- coding: utf-8 -*-
"""
Lumina News v4.0 - Streamlit Edition mit NewsAPI.org & Zusammenfassung
"""
import streamlit as st
import requests, json
from datetime import datetime
import re

# ----------------------------
# API Key (NewsAPI.org)
# ----------------------------
API_KEY = "64457577c9a14eb9a846b69dcae0d659"

# ----------------------------
# Kategorien
# ----------------------------
CATEGORIES = ["business", "technology", "sports", "politics", "world", "health", "science"]

# ----------------------------
# Safe JSON cache (optional)
# ----------------------------
CACHE_FILE = "news_cache.json"
def load_cache():
    try:
        with open(CACHE_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"articles": [], "last_update": ""}
def save_cache(data):
    try:
        with open(CACHE_FILE,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False, indent=2)
    except:
        st.warning("Cache konnte nicht gespeichert werden.")

CACHE = load_cache()

# ----------------------------
# Utility: kurze Zusammenfassung (10 Wörter)
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
def summarize(text, word_count=10):
    words = WORD_RE.findall(text)
    return " ".join(words[:word_count]) + ("..." if len(words)>word_count else "")

# ----------------------------
# News laden von API
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
                    "date": a.get("publishedAt","")[:10],
                    "url": a.get("url","")
                })
            # update cache
            CACHE["articles"] = articles
            CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_cache(CACHE)
            return articles
    except:
        st.warning("API konnte nicht geladen werden. Zeige letzte gespeicherte News.")
    return CACHE.get("articles", [])

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v4.0", layout="wide")

st.title("🌐 Lumina News v4.0")

# Spalten: links Kategorien, rechts News
col1, col2 = st.columns([1,3])

with col1:
    st.subheader("Kategorien")
    selected_cat = st.radio("Wähle Kategorie:", ["All"] + CATEGORIES)

with col2:
    st.subheader("Neueste News")
    cats_to_fetch = CATEGORIES if selected_cat=="All" else [selected_cat]
    for cat in cats_to_fetch:
        st.markdown(f"### {cat.capitalize()}")
        news_list = fetch_news(cat)
        if not news_list:
            st.write("Keine News verfügbar.")
        else:
            for n in news_list:
                st.markdown(f"**[{n['title']}]({n['url']})**")
                st.markdown(f"{summarize(n['desc'], 10)}")
                st.markdown("---")

st.markdown(f"*Letztes Update: {CACHE.get('last_update','Nie')}*")
