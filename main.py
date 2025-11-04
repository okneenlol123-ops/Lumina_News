# -*- coding: utf-8 -*-
"""
Lumina News - Offline CLI (optimiert, lazy analyzer, Startbanner, exit-summary)
Speichern als main.py und ausführen: python main.py
Keine externen Abhängigkeiten.
"""

from datetime import datetime
from collections import Counter
import json
import math
import os
import re
import sys

# -----------------------
# Dateipfade
# -----------------------
USERS_FILE = "users.json"
SETTINGS_FILE = "settings.json"

# -----------------------
# Hilfsfunktionen: JSON Safe IO
# -----------------------
def safe_load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] Fehler beim Laden von {path}: {e}")
    return default

def safe_save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Fehler beim Speichern von {path}: {e}")

# -----------------------
# Dataset (realistisch formulierte Artikel)
# 7 Kategorien, je 6 Artikel (kompakt, kann leicht erweitert werden)
# -----------------------
def build_news_dataset():
    return {
        "Powi": [
            {"title":"Neue Lehrpläne stärken kritisches Denken",
             "description":"Das Kultusministerium hat überarbeitete Lehrpläne vorgestellt, die kritisches Denken und Medienkompetenz in den Mittelpunkt stellen. "
                          "Lehrkräfte werden in Quellenkritik und Projektlernen fortgebildet. "
                          "Pilotprojekte laufen in mehreren Bundesländern. "
                          "Eltern- und Schülervertretungen waren eingebunden. "
                          "Langfristig soll die Studier- und Berufsvorbereitung verbessert werden.",
             "link":"https://example.org/powi/lehrplaene", "importance":5, "date":"2025-09-15"},
            {"title":"Digitaler Unterricht: Ausstattung kommt",
             "description":"Ein Förderprogramm liefert Hardware und Infrastruktur an Schulen. "
                          "Datenschutz und Methodik sind Teil der Maßnahmen. "
                          "Lehrkräfte erhalten begleitende Schulungen. "
                          "Die Pilotregionen berichten erste positive Effekte. "
                          "Ziel ist nachhaltige digitale Bildung.",
             "link":"https://example.org/powi/digital", "importance":4, "date":"2025-10-01"},
            {"title":"Schulfahrten werden gefördert",
             "description":"Zuschüsse für mehrtägige Schulfahrten werden ausgeweitet, um soziale Teilhabe zu stärken. "
                          "Anträge werden digitalisiert, um Zugang zu erleichtern. "
                          "Kulturelle Programme werden besonders unterstützt. "
                          "Verbände fordern parallel Inklusionsmittel. "
                          "Start der Maßnahme ist noch dieses Jahr.",
             "link":"https://example.org/powi/schulfahrten", "importance":3, "date":"2025-07-20"},
            {"title":"MINT-Initiative startet regionale Clubs",
             "description":"Regionale MINT-Clubs für Schüler fördern Interesse an Naturwissenschaften. "
                          "Mentoring-Programme verbinden Schulen und Hochschulen. "
                          "Besonders Mädchen werden gezielt angesprochen. "
                          "Wettbewerbe und Workshops begleiten die Initiative. "
                          "Langfristig sollen Fachkräfte gefördert werden.",
             "link":"https://example.org/powi/mint", "importance":4, "date":"2025-05-05"},
            {"title":"Schulsozialarbeit wird ausgebaut",
             "description":"Mehr Schulsozialarbeiter sollen psychosoziale Angebote für Schüler bereitstellen. "
                          "Prävention und Frühintervention sind zentrale Ziele. "
                          "Kooperation mit Jugendhilfe wird gestärkt. "
                          "Erste Pilotregionen melden sinkende Fehlzeiten. "
                          "Fördermittel wurden bewilligt.",
             "link":"https://example.org/powi/sozial", "importance":4, "date":"2025-04-12"},
            {"title":"Berufsorientierung: Pflichtmodul geplant",
             "description":"Schulen führen verpflichtende Module zur Berufsorientierung ein. "
                          "Praktika und Bewerbungstrainings werden enger mit Unternehmen vernetzt. "
                          "Schüler sollen realistische Berufsbilder kennenlernen. "
                          "Ziele sind bessere Übergänge in Ausbildung und Studium. "
                          "Projektstarts sind regional gestaffelt.",
             "link":"https://example.org/powi/beruf", "importance":3, "date":"2025-06-10"},
        ],
        "Wirtschaft": [
            {"title":"Industrieproduktion zeigt Aufwärtstrend",
             "description":"Die Industrieproduktion verbucht moderate Zuwächse, vor allem im Maschinenbau. "
                          "Exportaufträge und Investitionen in Automatisierung stärken das Wachstum. "
                          "Analysten warnen vor Lieferkettenrisiken, bleiben aber überwiegend optimistisch. "
                          "Unternehmen investieren in Digitalisierung. "
                          "Die Stimmung hat sich gegenüber dem Vorjahr verbessert.",
             "link":"https://example.org/wirtschaft/industrie", "importance":4, "date":"2025-10-20"},
            {"title":"Mittelstand investiert in KI-Lösungen",
             "description":"Viele mittelständische Firmen setzen auf KI zur Automatisierung und Effizienzsteigerung. "
                          "Förderprogramme unterstützen Pilotprojekte. "
                          "Datenschutz und Qualifizierung bleiben offene Fragen. "
                          "Erste Produktivitätsgewinne werden berichtet. "
                          "Berater verzeichnen starkes Interesse.",
             "link":"https://example.org/wirtschaft/ki", "importance":4, "date":"2025-09-05"},
            {"title":"Arbeitsmarkt bleibt robust",
             "description":"Die Arbeitslosenquote zeigt stabile Trends, offene Stellen vor allem in IT und Pflege. "
                          "Weiterbildung wird als Schlüssel zur Fachkräftesicherung gesehen. "
                          "Gewerkschaften verhandeln in mehreren Branchen. "
                          "Unternehmen melden anhaltenden Bedarf trotz wirtschaftlicher Schwankungen. "
                          "Regionale Unterschiede bleiben bestehen.",
             "link":"https://example.org/wirtschaft/arbeitsmarkt", "importance":3, "date":"2025-08-14"},
            {"title":"Startups sichern Finanzierung für grüne Techs",
             "description":"Investoren finanzieren vermehrt Startups im Bereich Energiespeicher und Mobilität. "
                          "Acceleratoren unterstützen Skalierung. "
                          "Politische Anreize flankieren private Mittel. "
                          "Markteintritte werden beschleunigt. "
                          "Erste Skalierungserfolge sind sichtbar.",
             "link":"https://example.org/wirtschaft/startups", "importance":3, "date":"2025-06-22"},
            {"title":"Export nach Asien nimmt zu",
             "description":"Deutsche Exporte in bestimmte asiatische Märkte steigen, besonders im Maschinenbau. "
                          "Unternehmen bauen Vertriebsnetzwerke aus. "
                          "Wechselkurse bleiben Einflussfaktor. "
                          "Logistikoptimierungen reduzieren Lieferzeiten. "
                          "Neue Partnerschaften werden geschlossen.",
             "link":"https://example.org/wirtschaft/export", "importance":3, "date":"2025-05-12"},
            {"title":"Energieeffizienz gewinnt an Bedeutung",
             "description":"Unternehmen investieren in Energieeffizienz und Abwärmenutzung zur Kostensenkung. "
                          "Förderprogramme erleichtern Investitionen. "
                          "Nachhaltigkeitskennzahlen werden wichtiger für Investoren. "
                          "Langfristig sollen Betriebskosten sinken. "
                          "Maßnahmen werden branchenübergreifend diskutiert.",
             "link":"https://example.org/wirtschaft/energie", "importance":3, "date":"2025-02-10"},
        ],
        "Politik": [
            {"title":"Koalitionsgespräche in entscheidender Phase",
             "description":"Verhandlungen über die Regierungsbildung treten in die finale Phase. "
                          "Kompromisse zu Klima- und Finanzfragen sind zu erwarten. "
                          "Die Öffentlichkeit verfolgt die Gespräche intensiv. "
                          "Parteien signalisieren Kompromissbereitschaft in Teilfragen. "
                          "Ein Abschluss wird in Kürze erwartet.",
             "link":"https://example.org/politik/koalition", "importance":5, "date":"2025-11-01"},
            {"title":"Transparenzgesetz: Lobbykontakte im Fokus",
             "description":"Ein Entwurf für erweiterte Offenlegungspflichten will Lobbykontakte transparenter machen. "
                          "Verbandsseite kritisiert den Verwaltungsaufwand. "
                          "Befürworter sehen einen Gewinn an Vertrauen. "
                          "Das Gesetz durchläuft parlamentarische Beratungen. "
                          "Zivilgesellschaftliche Gruppen unterstützen die Debatte.",
             "link":"https://example.org/politik/transparenz", "importance":4, "date":"2025-07-02"},
            {"title":"Datenschutz & KI: Debatten im Parlament",
             "description":"Anpassungen des Datenschutzrechts im Kontext von KI werden diskutiert. "
                          "Balance zwischen Innovation und Grundrechtsschutz steht im Mittelpunkt. "
                          "Sachverständige und Branchenvertreter werden angehört. "
                          "Regulatorische Leitplanken sind gefragt. "
                          "Entscheidungen werden folgen.",
             "link":"https://example.org/politik/datenschutz", "importance":5, "date":"2025-05-19"},
            {"title":"Kommunale Investitionshilfen beschlossen",
             "description":"Bundesmittel unterstützen kommunale Digitalisierungs- und Infrastrukturprojekte. "
                          "Ziel ist die langfristige Stärkung lokaler Handlungsfähigkeit. "
                          "Priorität haben strukturschwache Regionen. "
                          "Anträge werden schrittweise bearbeitet. "
                          "Kommunen begrüßen die Unterstützung.",
             "link":"https://example.org/politik/kommunen", "importance":3, "date":"2025-10-18"},
            {"title":"Integration: Programme für Arbeitsmarkt",
             "description":"Sprach- und Qualifizierungsprogramme für Zugewanderte werden ausgebaut. "
                          "Kooperationen mit Betrieben erleichtern Praktika. "
                          "Ziele sind nachhaltige Teilhabe und Beschäftigung. "
                          "Regionale Initiativen werden gefördert. "
                          "Erste Evaluationen zeigen positive Trends.",
             "link":"https://example.org/politik/integration", "importance":3, "date":"2025-06-25"},
            {"title":"Innenpolitik: Cyberabwehr wird gestärkt",
             "description":"Ressourcen für Cyberabwehr und IT-Sicherheit werden erhöht. "
                          "Kritische Infrastruktur steht im Fokus. "
                          "Zusammenarbeit mit Forschungseinrichtungen wird ausgebaut. "
                          "Ausbildungskapazitäten für Spezialisten sollen erweitert werden. "
                          "Maßnahmen sollen die Resilienz erhöhen.",
             "link":"https://example.org/politik/cyber", "importance":4, "date":"2025-04-10"},
        ],
        "Sport": [
            {"title":"Nationalteam triumphiert im Qualifikationsspiel",
             "description":"Dank taktischer Disziplin sichert sich das Team einen wichtigen Sieg. "
                          "Trainer lobt die mannschaftliche Leistung. "
                          "Fans feiern in vielen Städten. "
                          "Der Erfolg stärkt die Startchancen im Turnier. "
                          "Nächste Aufgaben sind bereits terminiert.",
             "link":"https://example.org/sport/qualifikation", "importance":5, "date":"2025-10-31"},
            {"title":"Nachwuchsprogramm eines Bundesligisten wird ausgebaut",
             "description":"Ein Club investiert in seine Akademie, um Talente langfristig zu fördern. "
                          "Kooperationen mit Schulen sollen Praxisnähe herstellen. "
                          "Trainer setzen moderne Trainingskonzepte ein. "
                          "Erste Erfolge zeigen sich in Jugendwettbewerben. "
                          "Förderer unterstützen langfristig.",
             "link":"https://example.org/sport/nachwuchs", "importance":3, "date":"2025-09-12"},
            {"title":"Olympia-Vorbereitung: Athleten in Top-Form",
             "description":"Vorbereitungswettkämpfe zeigen vielversprechende Leistungen. "
                          "Trainer optimieren Formkurven für die Saison. "
                          "Verbände sind mit dem Gesamtverlauf zufrieden. "
                          "Medaillenkandidaten zeigen starke Ergebnisse. "
                          "Vorfreude und Erwartungen steigen.",
             "link":"https://example.org/sport/olympia", "importance":4, "date":"2025-08-01"},
            {"title":"Tennis: Überraschungssieg sorgt für Aufsehen",
             "description":"Ein Newcomer gewinnt überraschend ein großes Turnier und sorgt für Medieninteresse. "
                          "Ranglistenpunkte verbessern seine Position deutlich. "
                          "Trainer loben mentale Stärke. "
                          "Sponsoren zeigen Interesse an einer Zusammenarbeit. "
                          "Weitere Turniere stehen an.",
             "link":"https://example.org/sport/tennis", "importance":3, "date":"2025-07-18"},
            {"title":"Radsport: Etappensieg ändert Gesamtwertung",
             "description":"Ein spektakulärer Antritt sorgt für einen Etappensieg und veränderte Gesamtstände. "
                          "Teamtaktiken prägten den Rennverlauf. "
                          "Die nächsten Berge entscheiden weiter. "
                          "Zuschauer loben den Kampfgeist der Fahrer. "
                          "Weitere spannende Etappen folgen.",
             "link":"https://example.org/sport/radsport", "importance":3, "date":"2025-04-22"},
            {"title":"Leichtathletik: Nachwuchsmeeting mit Bestleistun
gswerten",
             "description":"Junge Athleten erzielten persönliche Bestleistungen bei einem Meeting. "
                          "Trainer sehen positive Trends für kommende Großevents. "
                          "Sprint- und Sprungdisziplinen dominierten. "
                          "Vereine berichten über gesteigerte Teilnahme. "
                          "Talentförderprogramme werden ausgeweitet.",
             "link":"https://example.org/sport/leichtathletik", "importance":2, "date":"2025-03-30"},
        ],
        "Technologie": [
            {"title":"Neuer KI-Chip kündigt Energieeffizienz an",
             "description":"Ein Chiphersteller stellt einen energieeffizienten KI-Chip vor, der Rechenzentren entlasten soll. "
                          "Tests laufen in Kooperation mit Rechenzentren. "
                          "Partner prüfen Anwendungsszenarien für Edge und Cloud. "
                          "Die Markteinführung ist für 2026 geplant. "
                          "Forschungsteams sind beteiligt.",
             "link":"https://example.org/tech/ki-chip", "importance":5, "date":"2025-10-30"},
            {"title":"5G-Privatnetze ermöglichen smarte Fabriken",
             "description":"Unternehmen bauen private 5G-Netze für Produktionsanwendungen auf. "
                          "Echtzeitkommunikation fördert Automatisierung und Sensorik. "
                          "Pilotprojekte melden Effizienzgewinne. "
                          "Regulatorische Fragen werden parallel diskutiert. "
                          "Skalierung bleibt Herausforderung.",
             "link":"https://example.org/tech/5g", "importance":4, "date":"2025-08-20"},
            {"title":"Quantenfehlerkorrektur verbessert Stabilität",
             "description":"Forschungsgruppen melden Fortschritte in der Fehlerkorrektur für Quantenrechner. "
                          "Die Stabilität von Qubits steigt, Experimente zeigen Fortschritte. "
                          "Industriepartner prüfen konkrete Anwendungen. "
                          "Kommerzielle Nutzung bleibt mittelfristig anspruchsvoll. "
                          "Die Forschung bleibt vielversprechend.",
             "link":"https://example.org/tech/quanten", "importance":5, "date":"2025-07-09"},
            {"title":"Open-Source-Tools erleichtern Testautomatisierung",
             "description":"Community-Projekte bieten modulare Tools zur Testautomatisierung und CI-Integration. "
                          "Entwickler profitieren von wiederverwendbaren Workflows. "
                          "Adoption steigt insbesondere in Startups. "
                          "Projekte werden international getragen. "
                          "Kollaboration stärkt Best-Practices.",
             "link":"https://example.org/tech/opensource", "importance":3, "date":"2025-06-16"},
            {"title":"Cloudanbieter launchen Nachhaltigkeitswerkzeuge",
             "description":"Neue Tools unterstützen Kunden beim Messen von CO₂-Emissionen ihrer Workloads. "
                          "ESG-Reporting wird dadurch vereinfacht. "
                          "Kunden beginnen, Workloads effizienter zu planen. "
                          "Standards und Messmethoden werden diskutiert. "
                          "Einige Pilotkunden berichten Einsparungen.",
             "link":"https://example.org/tech/cloud", "importance":3, "date":"2025-03-12"},
            {"title":"Bildverarbeitung unterstützt medizinische Diagnostik",
             "description":"KI-gestützte Bildverarbeitung verbessert Erkennungsraten in einigen Diagnosen. "
                          "Ärzte nutzen die Tools als Unterstützung. "
                          "Regulatorische Prüfungen laufen parallel. "
                          "Pilotprojekte in Kliniken zeigen positiven Nutzen. "
                          "Ziel ist assistierende Nutzung, nicht Ersatz.",
             "link":"https://example.org/tech/med", "importance":5, "date":"2025-02-25"},
        ],
        "Weltweit": [
            {"title":"Internationale Klimapartnerschaften vereinbart",
             "description":"Staaten einigen sich auf Technologietransfer und Emissionsreduktion in einer Partnerschaft. "
                          "Finanzierung für Anpassungsmaßnahmen ist vorgesehen. "
                          "Monitoringmechanismen begleiten die Umsetzung. "
                          "Entwicklungsländer erhalten gezielte Unterstützung. "
                          "Die Initiative wird international begrüßt.",
             "link":"https://example.org/welt/klima", "importance":5, "date":"2025-10-05"},
            {"title":"Friedensgespräche in Konfliktregion gestartet",
             "description":"Diplomatische Verhandlungen sollen die Lage entschärfen und humanitären Zugang verbessern. "
                          "Der Prozess gilt als fragil, doch Vermittler zeigen Einsatz. "
                          "Internationale Organisationen unterstützen den Dialog. "
                          "Gefangenenaustausch und Hilfskorridore werden diskutiert. "
                          "Beobachter bleiben vorsichtig optimistisch.",
             "link":"https://example.org/welt/frieden", "importance":5, "date":"2025-09-22"},
            {"title":"Weltbank finanziert nachhaltige Infrastrukturprojekte",
             "description":"Neue Kredite unterstützen Wasser-, Energie- und Verkehrsprojekte in Entwicklungsregionen. "
                          "Umweltprüfungen sind Teil der Vergabebedingungen. "
                          "Transparenzkriterien begleiten die Auswahl. "
                          "Projekte zielen auf Arbeitsplatzschaffung und Wachstum. "
                          "Regionale Partnerschaften sind vorgesehen.",
             "link":"https://example.org/welt/weltbank", "importance":4, "date":"2025-08-11"},
            {"title":"Pandemieprävention: Impfstofflager werden ausgebaut",
             "description":"Strategische Lager für Impfstoffe erhöhen die Reaktionsfähigkeit bei Ausbrüchen. "
                          "Logistiknetzwerke und Kühlketten werden optimiert. "
                          "Multilaterale Finanzierung unterstützt die Maßnahmen. "
                          "Regionale Kooperationen verstärken Verteilungskapazitäten. "
                          "Ziel ist schnellere Verfügbarkeit in Krisen.",
             "link":"https://example.org/welt/impfstoffe", "importance":4, "date":"2025-06-05"},
            {"title":"Regionale Handelsverhandlungen neu gestartet",
             "description":"Verhandlungen zur Modernisierung von Handelsabkommen beginnen, Fokus auf digitale Wirtschaft. "
                          "Zoll- und Nachhaltigkeitsfragen stehen auf der Agenda. "
                          "Unternehmer hoffen auf klare Rahmenbedingungen. "
                          "Verhandlungen dauern voraussichtlich Monate. "
                          "Outcome könnte große wirtschaftliche Wirkung haben.",
             "link":"https://example.org/welt/handel", "importance":3, "date":"2025-07-01"},
            {"title":"Kultureller Austausch fördert Dialog",
             "description":"Ein internationales Festival stärkt den Austausch von Künstlern und kulturellen Projekten. "
                          "Workshops und Ausstellungen setzen auf lokale Teilhabe. "
                          "Initiativen unterstützen Bildungsangebote vor Ort. "
                          "Die Veranstaltung zieht internationale Gäste an. "
                          "Nachhaltige Netzwerke werden aufgebaut.",
             "link":"https://example.org/welt/kultur", "importance":2, "date":"2025-03-08"},
        ],
        "Allgemein": [
            {"title":"Bahn meldet verbesserte Pünktlichkeit",
             "description":"Die Bahn berichtet von Pünktlichkeitssteigerungen nach neuen Abläufen und Wartungsplänen. "
                          "Kunden zeigen sich vorsichtig optimistisch. "
                          "Weitere Investitionen sind geplant. "
                          "Transparenzberichte sollen Reisende besser informieren. "
                          "Langfristige Effekte werden beobachtet.",
             "link":"https://example.org/allgemein/bahn", "importance":3, "date":"2025-10-01"},
            {"title":"Kommunen investieren in Grünflächen",
             "description":"Städte fördern neue Begrünungsprojekte zur Verbesserung des Mikroklimas und Naherholung. "
                          "Bürgerbeteiligung wird aktiv eingebunden. "
                          "Förderprogramme unterstützen Planung und Pflege. "
                          "Die Maßnahmen stärken Lebensqualität in Vierteln. "
                          "Begleitende Studien evaluieren Effekte.",
             "link":"https://example.org/allgemein/gruen", "importance":2, "date":"2025-06-05"},
            {"title":"Verbraucherschutz: Regeln für Onlinekäufe verschärft",
             "description":"Informationspflichten und Rückgaberechte werden für Onlinehändler klarer geregelt. "
                          "Ziel ist erhöhte Transparenz und weniger Abzocke im E-Commerce. "
                          "Kontrollen werden verstärkt. "
                          "Konsumentenrechte werden gestärkt. "
                          "Umsetzung erfolgt schrittweise.",
             "link":"https://example.org/allgemein/verbraucher", "importance":4, "date":"2025-08-01"},
            {"title":"Bibliotheken bauen digitale Angebote aus",
             "description":"Digitale Lernräume und Medienwerkstätten erweitern das Angebot der Bibliotheken. "
                          "Kooperationen mit Schulen fördern Nutzung und Kompetenzaufbau. "
                          "Flexiblere Öffnungszeiten erhöhen Zugänglichkeit. "
                          "Programme fokussieren inklusive Bildung. "
                          "Regional werden Pilotprojekte getestet.",
             "link":"https://example.org/allgemein/bibliothek", "importance":2, "date":"2025-02-01"},
            {"title":"Katastrophenschutz übt Evakuierungen",
             "description":"Großangelegte Übungen für Evakuierungen testen Kommunikation und Logistik. "
                          "Rettungskräfte und Verwaltung kooperieren eng. "
                          "Erkenntnisse fließen in künftige Pläne ein. "
                          "Freiwillige unterstützen Szenarien. "
                          "Maßnahmen erhöhen Reaktionsfähigkeit.",
             "link":"https://example.org/allgemein/katastrophen", "importance":3, "date":"2025-01-08"},
            {"title":"Mobilität: Car-Sharing Tests gestartet",
             "description":"Pilotprojekte für Car-Sharing sollen Städte entlasten und Emissionen senken. "
                          "Datenanalyse begleitet die Planung. "
                          "Kooperation mit Anbietern wird geprüft. "
                          "Nutzerbefragungen fließen in Entscheidungen ein. "
                          "Ergebnisse entscheiden über Ausweitung.",
             "link":"https://example.org/allgemein/mobilitaet", "importance":3, "date":"2025-11-03"},
        ],
    }

# -----------------------
# Tokenizer, Stopwords, Sentiment Lexikon (Deutsch, kompakt)
# -----------------------
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+", flags=re.UNICODE)

GERMAN_STOPWORDS = {
    "und","oder","aber","auch","als","an","auf","bei","der","die","das","ein","eine","in","im","ist","sind",
    "mit","zu","von","den","des","für","dass","dem","nicht","vor","nach","wie","er","sie","es","wir","ihr","ich",
    "hat","haben","werden","wird","seit","mehr","dies","diese","sehr","nur","noch","so","als","bei","um","gegen"
}

POSITIVE_LEXICON = {
    "gut","stark","erfolgreich","verbessert","gewinnt","begrüßt","optimistisch","stabil","steigerung","gewinn",
    "sicher","förder","unterstützt","erholen","aufwind","positive","verbesserung","erfolg"
}

NEGATIVE_LEXICON = {
    "kritisch","warn","warnen","risiko","risiken","verlust","problem","schwier","krise","fragil","stagn","einbruch",
    "verzöger","engpass","kritik","mangel","unsicher","sorge","problematisch"
}

def tokenize(text):
    text = text or ""
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    tokens = [t for t in tokens if t not in GERMAN_STOPWORDS and len(t) > 2]
    return tokens

def sentiment_score_text(text):
    tokens = tokenize(text)
    pos = sum(1 for t in tokens if any(p in t for p in POSITIVE_LEXICON))
    neg = sum(1 for t in tokens if any(n in t for n in NEGATIVE_LEXICON))
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)

# -----------------------
# TF-IDF like map (lazy)
# -----------------------
def compute_idf_map(docs):
    # docs: list of strings
    doc_tokens = [set(tokenize(d)) for d in docs]
    df = Counter()
    for s in doc_tokens:
        for term in s:
            df[term] += 1
    N = len(docs) if docs else 1
    idf = {t: math.log((N + 1) / (df_n + 1)) + 1 for t, df_n in df.items()}
    return idf

# -----------------------
# Headline Scorer
# -----------------------
def score_headline(article, idf_map=None, important_terms=None):
    score = 0.0
    importance = float(article.get("importance", 3))
    score += importance * 10.0  # base 10..50
    txt = (article.get("title","") + " " + article.get("description",""))
    s = sentiment_score_text(txt)
    score += s * 8.0  # -8..+8
    title_tokens = tokenize(article.get("title",""))
    l = len(title_tokens)
    opt_bonus = max(0, 8 - abs(l - 9))  # ideal length ~9
    score += opt_bonus
    if idf_map:
        for w in set(title_tokens):
            score += idf_map.get(w, 0.0) * 2.0
    if important_terms:
        lowtxt = txt.lower()
        for it in important_terms:
            if it in lowtxt:
                score += 3.0
    score = max(-100.0, min(100.0, score))
    normalized = (score + 100.0) / 2.0
    return round(normalized, 1)

# -----------------------
# Analyzer (lazy evaluation)
# -----------------------
class Analyzer:
    def __init__(self, dataset):
        self.dataset = dataset
        self._initialized = False
        self.idf_map = {}
        self.global_top = []
        self.cat_stats = {}

    def initialize(self):
        if self._initialized:
            return
        all_texts = []
        for cat, arts in self.dataset.items():
            for a in arts:
                all_texts.append(a.get("title","") + " " + a.get("description",""))
        self.idf_map = compute_idf_map(all_texts)
        # global top tokens
        global_counter = Counter()
        for t in all_texts:
            global_counter.update(tokenize(t))
        self.global_top = [t for t,_ in global_counter.most_common(100)]
        # per-category
        for cat, arts in self.dataset.items():
            texts = [a.get("title","") + " " + a.get("description","") for a in arts]
            tokens = []
            for t in texts:
                tokens.extend(tokenize(t))
            freq = Counter(tokens)
            sentiments = [sentiment_score_text(t) for t in texts if t.strip()]
            avg_sent = round(sum(sentiments)/len(sentiments), 3) if sentiments else 0.0
            avg_imp = round(sum(a.get("importance",3) for a in arts)/len(arts), 3) if arts else 0.0
            month_counts = Counter()
            for a in arts:
                try:
                    dt = datetime.strptime(a.get("date","1970-01-01"), "%Y-%m-%d")
                    month_counts[dt.strftime("%Y-%m")] += 1
                except Exception:
                    pass
            self.cat_stats[cat] = {
                "freq": freq,
                "top_terms": [t for t,_ in freq.most_common(20)],
                "avg_sentiment": avg_sent,
                "avg_importance": avg_imp,
                "month_counts": dict(month_counts)
            }
        self._initialized = True

    def get_global_top(self, n=20):
        self.initialize()
        return self.global_top[:n]

    def get_cat_summary(self, cat):
        self.initialize()
        return self.cat_stats.get(cat, {})

    def sentiment_distribution(self, cat=None):
        self.initialize()
        def cls(x):
            if x > 0.2: return "positive"
            if x < -0.2: return "negative"
            return "neutral"
        buckets = Counter()
        if cat:
            arts = self.dataset.get(cat, [])
        else:
            arts = [a for lst in self.dataset.values() for a in lst]
        for a in arts:
            s = sentiment_score_text(a.get("title","") + " " + a.get("description",""))
            buckets[cls(s)] += 1
        return dict(buckets)

    def top_headlines(self, cat, n=10):
        self.initialize()
        arts = list(self.dataset.get(cat, []))
        important = self.get_global_top(8)
        scored = []
        for a in arts:
            sc = score_headline(a, idf_map=self.idf_map, important_terms=important)
            scored.append((sc, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(s, art) for s, art in scored[:n]]

    def trend_series(self, cat):
        self.initialize()
        return sorted(self.cat_stats.get(cat, {}).get("month_counts", {}).items())

# -----------------------
# User management
# -----------------------
class UserManager:
    def __init__(self):
        self.file = USERS_FILE
        self.users = safe_load_json(self.file, {})  # username -> {password, created}
    def register(self, username, password):
        if not username or not password:
            return False, "Benutzername und Passwort dürfen nicht leer sein."
        if username in self.users:
            return False, "Benutzer existiert bereits."
        self.users[username] = {"password": password, "created": datetime.utcnow().isoformat()}
        safe_save_json(self.file, self.users)
        return True, "Registrierung erfolgreich."
    def login(self, username, password):
        if username not in self.users:
            return False, "Benutzer nicht gefunden."
        if self.users[username].get("password") != password:
            return False, "Falsches Passwort."
        return True, "Login erfolgreich."

# -----------------------
# CLI (clean, fast, lazy)
# -----------------------
class CLI:
    def __init__(self):
        self.dataset = build_news_dataset()
        self.analyzer = Analyzer(self.dataset)  # lazy
        self.user_mgr = UserManager()
        self.settings = safe_load_json(SETTINGS_FILE, {"sort_mode":"neueste"})
        self.current_user = None

    def start_banner(self):
        print("="*50)
        print("🌟 Lumina News (Offline) — Schnellstart")
        print("1) Start")
        print("2) Beenden")
        print("="*50)
        while True:
            c = input("Auswahl: ").strip()
            if c == "1":
                return True
            if c == "2":
                print("Beende...")
                sys.exit(0)
            print("Bitte 1 oder 2 eingeben.")

    def run(self):
        # Banner
        self.start_banner()
        # Authentication
        while True:
            print("\n--- Anmeldung ---")
            print("1) Login")
            print("2) Registrierung")
            print("3) Als Gast fortfahren")
            print("0) Beenden")
            choice = input("Auswahl: ").strip()
            if choice == "1":
                u = input("Benutzername: ").strip()
                p = input("Passwort: ").strip()
                ok, msg = self.user_mgr.login(u, p)
                print(msg)
                if ok:
                    self.current_user = u
                    break
            elif choice == "2":
                u = input("Gewünschter Benutzername: ").strip()
                p = input("Passwort: ").strip()
                ok, msg = self.user_mgr.register(u, p)
                print(msg)
            elif choice == "3":
                self.current_user = "Gast"
                break
            elif choice == "0":
                print("Auf Wiedersehen.")
                sys.exit(0)
            else:
                print("Ungültig.")

        # Main loop
        try:
            self.main_loop()
        finally:
            # On exit, compute a short global summary (lazy init)
            print("\n--- Abschlussbericht (Kurz) ---")
            self.analyzer.initialize()
            top = self.analyzer.get_global_top(10)
            sentiment = self.analyzer.sentiment_distribution()
            # simple summary heuristics
            dominant = max(sentiment.items(), key=lambda x: x[1])[0] if sentiment else "neutral"
            print(f"Top-Themen (Stichwörter): {', '.join(top[:8])}")
            print(f"Sentiment-Verteilung (global): {sentiment}")
            print(f"Dominante Stimmung: {dominant}")
            print("Danke für die Nutzung von Lumina News. Bis bald!")

    def main_loop(self):
        while True:
            print(f"\n--- Hauptmenü (angemeldet: {self.current_user}) ---")
            print("1) Powi")
            print("2) Wirtschaft")
            print("3) Politik")
            print("4) Sport")
            print("5) Technologie")
            print("6) Weltweit")
            print("7) Allgemein")
            print("8) Analyzer / Trends")
            print("9) Suche")
            print("10) Export Kategorie -> JSON")
            print("11) Einstellungen")
            print("0) Abmelden & Beenden")
            cmd = input("Auswahl: ").strip()
            if cmd in [str(i) for i in range(1,8)]:
                cats = list(self.dataset.keys())
                cat = cats[int(cmd)-1]
                self.show_category(cat)
            elif cmd == "8":
                self.analyzer_menu()
            elif cmd == "9":
                self.search_menu()
            elif cmd == "10":
                self.export_category()
            elif cmd == "11":
                self.settings_menu()
            elif cmd == "0":
                print("Abmelden...")
                break
            else:
                print("Ungültige Eingabe.")

    def show_category(self, category):
        arts = list(self.dataset.get(category, []))
        sort_mode = self.settings.get("sort_mode", "neueste")
        if sort_mode in ("wichtig","importance"):
            arts.sort(key=lambda x: x.get("importance", 0), reverse=True)
        else:
            def pd(a):
                try:
                    return datetime.strptime(a.get("date","1970-01-01"), "%Y-%m-%d")
                except Exception:
                    return datetime(1970,1,1)
            arts.sort(key=lambda x: pd(x), reverse=True)
        page_size = 5
        page = 0
        total_pages = max(1, math.ceil(len(arts)/page_size))
        while True:
            start = page*page_size
            end = start + page_size
            print(f"\n--- {category} (Seite {page+1}/{total_pages}) ---")
            for i, a in enumerate(arts[start:end], start=1):
                print(f"{i}) {a['title']}  [{a['date']}]  W:{a['importance']}")
            print("Befehle: n=next, p=prev, v#=view z.B. v2, t=headlines, b=back")
            cmd = input("Befehl: ").strip().lower()
            if cmd == "n":
                if page+1 < total_pages:
                    page += 1
                else:
                    print("Letzte Seite.")
            elif cmd == "p":
                if page > 0:
                    page -= 1
                else:
                    print("Erste Seite.")
            elif cmd.startswith("v"):
                try:
                    idx = int(cmd[1:]) - 1
                    art = arts[start + idx]
                    self.view_article(art)
                except Exception:
                    print("Ungültige Auswahl. Beispiel: 'v2'")
            elif cmd == "t":
                # show top headlines via analyzer (lazy)
                tops = self.analyzer.top_headlines(category, n=10)
                print(f"\nTop Headlines in {category}:")
                for r, (score, art) in enumerate(tops, start=1):
                    print(f"{r}. [{score}] {art['title']} ({art['date']}) W:{art['importance']}")
                input("Enter zum Zurück.")
            elif cmd == "b":
                return
            else:
                print("Unbekannter Befehl.")

    def view_article(self, article):
        print("\n--- Artikel ---")
        print(f"Titel: {article.get('title')}")
        print(f"Datum: {article.get('date')}  |  Wichtigkeit: {article.get('importance')}")
        print(f"Link: {article.get('link')}\n")
        print(article.get('description'))
        # On demand analysis (fast)
        s = sentiment_score_text(article.get('title','') + " " + article.get('description',''))
        print(f"\n[Analyse] Sentiment-Score (Proxy): {s}")
        # headline score (needs analyzer.initialize for idf)
        self.analyzer.initialize()
        hs = score_headline(article, idf_map=self.analyzer.idf_map, important_terms=self.analyzer.get_global_top(8))
        print(f"[Analyse] Headline-Score: {hs}/100")
        input("Enter zum Zurück.")

    def analyzer_menu(self):
        while True:
            print("\n--- Analyzer / Trends ---")
            print("1) Globale Top-Keywords")
            print("2) Top-Terme pro Kategorie")
            print("3) Kategorie-Summaries")
            print("4) Sentiment-Verteilung (global oder Kategorie)")
            print("5) Trend Zeitreihe (Kategorie)")
            print("0) Zurück")
            c = input("Auswahl: ").strip()
            if c == "1":
                print("Globale Top-Keywords:")
                print(", ".join(self.analyzer.get_global_top(30)))
            elif c == "2":
                for cat in self.dataset.keys():
                    s = self.analyzer.get_cat_summary(cat)
                    print(f"\n{cat}: {', '.join(s.get('top_terms',[])[:10])}")
            elif c == "3":
                for cat in self.dataset.keys():
                    s = self.analyzer.get_cat_summary(cat)
                    print(f"\n{cat}: AvgSent={s.get('avg_sentiment')} | AvgImp={s.get('avg_importance')}")
            elif c == "4":
                cat = input("Kategorie (leer=global): ").strip()
                res = self.analyzer.sentiment_distribution(cat if cat else None)
                print("Sentiment-Verteilung:", res)
            elif c == "5":
                cat = input("Kategorie (Name): ").strip()
                ts = self.analyzer.trend_series(cat)
                if not ts:
                    print("Keine Zeitdaten.")
                else:
                    for m, cnt in ts:
                        print(f"{m}: {cnt} Artikel")
            elif c == "0":
                return
            else:
                print("Ungültig.")

    def search_menu(self):
        q = input("Suchbegriff (Titel/Beschreibung): ").strip().lower()
        if not q:
            print("Leere Suche.")
            return
        hits = []
        for cat, arts in self.dataset.items():
            for a in arts:
                if q in a.get("title","").lower() or q in a.get("description","").lower():
                    hits.append((cat, a))
        if not hits:
            print("Keine Treffer.")
            return
        print(f"{len(hits)} Treffer:")
        for i, (cat, a) in enumerate(hits, start=1):
            print(f"{i}) [{cat}] {a['title']} ({a['date']}) W:{a['importance']}")
        sel = input("Nummer öffnen (Enter=Abbrechen): ").strip()
        if sel:
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(hits):
                    self.view_article(hits[idx][1])
            except Exception:
                print("Ungültig.")

    def export_category(self):
        cats = list(self.dataset.keys())
        for i, c in enumerate(cats, start=1):
            print(f"{i}) {c}")
        sel = input("Kategorie (Nummer) oder 0 abbrechen: ").strip()
        if sel == "0" or not sel:
            return
        try:
            idx = int(sel)-1
            if not (0 <= idx < len(cats)):
                print("Ungültig.")
                return
            cat = cats[idx]
            fname = f"export_{cat.replace(' ', '_')}.json"
            safe_save_json(fname, self.dataset[cat])
            print(f"Exportiert: {fname}")
        except Exception as e:
            print("Fehler:", e)

    def settings_menu(self):
        cur = self.settings.get("sort_mode", "neueste")
        print(f"Aktuelle Sortierung: {cur} (Optionen: neueste / wichtig)")
        new = input("Neue Sortierung (leer = behalten): ").strip().lower()
        if not new:
            print("Keine Änderung.")
            return
        if new in ("neueste","wichtig","importance","date"):
            if new == "date": new = "neueste"
            if new == "importance": new = "wichtig"
            self.settings["sort_mode"] = new
            safe_save_json(SETTINGS_FILE, self.settings)
            print("Gespeichert.")
        else:
            print("Ungültige Option.")

# -----------------------
# Startpunkt
# -----------------------
def main():
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()
