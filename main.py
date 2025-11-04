# -*- coding: utf-8 -*-
"""
Lumina News v2.0 - Streamlit Offline Edition
Features:
 - Login / Registrierung (users.json)
 - Theme (light/dark) Umschaltbar (settings.json)
 - Home mit wichtigsten Artikeln & personalisiertem Feed
 - 7 Kategorien, jede mit News-Karten
 - Offline KI: Extractive Summary, Sentiment, Headline-Scoring
 - Favoriten / Lesezeichen (favorites.json, pro user)
 - Suche + Filter (Stimmung, Wichtigkeit)
 - Profilseite mit Statistiken
 - Keine externen APIs erforderlich (offline)
"""
import streamlit as st
import json
import os
import math
import re
from datetime import datetime
from collections import Counter, defaultdict

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
    except Exception:
        pass
    return default

def safe_save(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Fehler beim Speichern von {path}: {e}")

# ----------------------------
# Initialize persistent files if missing
# ----------------------------
if not os.path.exists(USERS_FILE):
    safe_save(USERS_FILE, {"admin": "1234"})  # default test account

if not os.path.exists(FAV_FILE):
    safe_save(FAV_FILE, {})

if not os.path.exists(SETTINGS_FILE):
    safe_save(SETTINGS_FILE, {"theme": "light", "home_count_each": 2})

# ----------------------------
# Load persistent state
# ----------------------------
USERS = safe_load(USERS_FILE, {"admin": "1234"})
FAVORITES = safe_load(FAV_FILE, {})
GLOBAL_SETTINGS = safe_load(SETTINGS_FILE, {"theme": "light", "home_count_each": 2})

# ----------------------------
# News dataset (offline, realistic placeholders)
# 7 categories, 10 articles each (compact descriptions)
# ----------------------------
def build_news_db():
    # For brevity, titles are realistic, descriptions are 3-5 sentences.
    db = {
        "Powi": [
            {"id":"powi-1","title":"Neue Lehrpläne fokussieren Medienkompetenz",
             "desc":"Das Bildungsministerium stellt neue Lehrpläne vor, die Medienkompetenz und kritisches Denken stärker betonen. "
                     "Lehrkräfte sollen in didaktischen Konzepten geschult werden. "
                     "Pilotphasen beginnen im nächsten Schuljahr. "
                     "Elternvertretungen wurden eingebunden.",
             "date":"2025-10-15","importance":5},
            {"id":"powi-2","title":"Schulsozialarbeit ausgeweitet",
             "desc":"Ressourcen für Schulsozialarbeit werden erhöht, um psychosoziale Unterstützung zu stärken. "
                     "Regionale Programme setzen auf Prävention. "
                     "Kooperationen mit Jugendämtern sind geplant.",
             "date":"2025-09-27","importance":4},
            {"id":"powi-3","title":"Digitalpakt: Ausstattung für Schulen",
             "desc":"Ein neues Förderpaket liefert Hardware und Netzwerkausbau für Schulen. "
                     "Datenschutz und Lehrkonzepte sind zentrale Bestandteile.",
             "date":"2025-08-05","importance":4},
            {"id":"powi-4","title":"Berufsorientierung wird Pflichtmodul",
             "desc":"Gymnasien führen verpflichtende Module zur Berufsorientierung ein. "
                     "Praktika und Bewerbungscoaching werden intensiviert.",
             "date":"2025-07-11","importance":3},
            {"id":"powi-5","title":"MINT-Förderung für Jugendliche",
             "desc":"Regionale MINT-Programme bündeln Mentoring, Wettbewerbe und Projektarbeit. "
                     "Ziel ist langfristige Fachkräftesicherung.",
             "date":"2025-06-02","importance":4},
            {"id":"powi-6","title":"Hybridunterricht: Erfahrungen aus Pilotprojekten",
             "desc":"Pilotprojekte zum Hybridunterricht zeigen sowohl Chancen als auch technische Herausforderungen. "
                     "Lehrkräfte berichten von erhöhter Flexibilität.",
             "date":"2025-11-03","importance":3},
            {"id":"powi-7","title":"Sprachförderung in Grundschulen intensiviert",
             "desc":"Zusätzliche Mittel fließen in Programme zur frühen Sprachförderung. "
                     "Fokus liegt auf mehrsprachigen Regionen.",
             "date":"2025-05-21","importance":3},
            {"id":"powi-8","title":"Wettbewerb: Nachhaltigkeitsprojekte an Schulen",
             "desc":"Schülerteams entwickeln Projekte zu Energieeinsparung und Recycling. "
                     "Gewinner erhalten Finanzierung und Mentoring.",
             "date":"2025-04-13","importance":2},
            {"id":"powi-9","title":"Schülervertretungen erhalten mehr Mitspracherechte",
             "desc":"Regelungen sehen stärkere Beteiligung der SV an Schulkonferenzen vor. "
                     "Pilotphasen werden evaluiert.",
             "date":"2025-03-30","importance":3},
            {"id":"powi-10","title":"Regionale Bildungszentren planen Kooperationen",
             "desc":"Kommunale Bildungszentren sollen vermehrt mit Unternehmen kooperieren. "
                     "Ziel ist praxisnahe Ausbildung.",
             "date":"2025-02-12","importance":2},
        ],
        "Wirtschaft": [
            {"id":"wi-1","title":"Industrieproduktion verzeichnet Aufschwung",
             "desc":"Die Industrie meldet ein moderates Wachstum, getrieben durch Maschinenbau und Exportnachfrage. "
                     "Unternehmen investieren in Automatisierung und Effizienz.",
             "date":"2025-10-20","importance":4},
            {"id":"wi-2","title":"Mittelstand setzt auf KI-Investitionen",
             "desc":"Viele mittelständische Unternehmen probieren KI-Pilotprojekte aus, um Prozesse zu optimieren. "
                     "Fördermittel erleichtern erste Schritte.",
             "date":"2025-09-05","importance":4},
            {"id":"wi-3","title":"Arbeitsmarkt zeigt robuste Entwicklung",
             "desc":"Die Arbeitslosenquote bleibt stabil. "
                     "Besonders IT, Pflege und Handwerk melden hohe Nachfrage.",
             "date":"2025-08-14","importance":3},
            {"id":"wi-4","title":"Inflation stabilisiert sich",
             "desc":"Preissteigerungen schwächten sich ab; Zentralbanken bleiben vorsichtig optimistisch.",
             "date":"2025-07-30","importance":4},
            {"id":"wi-5","title":"Startups erhalten neues Förderprogramm",
             "desc":"Ein Fördertopf unterstützt grüne Startups bei Skalierung und Internationalisierung.",
             "date":"2025-06-22","importance":3},
            {"id":"wi-6","title":"Exportbranche verbessert Logistik",
             "desc":"Unternehmen optimieren Lieferketten und setzen auf digitale Transparenz-Tools.",
             "date":"2025-05-12","importance":3},
            {"id":"wi-7","title":"Immobilienmarkt regional differenziert",
             "desc":"In Metropolen bleiben Preise hoch; Randregionen normalisieren sich langsam.",
             "date":"2025-04-01","importance":3},
            {"id":"wi-8","title":"Energieeffizienz auf der Agenda",
             "desc":"Fabriken investieren in Energiemanagementsysteme, um Kosten zu senken.",
             "date":"2025-03-18","importance":3},
            {"id":"wi-9","title":"Finanzbildung wird ausgeweitet",
             "desc":"Programme in Schulen sollen Alltagskompetenz stärken und frühzeitig Finanzwissen vermitteln.",
             "date":"2025-02-10","importance":2},
            {"id":"wi-10","title":"Nearshoring als Antwort auf Lieferkettenrisiken",
             "desc":"Unternehmen setzen auf diversifizierte Zuliefererstrukturen.",
             "date":"2025-01-05","importance":2},
        ],
        "Politik": [
            {"id":"po-1","title":"Koalitionsgespräche gehen in finale Phase",
             "desc":"Verhandlungen zu Klima und Finanzen erreichen Schlüsselmomente. "
                     "Parteien prüfen Kompromisslinien.",
             "date":"2025-11-01","importance":5},
            {"id":"po-2","title":"Transparenzgesetz diskutiert",
             "desc":"Debatten über Offenlegungspflichten für Lobbykontakte halten an.",
             "date":"2025-07-02","importance":4},
            {"id":"po-3","title":"Datenschutz und KI: neue Regeln",
             "desc":"Parlamentarische Beratungen zu Datenschutzanpassungen im KI-Kontext beginnen.",
             "date":"2025-05-19","importance":5},
            {"id":"po-4","title":"Kommunen erhalten Investitionshilfen",
             "desc":"Bundesmittel unterstützen kommunale Infrastruktur- und Digitalisierungsprojekte.",
             "date":"2025-10-18","importance":3},
            {"id":"po-5","title":"Innenpolitik: Cyberabwehr gestärkt",
             "desc":"Mehr Ressourcen fließen in Cyberabwehr und Ausbildung von Spezialisten.",
             "date":"2025-04-10","importance":4},
            {"id":"po-6","title":"Debatte um Wahlalter entflammt",
             "desc":"Diskussionen über mögliche Absenkung des Wahlalters finden auf kommunaler Ebene statt.",
             "date":"2025-03-03","importance":2},
            {"id":"po-7","title":"Rentenkommission veröffentlicht Zwischenbericht",
             "desc":"Erste Optionen für Reformen werden vorgestellt und öffentlich diskutiert.",
             "date":"2025-02-14","importance":4},
            {"id":"po-8","title":"Außenpolitik intensiviert Dialog",
             "desc":"Regelmäßige Treffen mit Nachbarstaaten sollen Kooperationen stärken.",
             "date":"2025-01-21","importance":3},
            {"id":"po-9","title":"Integration: Programme für Arbeitsmarktzugang",
             "desc":"Sprach- und Qualifizierungsangebote werden ausgebaut.",
             "date":"2025-06-25","importance":3},
            {"id":"po-10","title":"Sozialpolitik: Maßnahmen gegen Armut",
             "desc":"Regionale Projekte unterstützen vulnerable Gruppen und Familien.",
             "date":"2025-11-02","importance":3},
        ],
        "Sport": [
            {"id":"sp-1","title":"Nationalteam gewinnt wichtiges Qualifikationsspiel",
             "desc":"Das Team feierte einen knappen Sieg nach taktischer Disziplin. Fans und Trainer zeigen sich erfreut.",
             "date":"2025-10-31","importance":5},
            {"id":"sp-2","title":"Bundesligist investiert in Akademie",
             "desc":"Ein Club stärkt sein Nachwuchsprogramm mit neuen Trainingsmethoden.",
             "date":"2025-09-12","importance":3},
            {"id":"sp-3","title":"Olympia-Vorbereitung läuft planmäßig",
             "desc":"Athleten absolvieren intensive Trainingslager und Vorbereitungswettkämpfe.",
             "date":"2025-08-01","importance":4},
            {"id":"sp-4","title":"Tennis-Turnier mit Überraschungssieg",
             "desc":"Ein Newcomer sichert sich den Titel und sorgt für Medieninteresse.",
             "date":"2025-07-18","importance":3},
            {"id":"sp-5","title":"Radsport: Etappensieg verändert Gesamtwertung",
             "desc":"Eine dramatische Etappe veränderte die Entscheidung in der Gesamtwertung.",
             "date":"2025-04-22","importance":3},
            {"id":"sp-6","title":"Leichtathletik: Nachwuchsmeeting begeistert",
             "desc":"Junge Athleten erzielten persönliche Bestleistungen in mehreren Disziplinen.",
             "date":"2025-03-30","importance":2},
            {"id":"sp-7","title":"Eishockey-Aufsteiger erreicht Playoffs",
             "desc":"Der Aufsteiger schaffte überraschend den Einzug in die Playoffs.",
             "date":"2025-02-12","importance":2},
            {"id":"sp-8","title":"Lokalderby begeistert Fans",
             "desc":"Ein traditionsreiches Derby sorgte für volle Stadien und Emotionen.",
             "date":"2025-01-18","importance":3},
            {"id":"sp-9","title":"Handball: Auftaktsieg stärkt Moral",
             "desc":"Die Mannschaft startete erfolgreich in die Saison und zeigte defensive Stabilität.",
             "date":"2025-05-09","importance":2},
            {"id":"sp-10","title":"Basketball: Entscheidungsspiel spannend",
             "desc":"Ein knappes Spiel entschied die Platzierungen in der Liga.",
             "date":"2025-06-11","importance":3},
        ],
        "Technologie": [
            {"id":"te-1","title":"Neuer KI-Chip verspricht Effizienz",
             "desc":"Ein Halbleiterhersteller kündigt einen energieeffizienten KI-Chip an, der Cloud- und Edge-Workloads verbessern soll.",
             "date":"2025-10-30","importance":5},
            {"id":"te-2","title":"5G-Privatnetze für Industrie",
             "desc":"Private 5G-Netze unterstützen Produktionsanwendungen mit niedriger Latenz.",
             "date":"2025-08-20","importance":4},
            {"id":"te-3","title":"Quantenforschung macht Schritte voran",
             "desc":"Verbesserte Fehlerkorrektur erhöht Stabilität und Chancen für größere Qubit-Systeme.",
             "date":"2025-07-09","importance":5},
            {"id":"te-4","title":"Open-Source-Tool hilft Testautomatisierung",
             "desc":"Community-Projekte liefern modulare Lösungen für CI/CD und Testpipelines.",
             "date":"2025-06-16","importance":3},
            {"id":"te-5","title":"Cloudanbieter präsentieren Nachhaltigkeits-Tools",
             "desc":"Tools zur Messung von Workload-Emissionen sollen Kunden bei ESG-Reporting helfen.",
             "date":"2025-03-12","importance":3},
            {"id":"te-6","title":"Bildverarbeitung verbessert Diagnostik",
             "desc":"KI-Modelle unterstützen Ärztinnen und Ärzte bei der Bilddiagnostik als Assistenzsysteme.",
             "date":"2025-02-25","importance":5},
            {"id":"te-7","title":"Edge-Computing gewinnt an Bedeutung",
             "desc":"Viele Anwendungen verlagern Verarbeitung an die Edge, um Latenz zu verringern.",
             "date":"2025-01-16","importance":3},
            {"id":"te-8","title":"Zero-Trust-Ansätze setzen sich durch",
             "desc":"Unternehmen modernisieren Sicherheitsarchitekturen durch Identitätsfokus.",
             "date":"2025-11-02","importance":4},
            {"id":"te-9","title":"Open-Data-Initiativen fördern Forschung",
             "desc":"Mehr Datensets werden offen bereitgestellt, um Innovation zu beschleunigen.",
             "date":"2025-09-10","importance":3},
            {"id":"te-10","title":"Robotics verbessert Lagerlogistik",
             "desc":"Autonome Roboter verbessern Kommissionierprozesse in Lagern.",
             "date":"2025-04-18","importance":3},
        ],
        "Weltweit": [
            {"id":"we-1","title":"Gipfeltreffen einigen sich auf Klimaziele",
             "desc":"Vertreter vieler Länder erzielten Vereinbarungen zu Technologieaustausch und Emissionsminderung.",
             "date":"2025-10-05","importance":5},
            {"id":"we-2","title":"Friedensgespräche beginnen",
             "desc":"Diplomaten initiierten Gespräche mit dem Ziel einer Deeskalation und humanitären Zugangsverbesserung.",
             "date":"2025-09-22","importance":5},
            {"id":"we-3","title":"Weltbank finanziert Infrastrukturprojekte",
             "desc":"Neue Kreditlinien unterstützen nachhaltige Projekte in Entwicklungsregionen.",
             "date":"2025-08-11","importance":4},
            {"id":"we-4","title":"Pandemieprävention: Impfstofflager erweitert",
             "desc":"Strategische Lager sollen schnelle Reaktionsfähigkeit bei Ausbrüchen ermöglichen.",
             "date":"2025-06-05","importance":4},
            {"id":"we-5","title":"Handelsverhandlungen neu gestartet",
             "desc":"Staaten verhandeln Modernisierung von Handelsabkommen mit Fokus auf digitale Wirtschaft.",
             "date":"2025-07-01","importance":3},
            {"id":"we-6","title":"Humanitäre Hilfe erreicht Krisenregionen",
             "desc":"Konvois liefern dringend benötigte Güter; Verteilungspartner sind aktiv.",
             "date":"2025-04-20","importance":4},
            {"id":"we-7","title":"Kultureller Austausch stärkt Dialog",
             "desc":"Ein internationales Festival fördert Künstlerkooperation und Bildungsprogramme.",
             "date":"2025-03-08","importance":2},
            {"id":"we-8","title":"Wasserprojekte gegen Dürre gestartet",
             "desc":"Techniken zur Wasserrückgewinnung werden in Pilotprojekten getestet.",
             "date":"2025-02-14","importance":3},
            {"id":"we-9","title":"Digitale Rechte im Fokus",
             "desc":"Konferenzen diskutieren Datenschutz, Zugang und digitale Bildung weltweit.",             "date":"2025-01-30","importance":3},
            {"id":"we-10","title":"Regionale Infrastrukturprogramme angekündigt",
             "desc":"Finanzierungsprogramme für lokale Infrastrukturprojekte sollen kurzfristig Arbeitsplätze schaffen.",
             "date":"2025-01-30","importance":3},
        ],
        "Allgemein": [
            {"id":"al-1","title":"Bahn meldet bessere Pünktlichkeit",
             "desc":"Die Bahn berichtet von leicht verbesserten Pünktlichkeitswerten nach neuen Wartungszyklen. "
                     "Reisende zeigen sich vorsichtig optimistisch.",
             "date":"2025-10-01","importance":3},
            {"id":"al-2","title":"Grünflächen in Städten werden ausgebaut",
             "desc":"Kommunen investieren in Parks und Stadtbegrünung, um Mikroklima und Lebensqualität zu erhöhen.",
             "date":"2025-06-05","importance":2},
            {"id":"al-3","title":"Verbraucherschutz: klare Regeln für Onlinekäufe",
             "desc":"Neue Regelungen stärken Informationspflichten und Rückgaberechte für Online-Käufe.",
             "date":"2025-08-01","importance":4},
            {"id":"al-4","title":"Bibliotheken erweitern digitale Angebote",
             "desc":"Viele Bibliotheken bieten jetzt digitale Lernräume und Medienwerkstätten an.",
             "date":"2025-02-01","importance":2},
            {"id":"al-5","title":"Katastrophenschutz übt Evakuierungspläne",
             "desc":"Regionale Behörden testen Evakuierungsrouten und Kommunikationsketten in Vollübungen.",
             "date":"2025-01-08","importance":3},
            {"id":"al-6","title":"Ehrenamtsbörsen vermitteln Helfer",
             "desc":"Digitale Plattformen vernetzen Ehrenamtliche mit lokalen Projekten und Organisationen.",
             "date":"2025-03-22","importance":2},
            {"id":"al-7","title":"Mobilität: Car-Sharing-Pilotprojekte",
             "desc":"Pilotprojekte für Car-Sharing in Stadtteilen sollen den Individualverkehr verringern.",
             "date":"2025-11-03","importance":3},
            {"id":"al-8","title":"Lokale Kulturförderung gestärkt",
             "desc":"Kleine Kulturprojekte erhalten mehr Fördermittel und Coaching-Angebote.",
             "date":"2025-09-09","importance":2},
            {"id":"al-9","title":"Regionale Impfkampagnen verbessern Reichweite",
             "desc":"Mobile Impfstellen werden in strukturschwachen Regionen eingesetzt.",
             "date":"2025-04-10","importance":3},
            {"id":"al-10","title":"Fahrradstraßen-Pilotprojekte erfolgreich",
             "desc":"Teststrecken für Fahrradstraßen zeigen positive Nutzerbewertungen und weniger Kfz-Verkehr.",
             "date":"2025-05-20","importance":2},
        ]
    }
    return db

# Build DB once
NEWS_DB = build_news_db()
CATEGORIES = list(NEWS_DB.keys())

# ----------------------------
# Utility / Text processing
# ----------------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+", flags=re.UNICODE)
STOPWORDS = set([
    "und","der","die","das","ein","eine","in","im","zu","von","mit","für","auf","ist","sind","wie","als","auch","an","bei",
    "hat","haben","wird","werden","nicht","oder","aber","wir","ich","du","er","sie","es","dem","den","des"
])

def tokenize(text):
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

def extractive_summary(text, max_sentences=2):
    # Very simple extractive approach: split sentences and pick those with most 'keywords'
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        return ""
    # score sentences by token overlap with overall token frequency
    tokens = tokenize(text)
    freq = Counter(tokens)
    sent_scores = []
    for s in sentences:
        s_tokens = tokenize(s)
        score = sum(freq.get(w,0) for w in s_tokens)
        sent_scores.append((score, s))
    sent_scores.sort(key=lambda x: x[0], reverse=True)
    chosen = [s for _, s in sent_scores[:max_sentences]]
    return " ".join(chosen)

def sentiment_score(text):
    # returns -1..1 float
    pos = 0
    neg = 0
    t = text.lower()
    # small lexicon
    POS = ["erfolgreich","gewinnt","stark","besser","stabil","positiv","lob","begeistert","sieg","förder"]
    NEG = ["krise","verlust","scheit","problem","kritik","sorgen","unsicher","verzöger","einbruch","attack"]
    for p in POS:
        if p in t:
            pos += 1
    for n in NEG:
        if n in t:
            neg += 1
    if pos + neg == 0:
        return 0.0
    return round((pos - neg) / (pos + neg), 3)

def classify_sentiment_label(score):
    if score > 0.2:
        return "Positiv"
    if score < -0.2:
        return "Negativ"
    return "Neutral"

def headline_score(article):
    # heuristic score 0..100
    base = article.get("importance", 3) * 15  # 15..75
    txt = (article.get("title","") + " " + article.get("desc",""))
    s = sentiment_score(txt)
    base += s * 10  # +/-10
    # length bonus (ideal 6-14 tokens)
    l = len(tokenize(article.get("title","")))
    base += max(0, 8 - abs(l - 10))
    return int(max(0, min(100, base)))

# ----------------------------
# Favorites management
# ----------------------------
def load_favorites():
    return safe_load(FAV_FILE, {})

def save_favorites(favs):
    safe_save(FAV_FILE, favs)

FAVORITES = load_favorites()  # structure: {username: [article_ids...]}

def add_favorite(user, article_id):
    favs = FAVORITES.get(user, [])
    if article_id not in favs:
        favs.append(article_id)
    FAVORITES[user] = favs
    save_favorites(FAVORITES)

def remove_favorite(user, article_id):
    favs = FAVORITES.get(user, [])
    if article_id in favs:
        favs.remove(article_id)
    FAVORITES[user] = favs
    save_favorites(FAVORITES)

def user_favorites(user):
    return FAVORITES.get(user, [])

# ----------------------------
# Settings management
# ----------------------------
def load_settings():
    return safe_load(SETTINGS_FILE, {"theme":"light","home_count_each":2})

def save_settings(settings):
    safe_save(SETTINGS_FILE, settings)

GLOBAL_SETTINGS = load_settings()

# ----------------------------
# Search & retrieval helpers
# ----------------------------
def find_article_by_id(article_id):
    for cat, lst in NEWS_DB.items():
        for a in lst:
            if a.get("id") == article_id:
                return a, cat
    return None, None

def search_news(query, mood_filter=None, min_importance=None):
    q = query.lower().strip()
    hits = []
    for cat, lst in NEWS_DB.items():
        for a in lst:
            txt = (a.get("title","") + " " + a.get("desc","")).lower()
            if q in txt:
                score = headline_score(a)
                sscore = sentiment_score(txt)
                label = classify_sentiment_label(sscore)
                if mood_filter and label != mood_filter:
                    continue
                if min_importance and a.get("importance",0) < min_importance:
                    continue
                hits.append((score, a, cat, label))
    hits.sort(key=lambda x: x[0], reverse=True)
    return hits

# ----------------------------
# Analytics for personalization
# ----------------------------
def user_profile_stats(username):
    # simple stats: favorite count per category, most-read categories (mocked)
    favs = user_favorites(username)
    cat_counter = Counter()
    for fid in favs:
        a, cat = find_article_by_id(fid)
        if cat:
            cat_counter[cat] += 1
    return {"favorites_total": len(favs), "fav_by_category": dict(cat_counter)}

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Lumina News v2.0", layout="wide")
# initialize session
if "username" not in st.session_state:
    st.session_state.username = ""
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "theme" not in st.session_state:
    st.session_state.theme = GLOBAL_SETTINGS.get("theme","light")
if "last_read" not in st.session_state:
    st.session_state.last_read = []  # list of article ids

# Theme CSS (simple switch)
LIGHT_CSS = """
/* light */
body { background-color: #f7f9fc; color: #0b1a2b; }
.card { background: white; border-radius:8px; padding:12px; box-shadow: 0 1px 6px rgba(10,20,40,0.08); margin-bottom:12px; }
.header { color: #004aad; }
.small { color: #666; font-size:12px; }
.button-primary { background-color:#004aad; color:white; border-radius:6px; padding:6px 12px; }
"""
DARK_CSS = """
/* dark */
body { background-color: #0b1220; color: #e6eef8; }
.card { background: #0f1724; border-radius:8px; padding:12px; box-shadow: 0 1px 10px rgba(0,0,0,0.5); margin-bottom:12px; }
.header { color: #66b2ff; }
.small { color: #9fb7d9; font-size:12px; }
.button-primary { background-color:#1f6feb; color:white; border-radius:6px; padding:6px 12px; }
"""

def inject_css():
    css = LIGHT_CSS if st.session_state.theme == "light" else DARK_CSS
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

inject_css()

# Topbar
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("<h1 class='header'>🌐 Lumina News v2.0</h1>", unsafe_allow_html=True)
with col2:
    # small controls: theme toggle
    theme_choice = st.selectbox("Theme", ["light","dark"], index=0 if st.session_state.theme=="light" else 1)
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        GLOBAL_SETTINGS["theme"] = theme_choice
        save_settings(GLOBAL_SETTINGS)
        inject_css()

st.markdown("---")

# Authentication area
if not st.session_state.logged_in:
    # two-column: login + register
    lcol, rcol = st.columns(2)
    with lcol:
        st.subheader("🔐 Anmelden")
        with st.form("login_form"):
            uname = st.text_input("Benutzername", key="login_user")
            pwd = st.text_input("Passwort", type="password", key="login_pass")
            submit = st.form_submit_button("Einloggen")
            if submit:
                # load users
                users = safe_load(USERS_FILE, {"admin":"1234"})
                if users.get(uname) == pwd:
                    st.session_state.logged_in = True
                    st.session_state.username = uname
                    st.success(f"Willkommen, {uname}!")
                else:
                    st.error("Falsche Zugangsdaten.")
    with rcol:
        st.subheader("🆕 Registrieren")
        with st.form("reg_form"):
            r_uname = st.text_input("Neuer Benutzername", key="reg_user")
            r_pwd = st.text_input("Neues Passwort", type="password", key="reg_pass")
            reg_submit = st.form_submit_button("Registrieren")
            if reg_submit:
                users = safe_load(USERS_FILE, {"admin":"1234"})
                if not r_uname or not r_pwd:
                    st.warning("Bitte Benutzernamen und Passwort angeben.")
                elif r_uname in users:
                    st.warning("Benutzer existiert bereits.")
                else:
                    users[r_uname] = r_pwd
                    safe_save(USERS_FILE, users)
                    st.success("Registrierung erfolgreich! Bitte anmelden.")

    st.stop()

# If here, user is logged in
username = st.session_state.username

# Sidebar navigation
st.sidebar.title(f"👤 {username}")
pages = ["🏠 Home", "🔎 Suche", "📚 Kategorien", "📊 Analyse Gesamt", "⭐ Favoriten", "⚙️ Profil / Einstellungen"]
page = st.sidebar.radio("Navigation", pages)

# Helper to render a news card
def render_news_card(article, category, show_actions=True):
    # Build HTML for card
    title = article.get("title","")
    desc = article.get("desc","")
    date = article.get("date","")
    imp = article.get("importance",3)
    aid = article.get("id")
    score = headline_score(article)
    s_score = sentiment_score(desc)
    s_label = classify_sentiment_label(s_score)
    summary = extractive_summary(desc, max_sentences=2)
    favs = user_favorites(username)
    is_fav = aid in favs

    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"**{title}**  <span class='small'>{date} • Wichtigkeit: {imp} • Score: {score} • Stimmung: {s_label}</span>")
    st.markdown(f"<div style='margin-top:8px'>{summary}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='margin-top:8px; color:#888;'>Volltext: {desc}</div>", unsafe_allow_html=True)
    # actions
    cols = st.columns([1,1,1,6])
    with cols[0]:
        if show_actions and st.button("Lesen", key=f"read-{aid}"):
            # record last read
            st.session_state.last_read.insert(0, aid)
            if len(st.session_state.last_read) > 50:
                st.session_state.last_read = st.session_state.last_read[:50]
            st.experimental_rerun()
    with cols[1]:
        if show_actions and not is_fav and st.button("★ Favorit", key=f"fav-{aid}"):
            add_favorite(username, aid)
            st.success("Zur Favoritenliste hinzugefügt")
            st.experimental_rerun()
    with cols[2]:
        if show_actions and is_fav and st.button("✖ Entfernen", key=f"unfav-{aid}"):
            remove_favorite(username, aid)
            st.info("Aus Favoriten entfernt")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Page: Home ----------
if page == "🏠 Home":
    st.header("🏠 Home — Wichtige & personalisierte News")
    st.write("Hier siehst du oben die wichtigsten Meldungen und darunter personalisierte Empfehlungen.")

    # Top news: top N per category (settings control)
    n_each = GLOBAL_SETTINGS.get("home_count_each", 2)
    top_items = []
    for cat in CATEGORIES:
        top = sorted(NEWS_DB[cat], key=lambda x: x.get("importance",3), reverse=True)[:n_each]
        for t in top:
            top_items.append((t, cat))
    # Sort overall by importance then date
    top_items.sort(key=lambda x: (x[0].get("importance",3), x[0].get("date","")), reverse=True)

    st.subheader("Wichtigste Meldungen")
    for art, cat in top_items[:10]:
        render_news_card(art, cat)

    st.subheader("Empfohlene für dich")
    # personalization: show favorites categories & last read
    profile = user_profile_stats(username)
    favcats = list(profile.get("fav_by_category", {}).keys())
    recommended = []
    if favcats:
        for fc in favcats:
            recommended.extend([(a, fc) for a in NEWS_DB.get(fc, [])])
    # fallback: last read categories or recent
    if not recommended:
        # use last read
        for aid in st.session_state.last_read[:10]:
            a, c = find_article_by_id(aid)
            if a:
                recommended.append((a,c))
    if not recommended:
        # fallback to recent global
        for cat in CATEGORIES:
            recent = sorted(NEWS_DB[cat], key=lambda x: x.get("date",""), reverse=True)[:2]
            for r in recent:
                recommended.append((r, cat))

    # deduplicate by id
    seen = set()
    rec_final = []
    for a,c in recommended:
        if a.get("id") not in seen:
            rec_final.append((a,c))
            seen.add(a.get("id"))
    for a,c in rec_final[:8]:
        render_news_card(a, c)

# ---------- Page: Search ----------
elif page == "🔎 Suche":
    st.header("🔎 Suche")
    q = st.text_input("Suchbegriff (mehrere Wörter möglich)")
    mood = st.selectbox("Stimmung filtern", ["Alle","Positiv","Neutral","Negativ"])
    min_imp = st.slider("Minimale Wichtigkeit", 1, 5, 1)
    if st.button("Suchen"):
        mf = None if mood=="Alle" else mood
        hits = search_news(q, mood_filter=mf, min_importance=min_imp)
        st.write(f"{len(hits)} Treffer")
        for score, art, cat, label in hits:
            render_news_card(art, cat)

# ---------- Page: Categories ----------
elif page == "📚 Kategorien":
    st.header("📚 Kategorien")
    sel_cat = st.selectbox("Kategorie wählen", ["Alle"] + CATEGORIES)
    sort_opt = st.selectbox("Sortieren nach", ["Wichtigkeit","Datum","Headline-Score"])
    filter_mood = st.selectbox("Filter Stimmung", ["Alle","Positiv","Neutral","Negativ"])
    filter_imp = st.slider("Min. Wichtigkeit", 1, 5, 1)
    items = []
    cats_to_show = CATEGORIES if sel_cat == "Alle" else [sel_cat]
    for cat in cats_to_show:
        for a in NEWS_DB[cat]:
            sscore = sentiment_score(a.get("desc",""))
            label = classify_sentiment_label(sscore)
            if filter_mood != "Alle" and label != filter_mood:
                continue
            if a.get("importance",0) < filter_imp:
                continue
            items.append((a, cat, headline_score(a)))
    if sort_opt == "Wichtigkeit":
        items.sort(key=lambda x: x[0].get("importance",0), reverse=True)
    elif sort_opt == "Datum":
        items.sort(key=lambda x: x[0].get("date",""), reverse=True)
    else:
        items.sort(key=lambda x: x[2], reverse=True)

    for a, c, sc in items:
        render_news_card(a, c)

# ---------- Page: Analysis ----------
elif page == "📊 Analyse Gesamt":
    st.header("📊 Gesamtanalyse")
    st.write("Stimmungen und Top-Wörter pro Kategorie")
    for cat in CATEGORIES:
        lst = NEWS_DB[cat]
        sentiments = [classify_sentiment_label(sentiment_score((x.get("title","")+" "+x.get("desc","")))) for x in lst]
        pos = sentiments.count("Positiv")
        neu = sentiments.count("Neutral")
        neg = sentiments.count("Negativ")
        st.subheader(cat)
        st.write({"Positiv": pos, "Neutral": neu, "Negativ": neg})
        twords = Counter()
        for x in lst:
            for w in tokenize(x.get("desc","")):
                twords[w] += 1
        st.write("Top Wörter:", twords.most_common(8))

# ---------- Page: Favorites ----------
elif page == "⭐ Favoriten":
    st.header("⭐ Deine Favoriten")
    favs = user_favorites(username)
    if not favs:
        st.info("Keine Favoriten. Markiere Artikel mit ★ um sie hier zu speichern.")
    else:
        for aid in favs:
            art, cat = find_article_by_id(aid)
            if art:
                render_news_card(art, cat)

# ---------- Page: Profile / Settings ----------
elif page == "⚙️ Profil / Einstellungen":
    st.header("⚙️ Profil & Einstellungen")
    st.subheader("Benutzerinfo")
    st.write(f"Benutzername: **{username}**")
    stats = user_profile_stats(username)
    st.write(f"Favoriten insgesamt: {stats.get('favorites_total',0)}")
    st.write("Favoriten pro Kategorie:", stats.get("fav_by_category", {}))

    st.subheader("Einstellungen")
    c1, c2 = st.columns(2)
    with c1:
        home_count = st.number_input("Anzahl Top-News pro Kategorie auf Home", min_value=1, max_value=5, value=GLOBAL_SETTINGS.get("home_count_each",2))
        if st.button("Speichern Home-Einstellung"):
            GLOBAL_SETTINGS["home_count_each"] = int(home_count)
            save_settings(GLOBAL_SETTINGS)
            st.success("Gespeichert")
    with c2:
        if st.button("Alle Favoriten löschen"):
            FAVORITES[username] = []
            save_favorites(FAVORITES)
            st.info("Favoriten gelöscht")

# End of file
