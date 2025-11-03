# -*- coding: utf-8 -*-
"""
Lumina News - Offline CLI (Single-file)
Features:
 - 7 Kategorien x ~10 realistische Artikel (fest eingebettet)
 - Benutzerverwaltung (users.json)
 - Einstellungen (settings.json)
 - Lazily-evaluierter, lokaler News-Analyzer:
     * Top-Keywords (global & per Kategorie)
     * Sentiment (lexikonbasiert, deutsch)
     * Headline-Scoring (0-100)
     * Trend-Zeitreihen nach Monat (YYYY-MM)
 - Cleanes CLI-Menü, Paging, Suche, Export
 - Keine externen Module (nur Standardlib)
Usage:
    python main.py
"""

import json
import os
import sys
import math
import re
from datetime import datetime
from collections import Counter, defaultdict

# ------------------------------
# Dateipfade
# ------------------------------
USERS_FILE = "users.json"
SETTINGS_FILE = "settings.json"

# ------------------------------
# Hilfsfunktionen: JSON IO sicher
# ------------------------------
def safe_load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default
    except Exception as e:
        print(f"[WARN] Fehler beim Laden von {path}: {e}")
        return default

def safe_save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Fehler beim Speichern von {path}: {e}")

# ------------------------------
# Dataset: 7 Kategorien x 10 Artikel (realistisch formuliert)
# ------------------------------
def build_news_dataset():
    # Jede Nachricht hat: title, description (mehrere Sätze), link, importance (1-5), date "YYYY-MM-DD"
    # Die Texte hier sind realistisch gehalten, ideal für offline-Analysen.
    data = {
        "Powi": [
            {"title":"Neue Lehrpläne stärken kritisches Denken",
             "description":"Das Kultusministerium hat überarbeitete Lehrpläne vorgestellt, die kritisches Denken und Medienkompetenz in den Mittelpunkt stellen. "
                          "Schwerpunkte liegen auf Quellenkritik, Projektlernen und digitaler Kompetenz. "
                          "Lehrkräfte erhalten Fortbildungen, um die neuen Inhalte umzusetzen. "
                          "Pilotprojekte laufen bereits in mehreren Bundesländern. "
                          "Eltern- und Schülervertretungen wurden in die Erarbeitung einbezogen.",
             "link":"https://example.org/powi/lehrplaene","importance":5,"date":"2025-09-15"},
            {"title":"Digitaler Unterricht wird weiter ausgebaut",
             "description":"Ein Förderprogramm stellt Schulträgern Mittel für Infrastruktur und Endgeräte bereit. "
                          "Lehrkräfte sollen schrittweise in digitalen Didaktiken geschult werden. "
                          "Datenschutz und pädagogische Konzepte gelten als zentrale Punkte. "
                          "Die Pilotphase startet noch dieses Jahr in 120 Schulen. "
                          "Ziel ist ein nachhaltiger Ausbau der digitalen Bildung.",
             "link":"https://example.org/powi/digital","importance":4,"date":"2025-10-01"},
            {"title":"Schulfahrten: Zuschüsse ausgeweitet",
             "description":"Bund und Länder haben vereinbart, Zuschüsse für mehrtägige Schulfahrten auszuweiten. "
                          "Ziel ist, soziale Teilhabe unabhängig vom Einkommen zu ermöglichen. "
                          "Anträge sollen künftig digitalisiert und vereinfacht werden. "
                          "Kulturelle und naturnahe Programme sind vorrangig vorgesehen. "
                          "Verbände begrüßen die Maßnahme, fordern aber zusätzliche Mittel für Inklusion.",
             "link":"https://example.org/powi/schulfahrten","importance":3,"date":"2025-07-20"},
            {"title":"MINT-Förderung: Talente früh identifizieren",
             "description":"Ein neues Programm unterstützt MINT-Angebote an Schulen und Workshops für Schüler. "
                          "Mentoring, Wettbewerbe und Kooperationen mit Hochschulen sind Bestandteil. "
                          "Besonders Mädchen und unterrepräsentierte Gruppen sollen gefördert werden. "
                          "Regionale Netzwerke stärken die Umsetzung. "
                          "Langfristiges Ziel ist die Sicherung von Fachkräften.",
             "link":"https://example.org/powi/mint","importance":4,"date":"2025-05-05"},
            {"title":"Schulsozialarbeit wird ausgebaut",
             "description":"Aufgrund gestiegener Nachfrage werden zusätzliche Stellen für Schulsozialarbeit geschaffen. "
                          "Prävention und psychosoziale Unterstützung stehen im Mittelpunkt. "
                          "Kooperationen mit Jugendämtern und Beratungsstellen sind geplant. "
                          "Die Maßnahme soll Fehlzeiten reduzieren und Integration fördern. "
                          "Erste Evaluationen melden positive Effekte.",
             "link":"https://example.org/powi/sozialarbeit","importance":4,"date":"2025-04-12"},
            {"title":"Berufsorientierung: Pflichtmodule an Gymnasien",
             "description":"Gymnasien führen verpflichtende Module zur Berufsorientierung und Bewerbungstrainings ein. "
                          "Unternehmen bieten Praktika und Workshops an. "
                          "Ziel ist eine bessere Vorbereitung auf Studium und Arbeitswelt. "
                          "Die ersten Pilotkurse starten im kommenden Schuljahr. "
                          "Schulen berichten von verstärkter Nachfrage seitens der Schüler.",
             "link":"https://example.org/powi/berufsorientierung","importance":3,"date":"2025-06-10"},
            {"title":"Sprachförderung für Grundschulen erweitert",
             "description":"Zusätzliche Ressourcen fließen in frühe Sprachförderprogramme, besonders in mehrsprachigen Regionen. "
                          "Lehrkräfte bekommen Material und Trainings, um gezielt zu fördern. "
                          "Frühe Interventionen sollen Lernrückstände verhindern. "
                          "Elternarbeit wird als wichtiger Faktor gesehen. "
                          "Erste Ergebnisse deuten auf geringere Defizite hin.",
             "link":"https://example.org/powi/sprach","importance":3,"date":"2025-02-18"},
            {"title":"Schulbauoffensive: Klassenzimmer modernisieren",
             "description":"Das Programm sieht die Sanierung vieler Schulgebäude und energieeffiziente Modernisierung vor. "
                          "Digitale Ausstattung ist integraler Bestandteil. "
                          "Kommunen erhalten finanzielle Unterstützung für Planungsphasen. "
                          "Priorität haben baulich dringende Standorte. "
                          "Projekte sollen in den nächsten drei Jahren umgesetzt werden.",
             "link":"https://example.org/powi/schulbau","importance":5,"date":"2025-03-28"},
            {"title":"Nachhaltigkeitswettbewerb fördert Schulideen",
             "description":"Ein Wettbewerb prämiert Projekte zu Energieeinsparung, Recycling und Bildung für nachhaltige Entwicklung. "
                          "Gewinner erhalten Finanzierung und Mentoren. "
                          "Die Initiative stärkt praktisches Lernen und Verantwortungsbewusstsein. "
                          "Schulen vernetzen sich über regionale Plattformen. "
                          "Viele Projekte zeigen direkte Einsparungen im Alltag.",
             "link":"https://example.org/powi/nachhaltigkeit","importance":2,"date":"2025-01-31"},
            {"title":"Hybridunterricht: Pilotphase zeigt gemischte Ergebnisse",
             "description":"Einige Schulen testen hybridere Lernkonzepte mit Präsenz- und Onlinephasen. "
                          "Schüler und Lehrkräfte berichten von mehr Flexibilität, aber auch technischen Herausforderungen. "
                          "Evaluationen sollen Best-Practices herausarbeiten. "
                          "Digitale Coaches werden zur Unterstützung eingesetzt. "
                          "Langfristige Modelle bleiben noch zu definieren.",
             "link":"https://example.org/powi/hybrid","importance":3,"date":"2025-11-03"},
        ],
        "Wirtschaft": [
            {"title":"Industrieproduktion zeigt Aufwärtstrend",
             "description":"Die Industrieproduktion verzeichnet moderate Zuwächse, vor allem im Maschinenbau. "
                          "Investitionen in Automatisierung und Effizienz steigen. "
                          "Analysten warnen vor möglichen Lieferkettenrisiken. "
                          "Exportnachfrage bleibt ein Treiber für Wachstum. "
                          "Unternehmen investieren stärker in Digitalisierung.",
             "link":"https://example.org/wirtschaft/industrie","importance":4,"date":"2025-10-20"},
            {"title":"Mittelstand investiert in KI-Lösungen",
             "description":"Viele Mittelständler setzen KI ein, um Prozesse zu optimieren und Service zu verbessern. "
                          "Pilotprojekte werden durch Förderprogramme unterstützt. "
                          "Fachkräftesicherung und Datenschutz sind zentrale Herausforderungen. "
                          "Unternehmen verzeichnen erste Effizienzgewinne. "
                          "Die Nachfrage nach KI-Consulting steigt.",
             "link":"https://example.org/wirtschaft/ki","importance":4,"date":"2025-09-05"},
            {"title":"Arbeitsmarkt bleibt robust",
             "description":"Trotz konjunktureller Spannungen zeigt der Arbeitsmarkt Stabilität. "
                          "Zahlreiche offene Stellen bestehen besonders in IT, Handwerk und Pflege. "
                          "Weiterbildungsprogramme werden ausgebaut, um Fachkräfte zu sichern. "
                          "Gewerkschaften verhandeln über Tarifabschlüsse in mehreren Branchen. "
                          "Die Beschäftigungsdynamik bleibt insgesamt positiv.",
             "link":"https://example.org/wirtschaft/arbeitsmarkt","importance":3,"date":"2025-08-14"},
            {"title":"Inflationsrate stabilisiert sich",
             "description":"Die Inflationsrate hat sich gegenüber dem Vorjahr abgeschwächt. "
                          "Energiepreise und Nahrungsmittel bleiben regional volatil. "
                          "Zentralbanken signalisieren vorsichtigen Optimismus. "
                          "Verbraucher spüren erste Entlastungen im Alltag. "
                          "Langfristige Stabilität hängt von globalen Rohstoffpreisen ab.",
             "link":"https://example.org/wirtschaft/inflation","importance":4,"date":"2025-07-30"},
            {"title":"Startups sichern sich Finanzierung für grüne Technologien",
             "description":"Investoren zeigen verstärktes Interesse an Startups mit nachhaltigen Lösungen. "
                          "Projekte in Energiespeicherung und nachhaltiger Mobilität erhalten Mittel. "
                          "Acceleratoren unterstützen Skalierung und Markteintritt. "
                          "Politische Anreize ergänzen private Finanzierung. "
                          "Erste Skalierungseffekte sind sichtbar.",
             "link":"https://example.org/wirtschaft/startups","importance":3,"date":"2025-06-22"},
            {"title":"Exportsektor profitiert von Asien-Nachfrage",
             "description":"Deutsche Exporte in ausgewählte asiatische Märkte verzeichnen ein Plus. "
                          "Maschinenbau und Spezialchemie sind gefragt. "
                          "Unternehmen stärken regionale Vertriebsnetzwerke. "
                          "Wechselkursschwankungen bleiben ein Risikofaktor. "
                          "Analysten sehen Chancen, aber auch intensiven Wettbewerb.",
             "link":"https://example.org/wirtschaft/export","importance":3,"date":"2025-05-12"},
            {"title":"Immobilienmarkt zeigt regionale Divergenz",
             "description":"Während Ballungsräume hohe Preise halten, normalisiert sich der Markt in Randregionen. "
                          "Förderprogramme für bezahlbares Wohnraum werden ausgeweitet. "
                          "Bauunternehmen klagen über Material- und Personalmangel. "
                          "Die politische Debatte um Mietspolitik bleibt intensiv. "
                          "Marktveränderungen sind lokal sehr unterschiedlich.",
             "link":"https://example.org/wirtschaft/immobilien","importance":3,"date":"2025-04-01"},
            {"title":"Lieferketten setzen vermehrt auf Resilienz",
             "description":"Unternehmen diversifizieren Zulieferer und setzen verstärkt auf Nearshoring. "
                          "Digitale Tools verbessern Transparenz entlang der Lieferketten. "
                          "Kostendruck und Qualitätssicherung bleiben zentrale Herausforderungen. "
                          "Strategische Entscheidungen variieren branchenabhängig. "
                          "Eine robustere Struktur soll Ausfälle mindern.",
             "link":"https://example.org/wirtschaft/lieferketten","importance":3,"date":"2025-03-18"},
            {"title":"Energieeffizienz wird zur Unternehmensstrategie",
             "description":"Steigende Energiekosten treiben Investitionen in Effizienzmaßnahmen an. "
                          "Abwärmenutzung und Energiemanagement gewinnen an Bedeutung. "
                          "Förderprogramme erleichtern die Umsetzung größerer Projekte. "
                          "Langfristig sollen Betriebskosten gesenkt werden. "
                          "Nachhaltigkeitskennzahlen werden wichtiger für Investoren.",
             "link":"https://example.org/wirtschaft/energie","importance":2,"date":"2025-02-10"},
            {"title":"Finanzbildung: Schulen kooperieren mit Institutionen",
             "description":"Programme zur Finanzbildung werden in Schulen vermehrt angeboten. "
                          "Workshops und Planspiele vermitteln praktische Kenntnisse. "
                          "Kritiker fordern neutrale Inhalte, während Befürworter praktische Relevanz sehen. "
                          "Die Nachfrage nach solchen Angeboten steigt. "
                          "Projekte werden regional skaliert.",
             "link":"https://example.org/wirtschaft/finanzbildung","importance":2,"date":"2025-01-05"},
        ],
        "Politik": [
            {"title":"Koalitionsgespräche erreichen finale Phase",
             "description":"Nach intensiven Verhandlungen stehen die Koalitionspartner vor dem Abschluss. "
                          "Kernpunkte betreffen Klima, Soziales und Infrastrukturfinanzierung. "
                          "Beide Seiten zeigen Kompromissbereitschaft bei Teilen des Pakets. "
                          "Die Öffentlichkeit und Medien verfolgen die Gespräche aufmerksam. "
                          "Ein Abschluss wird in den nächsten Tagen erwartet.",
             "link":"https://example.org/politik/koalition","importance":5,"date":"2025-11-01"},
            {"title":"Transparenzgesetz: Lobbykontakte im Fokus",
             "description":"Ein Entwurf sieht erweiterte Offenlegungspflichten für Lobbykontakte vor. "
                          "Ziel ist mehr Nachvollziehbarkeit politischer Einflussnahme. "
                          "Verbände kritisieren erhöhten Verwaltungsaufwand. "
                          "Befürworter sehen einen Gewinn an Vertrauen in politische Prozesse. "
                          "Das Gesetz durchläuft mehrere Beratungsstufen.",
             "link":"https://example.org/politik/transparenz","importance":4,"date":"2025-07-02"},
            {"title":"Datenschutz & KI: Parlament diskutiert Anpassungen",
             "description":"Parlamentarische Beratungen zu Datenschutzregelungen im Kontext von KI haben begonnen. "
                          "Die Balance zwischen Innovation und Grundrechtsschutz steht im Mittelpunkt. "
                          "Experten und Verbände werden angehört. "
                          "Branchenspezifische Lösungen bleiben umstritten. "
                          "Weitere Hearings sind terminiert.",
             "link":"https://example.org/politik/datenschutz","importance":5,"date":"2025-05-19"},
            {"title":"Kommunen erhalten mehr Planungshilfe",
             "description":"Bundesmittel unterstützen Kommunen bei Investitions- und Digitalisierungsprojekten. "
                          "Ziel ist die langfristige Handlungsfähigkeit der Verwaltungen. "
                          "Besonders strukturschwache Regionen profitieren von Zuwendungen. "
                          "Planungsmittel beschleunigen Projektzyklen. "
                          "Kommunen begrüßen die Unterstützung.",
             "link":"https://example.org/politik/kommunen","importance":3,"date":"2025-10-18"},
            {"title":"Integration: Programme für Arbeitsmarktintegration",
             "description":"Ausbau von Sprachkursen und Qualifizierungsmaßnahmen für Zugewanderte ist geplant. "
                          "Kooperationen mit Betrieben erleichtern Praktika und Ausbildungseinstiege. "
                          "Ziel ist nachhaltige Teilhabe und Beschäftigung. "
                          "Regionale Initiativen werden verstärkt gefördert. "
                          "Erste Pilotprojekte berichten von Erfolgen.",
             "link":"https://example.org/politik/integration","importance":3,"date":"2025-06-25"},
            {"title":"Innenpolitik: Cyberabwehr gestärkt",
             "description":"Bund und Länder erhöhen Ressourcen für Cyberabwehr und IT-Sicherheit. "
                          "Kritische Infrastrukturen stehen im Fokus. "
                          "Zusammenarbeit mit Forschung und Wirtschaft wird ausgebaut. "
                          "Ziel ist besserer Schutz vor Attacken. "
                          "Ausbildungsplätze für Spezialisten werden ausgebaut.",
             "link":"https://example.org/politik/cyber","importance":4,"date":"2025-04-10"},
            {"title":"Wahlrecht-Debatte um kommunales Wahlalter",
             "description":"Diskussionen über eine mögliche Absenkung des Wahlalters auf kommunaler Ebene werden geführt. "
                          "Befürworter erhoffen mehr Jugendbeteiligung. "
                          "Gegner warnen vor unzureichender Reife. "
                          "Pilottests in Gemeinden könnten erste Erkenntnisse liefern. "
                          "Die Debatte bleibt kontrovers.",
             "link":"https://example.org/politik/wahlrecht","importance":2,"date":"2025-03-03"},
            {"title":"Rentenkommission legt Zwischenbericht vor",
             "description":"Eine Kommission präsentiert Optionen für die Stabilisierung des Rentensystems. "
                          "Diskutiert werden flexible Übergänge und Finanzierungsmechanismen. "
                          "Breiter gesellschaftlicher Dialog ist geplant. "
                          "Konkrete Vorschläge sollen im nächsten Jahr folgen. "
                          "Stakeholder zeigen unterschiedliche Perspektiven.",             "link":"https://example.org/politik/rente","importance":4,"date":"2025-02-14"},
            {"title":"Außenpolitik: Dialog mit Nachbarn intensiviert",
             "description":"Die Regierung hat den diplomatischen Austausch mit Nachbarstaaten vertieft. "
                          "Schwerpunkte sind Handel, Forschung und Energie. "
                          "Regelmäßige Ministertreffen sollen Vertrauen aufbauen. "
                          "Analysten sehen strategische Vorteile. "
                          "Abkommen sollen in den kommenden Monaten finalisiert werden.",
             "link":"https://example.org/politik/aussen","importance":3,"date":"2025-01-21"},
            {"title":"Sozialpolitik: Programme gegen Armut",
             "description":"Neue regionale Programme unterstützen vulnerable Haushalte. "
                          "Ziel ist die Integration in Arbeit und Bildung. "
                          "Kooperationen mit NGOs sollen Wirkung verstärken. "
                          "Pilotprojekte zeigen erste positive Ergebnisse. "
                          "Weitere Ausweitungen sind in Planung.",
             "link":"https://example.org/politik/sozial","importance":3,"date":"2025-11-02"},
        ],
        "Sport": [
            {"title":"Nationalteam gewinnt wichtiges Qualifikationsspiel",
             "description":"Das Nationalteam sicherte sich einen knappen Sieg dank taktischer Disziplin. "
                          "Der Trainer lobt die Mannschaftsleistung. "
                          "Fans feiern den Erfolg landesweit. "
                          "Die Partie stärkt die Chancen in der Gruppenphase. "
                          "Ausblick bleibt positiv für kommende Spiele.",
             "link":"https://example.org/sport/qualifikation","importance":5,"date":"2025-10-31"},
            {"title":"Bundesligist investiert in Nachwuchsprogramm",
             "description":"Ein Spitzenclub investiert stark in sein Nachwuchsleistungszentrum. "
                          "Ziel ist, Talente systematisch zu entwickeln. "
                          "Kooperationen mit Schulen und Vereinen sind Teil der Strategie. "
                          "Trainer betonen langfristige Perspektiven. "
                          "Erste Erfolge zeigen sich in Jugendwettbewerben.",
             "link":"https://example.org/sport/nachwuchs","importance":3,"date":"2025-09-12"},
            {"title":"Olympia-Vorbereitung läuft planmäßig",
             "description":"Athleten zeigen starke Form in Vorbereitungswettkämpfen. "
                          "Trainer optimieren Trainingszyklen. "
                          "Verbände sind zufrieden mit der bisherigen Planung. "
                          "Medaillenkandidaten präsentieren überzeugende Leistungen. "
                          "Die Hoffnungen sind groß für die Spiele.",
             "link":"https://example.org/sport/olympia","importance":4,"date":"2025-08-01"},
            {"title":"Tennis: Überraschungssieger begeistert Publikum",
             "description":"Ein Newcomer gewann überraschend ein großes Turnier. "
                          "Der Erfolg bringt wichtige Ranglistenpunkte und Aufmerksamkeit. "
                          "Trainer loben mentale Stärke und Technik. "
                          "Sponsoren zeigen Interesse. "
                          "Der Spieler könnte ein neuer Star werden.",
             "link":"https://example.org/sport/tennis","importance":3,"date":"2025-07-18"},
            {"title":"Basketball: Entscheidungsspiel sorgt für Spannung",
             "description":"Ein Entscheidungsspiel entschied über die Playoff-Platzierung in der Bundesliga. "
                          "Die Partie ging in die Verlängerung und bot zahlreiche Höhepunkte. "
                          "Fans füllten die Halle bis auf den letzten Platz. "
                          "Experten loben die taktische Tiefe der Begegnung. "
                          "Die Playoffs versprechen weitere intensive Duelle.",
             "link":"https://example.org/sport/basketball","importance":3,"date":"2025-06-11"},
            {"title":"Handball: Auftaktsieg schafft Zuversicht",
             "description":"Die Nationalmannschaft startete erfolgreich in die Saison. "
                          "Die Defensive zeigte starke Stabilität. "
                          "Junge Talente bekamen Einsatzzeiten. "
                          "Trainer betont Teamchemie als Schlüssel. "
                          "Fans freuen sich auf die kommenden Aufgaben.",
             "link":"https://example.org/sport/handball","importance":2,"date":"2025-05-09"},
            {"title":"Radsport: Etappensieg verändert Gesamtwertung",
             "description":"Ein spektakulärer Antritt in der Schlussetappe brachte einem Fahrer den Etappensieg. "
                          "Die Gesamtwertung veränderte sich dadurch signifikant. "
                          "Teams planen taktische Antworten für die Berge. "
                          "Die Zuschauer erlebten packende Duelle. "
                          "Weitere Etappen versprechen Spannung.",
             "link":"https://example.org/sport/radsport","importance":3,"date":"2025-04-22"},
            {"title":"Leichtathletik: Nachwuchsmeeting mit Bestleistungen",
             "description":"Bei einem Meeting erzielten junge Athleten mehrere persönliche Bestmarken. "
                          "Trainer sehen einen positiven Trend für kommende Großereignisse. "
                          "Sprint- und Sprungdisziplinen fielen besonders auf. "
                          "Die Veranstaltung stärkte den Austausch zwischen Vereinen. "
                          "Initiativen zur Talentsichtung werden ausgeweitet.",
             "link":"https://example.org/sport/leichtathletik","importance":2,"date":"2025-03-30"},
            {"title":"Eishockey: Überraschungsteam zieht in Playoffs ein",
             "description":"Ein Aufsteiger erreichte überraschend die Playoffs nach starker Teamleistung. "
                          "Fans feierten die Saison als großen Erfolg. "
                          "Trainer lobten das kollektive Engagement. "
                          "In den Playoffs hoffen Beobachter auf weitere Überraschungen. "
                          "Die Clubentwicklung gilt als vorbildlich.",
             "link":"https://example.org/sport/eishockey","importance":2,"date":"2025-02-12"},
            {"title":"Lokalderby bringt Emotionen und volle Stadien",
             "description":"Ein lokales Derby sorgte für volle Zuschauerränge und hohe Emotionen. "
                          "Die Begegnung verlief intensiv und fair. "
                          "Sicherheitskonzepte wurden erfolgreich umgesetzt. "
                          "Organisatoren ziehen positive Bilanz. "
                          "Die Rivalität bleibt sportlich spannend.",
             "link":"https://example.org/sport/derby","importance":3,"date":"2025-01-18"},
        ],
        "Technologie": [
            {"title":"Neuer KI-Chip erhöht Energieeffizienz",
             "description":"Ein Hersteller kündigt einen KI-Chip an, der die Rechenleistung pro Watt deutlich verbessert. "
                          "Rechenzentren und Edge-Anwendungen sollen profitieren. "
                          "Partnerschaften mit Cloud-Anbietern sind angekündigt. "
                          "Tests laufen in ausgewählten Rechenzentren. "
                          "Die Markteinführung wird für 2026 erwartet.",
             "link":"https://example.org/tech/ki-chip","importance":5,"date":"2025-10-30"},
            {"title":"5G-Privatnetze stärken Industrie 4.0",
             "description":"Private 5G-Netze werden in Produktionsstätten häufiger eingesetzt. "
                          "Echtzeitsteuerung und vernetzte Sensorik profitieren besonders. "
                          "Regulatorische Fragen zur Frequenzvergabe bleiben Thema. "
                          "Pilotprojekte zeigen Effizienzsteigerungen. "
                          "Skalierung ist die nächste Herausforderung.",
             "link":"https://example.org/tech/5g","importance":4,"date":"2025-08-20"},
            {"title":"Quantenforschung macht Fortschritte bei Fehlerkorrektur",
             "description":"Neue Methoden zur Fehlerkorrektur bringen die praktische Quantenverarbeitung näher. "
                          "Forscherteams berichten über signifikante Verbesserungen. "
                          "Industriepartner prüfen mögliche Anwendungen. "
                          "Konkrete kommerzielle Systeme sind noch Zukunftsmusik. "
                          "Die Forschung bleibt anspruchsvoll, aber vielversprechend.",
             "link":"https://example.org/tech/quanten","importance":5,"date":"2025-07-09"},
            {"title":"Open-Source-Tools vereinfachen Testautomatisierung",
             "description":"Community-Projekte liefern modulare Tools für Entwickler und Tester. "
                          "CI/CD-Pipelines werden dadurch flexibler und schneller. "
                          "Contributors aus vielen Ländern tragen bei. "
                          "Unternehmen profitieren von geringeren Time-to-Market. "
                          "Adoption wächst besonders in Startups.",
             "link":"https://example.org/tech/opensource","importance":3,"date":"2025-06-16"},
            {"title":"Cloudanbieter bieten Nachhaltigkeits-Tools",
             "description":"Neue Tools messen Workload-Emissionen und helfen bei Optimierung. "
                          "Unternehmen verwenden die Daten für ESG-Reporting. "
                          "Standardisierte Metriken vereinfachen Vergleiche. "
                          "Erste Kunden berichten von Einsparungen. "
                          "Die Branche diskutiert weitere Standards.",
             "link":"https://example.org/tech/cloud","importance":3,"date":"2025-03-12"},
            {"title":"Robotics: Service-Roboter in Lagerlogistik",
             "description":"Autonome Roboter unterstützen Kommissionierung und Transporte. "
                          "Integration in Lagerverwaltungssysteme optimiert Prozesse. "
                          "Arbeitskräfte werden für höherwertige Tätigkeiten umgeschult. "
                          "Pilotprojekte zeigen Zeit- und Fehlerreduktion. "
                          "Wirtschaftliche Effekte werden gemessen.",
             "link":"https://example.org/tech/robotics","importance":3,"date":"2025-04-18"},
            {"title":"Bildverarbeitung verbessert medizinische Diagnostik",
             "description":"KI-Modelle liefern verbesserte Ergebnisse bei der Analyse medizinischer Bilder. "
                          "Ärzte nutzen Systeme als Unterstützung bei Diagnosen. "
                          "Regulatorische Prüfungen laufen derzeit. "
                          "Pilotprojekte in Kliniken zeigen vielversprechende Ergebnisse. "
                          "Die Systeme sind als Assistenz gedacht, nicht als Ersatz.",
             "link":"https://example.org/tech/med","importance":5,"date":"2025-02-25"},
            {"title":"Edge-Computing reduziert Latenz in Anwendungen",
             "description":"Mehr Anwendungen verlagern Verarbeitung an die Edge, um Latenz zu verringern. "
                          "Smart-City- und Industrieanwendungen profitieren besonders. "
                          "Heterogene Hardware ist technische Herausforderung. "
                          "Entwickler passen Architekturen entsprechend an. "
                          "Energieeffizienz bleibt ein wichtiges Thema.",
             "link":"https://example.org/tech/edge","importance":3,"date":"2025-01-16"},
            {"title":"Zero-Trust-Ansätze verbreiten sich in Unternehmen",
             "description":"Unternehmen setzen vermehrt auf Zero-Trust-Architekturen zur Absicherung. "
                          "Identitäts- und Rechteverwaltung stehen im Mittelpunkt. "
                          "Migrationen sind komplex, aber bieten langfristig bessere Sicherheit. "
                          "Beratung und Schulung sind gefragte Dienstleistungen. "
                          "Modelle werden schrittweise eingeführt.",
             "link":"https://example.org/tech/zero-trust","importance":4,"date":"2025-11-02"},
            {"title":"Open-Data-Initiativen fördern Forschung und Innovation",
             "description":"Institutionen stellen mehr Datensets offen zur Nutzung durch Forschung und Startups. "
                          "Transparenz und Reproduzierbarkeit werden dadurch gestärkt. "
                          "Forscherteams entwickeln neue Anwendungen auf Basis der Daten. "
                          "Ethik und Zugangsregelungen werden parallel diskutiert. "
                          "Die Initiativen unterstützen langfristig Innovation.",
             "link":"https://example.org/tech/opendata","importance":3,"date":"2025-09-10"},
        ],
        "Weltweit": [
            {"title":"Internationale Klimapartnerschaften vereinbart",
             "description":"Staaten verständigen sich auf Kooperationen zur Emissionsreduktion und Technologietransfer. "
                          "Finanzierung für Anpassungsmaßnahmen ist ein wichtiger Bestandteil. "
                          "Monitoring-Mechanismen sollen Fortschritt sichern. "
                          "Entwicklungsländer erhalten gezielte Unterstützung. "
                          "Die Initiative wird international begrüßt.",
             "link":"https://example.org/welt/klima","importance":5,"date":"2025-10-05"},
            {"title":"Friedensgespräche gestartet",
             "description":"Diplomaten haben Gespräche zwischen Konfliktparteien initiiert, um eine Deeskalation zu ermöglichen. "
                          "Humanitäre Zugänge und Gefangenenaustausch sind zentrale Punkte. "
                          "Der Prozess gilt als fragil, aber notwendig. "
                          "Internationale Organisationen unterstützen Vermittlungsbemühungen. "
                          "Beobachter zeigen vorsichtigen Optimismus.",
             "link":"https://example.org/welt/frieden","importance":5,"date":"2025-09-22"},
            {"title":"Weltbank finanziert Infrastrukturprojekte",
             "description":"Neue Kreditlinien unterstützen nachhaltige Infrastruktur in Entwicklungsregionen. "
                          "Projekte umfassen Wasser, Energie und Transport. "
                          "Umweltprüfungen begleiten die Maßnahmen. "
                          "Transparenzkriterien sollen Vergabeverfahren sichern. "
                          "Die Vorhaben zielen auf Beschäftigung und Wachstum ab.",
             "link":"https://example.org/welt/weltbank","importance":4,"date":"2025-08-11"},
            {"title":"Pandemieprävention: Impfstofflager ausgebaut",
             "description":"Internationale Kooperationen bauen strategische Lager für Impfstoffe und medizinische Güter auf. "
                          "Schnelle Verfügbarkeit in Krisenzeiten ist Ziel. "
                          "Logistische Netzwerke und Kühlketten werden optimiert. "
                          "Finanzierung erfolgt durch multilaterale Fonds. "
                          "Regionale Kooperationen verbessern Verteilungskapazitäten.",
             "link":"https://example.org/welt/impfstoffe","importance":4,"date":"2025-06-05"},
            {"title":"Handel: Regionale Abkommen neu verhandelt",
             "description":"Länder verhandeln die Modernisierung von Handelsabkommen mit Fokus auf digitale Wirtschaft. "
                          "Zollfragen und Nachhaltigkeitsstandards werden diskutiert. "
                          "Unternehmer erhoffen sich klarere Rahmenbedingungen. "
                          "Verhandlungen könnten Monate dauern. "
                          "Ergebnisse haben große wirtschaftliche Wirkung.",
             "link":"https://example.org/welt/handel","importance":3,"date":"2025-07-01"},
            {"title":"Humanitäre Hilfe: Konvois erreichen Krisenregion",
             "description":"Internationale Hilfsorganisationen konnten dringend benötigte Güter in schwer erreichbare Gebiete bringen. "
                          "Medizinische Versorgung und Lebensmittel sind nun besser verfügbar. "
                          "Logistische Hürden wurden teilweise überwunden. "
                          "Lokale Partner unterstützen die Verteilung. "
                          "Weitere Hilfstransporte sind in Planung.",
             "link":"https://example.org/welt/hilfe","importance":4,"date":"2025-04-20"},
            {"title":"Kultureller Austausch fördert Verständigung",
             "description":"Ein internationales Festival bündelt Künstler aus unterschiedlichen Ländern zur Förderung des Dialogs. "
                          "Workshops und Ausstellungen stärken lokale Kooperationen. "
                          "Programme betonen Bildungs- und Verständigungsformate. "
                          "Besucherzahlen zeigten gegenüber dem Vorjahr Zuwächse. "
                          "Initiativen sollen in Folgeprojekten fortgeführt werden.",
             "link":"https://example.org/welt/kultur","importance":2,"date":"2025-03-08"},
            {"title":"Wasserprojekte gegen Dürre gestartet",
             "description":"Regionale Initiativen zur effizienten Wassernutzung werden umgesetzt, um Landwirtschaft zu stabilisieren. "
                          "Techniken zur Rückgewinnung und Bewässerungsoptimierung werden getestet. "
                          "Landwirte erhalten Schulungen für nachhaltige Methoden. "
                          "Projekte erhalten internationale Unterstützung. "
                          "Ziele sind langfristige Ertragsstabilisierung.",
             "link":"https://example.org/welt/wasser","importance":3,"date":"2025-02-14"},
            {"title":"Digitale Rechte: Internationaler Dialog",
             "description":"Vertreter aus Politik, Zivilgesellschaft und Wirtschaft diskutierten Rechte im digitalen Raum. "
                          "Themen sind Datenschutz, Zugang und digitale Bildung. "
                          "Abschlusserklärungen regen nationale Umsetzungen an. "
                          "Weitere Austauschformate sind geplant. "
                          "Die Konferenz generierte breite Aufmerksamkeit.",
             "link":"https://example.org/welt/digital","importance":3,"date":"2025-05-16"},
            {"title":"Regionale Infrastrukturprogramme angekündigt",
             "description":"Finanzierungsprogramme für lokale Infrastrukturprojekte wurden vorgestellt. "
                          "Fokus liegt auf Straßen, Wasser und Energieprojekten. "
                          "Zugang zu Krediten soll erleichtert werden. "
                          "Partizipation der Gemeinden ist vorgesehen. "
                          "Programme sollen kurzfristig Arbeitsplätze schaffen.",
             "link":"https://example.org/welt/infrastruktur","importance":3,"date":"2025-01-30"},
        ],
        "Allgemein": [
            {"title":"Deutsche Bahn meldet bessere Pünktlichkeit",
             "description":"Die Bahn berichtet von verbesserter Pünktlichkeit durch neue Instandhaltungspläne. "
                          "Kunden zeigen sich vorsichtig optimistisch. "
                          "Weitere Investitionen in Infrastruktur sind geplant. "
                          "Transparenzberichte sollen Kundeninformation verbessern. "
                          "Langfristige Auswirkungen werden beobachtet.",
             "link":"https://example.org/allgemein/bahn","importance":3,"date":"2025-10-01"},
            {"title":"Stadtplanung: Grünflächen werden ausgebaut",
             "description":"Kommunen starten neue Begrünungsprojekte zur Verbesserung des Mikroklimas. "
                          "Bürgerbeteiligung ist Teil der Planungen. "
                          "Fördermittel unterstützen Umsetzung und Pflege. "
                          "Naherholungsflächen werden erweitert. "
                          "Wissenschaftliche Begleitung sichert Qualitätskontrolle.",
             "link":"https://example.org/allgemein/gruen","importance":2,"date":"2025-06-05"},
            {"title":"Verbraucherschutz: Regeln für Onlinekäufe verbessert",
             "description":"Neue Regelungen stärken Informationspflichten und Rückgaberechte bei Onlinekäufen. "
                          "Händler müssen transparente Preisangaben bereitstellen. "
                          "Kontrollen und Sanktionen werden verschärft. "
                          "Ziel ist mehr Verbrauchervertrauen im E-Commerce. "
                          "Umsetzung erfolgt schrittweise.",
             "link":"https://example.org/allgemein/verbraucher","importance":4,"date":"2025-08-01"},
            {"title":"Bibliotheken erweitern digitale Angebote",
             "description":"Bibliotheken bieten vermehrt digitale Lernräume und Medienwerkstätten an. "
                          "Kooperation mit Schulen fördert Nutzungsangebote. "
                          "Flexiblere Öffnungszeiten steigern Erreichbarkeit. "
                          "Programme unterstützen Medienkompetenz. "
                          "Initiativen zielen auf inklusive Bildung.",
             "link":"https://example.org/allgemein/bibliothek","importance":2,"date":"2025-02-01"},
            {"title":"Katastrophenschutz übt Evakuierungspläne",
             "description":"Regionale Behörden führten umfassende Evakuierungsübungen durch. "
                          "Szenarien reichten von Flutereignissen bis Industrieunfällen. "
                          "Kommunikation und Routenplanung wurden erprobt. "
                          "Erkenntnisse fließen in künftige Konzepte ein. "
                          "Freiwillige und Rettungskräfte beteiligten sich.",
             "link":"https://example.org/allgemein/katastrophen","importance":3,"date":"2025-01-08"},
            {"title":"Ehrenamtsbörsen vermitteln lokale Helfer",
             "description":"Digitale Freiwilligenbörsen vernetzen Ehrenamtliche und Projekte vor Ort. "
                          "Plattformen unterstützen Schulungen und Versicherungsschutz. "
                          "Senioren- und Bildungsprojekte profitieren besonders. "
                          "Engagement stärkt Nachbarschaften. "
                          "Modelle werden regional skaliert.",
             "link":"https://example.org/allgemein/ehrenamt","importance":2,"date":"2025-03-22"},
            {"title":"Regionale Impfkampagnen starten",
             "description":"Gesundheitsämter starten mobile Impfkampagnen, um Erreichbarkeit zu erhöhen. "
                          "Kooperation mit Apotheken und Hausärzten erleichtert Umsetzung. "
                          "Informationskampagnen begleiten die Maßnahmen. "
                          "Ziel ist eine höhere Impfquote in vulnerablen Gruppen. "
                          "Logistische Unterstützung ist organisiert.",
             "link":"https://example.org/allgemein/impfungen","importance":3,"date":"2025-04-10"},
            {"title":"Fahrradstraßen-Pilotprojekte getestet",
             "description":"Städte testen Fahrradstraßen mit Verkehrsberuhigung und verbesserter Infrastruktur. "
                          "Nutzerbefragungen fließen in die Weiterentwicklung ein. "
                          "Maßnahmen sollen nachhaltige Mobilität stärken. "
                          "Wissenschaftliche Begleitung bewertet Effekte. "
                          "Positive Rückmeldungen fördern Ausweitung.",
             "link":"https://example.org/allgemein/fahrrad","importance":2,"date":"2025-05-20"},
            {"title":"Lokale Kulturförderung stärkt Initiativen",
             "description":"Förderprogramme unterstützen kleine Kulturprojekte und Jugendinitiativen. "
                          "Finanzielle Mittel und Coaching werden bereitgestellt. "
                          "Projekte tragen zur kulturellen Vielfalt vor Ort bei. "
                          "Erfolgreiche Vorhaben werden als Modell adaptiert. "
                          "Bewerbungen sind offen für verschiedene Träger.",
             "link":"https://example.org/allgemein/kultur","importance":2,"date":"2025-09-09"},
            {"title":"Car-Sharing-Tests für städtische Mobilität",
             "description":"Pilotprojekte zu Car-Sharing werden in ausgewählten Stadtteilen getestet. "
                          "Ziel ist Reduktion des Individualverkehrs und Emissionen. "
                          "Datenauswertung begleitet die Tests. "
                          "Kooperationen mit Anbietern werden geprüft. "
                          "Erfahrungen dienen der Verkehrsplanung.",
             "link":"https://example.org/allgemein/mobilitaet","importance":3,"date":"2025-11-03"},
        ],
    }
    return data
# ------------------------------
# Tokenizer, Stopwords, Sentiment Lexika (Deutsch)
# ------------------------------
GERMAN_STOPWORDS = {
    "und","oder","aber","auch","als","an","auf","bei","der","die","das","ein","eine","in","im","ist","sind",
    "mit","zu","von","den","des","für","dass","dem","nicht","vor","nach","wie","er","sie","es","wir","ihr","ich",
    "hat","haben","werden","wird","seit","mehr","dies","diese","sehr","nur","noch","so","als","bei","um","gegen"
}

POSITIVE_LEXICON = {
    "gut","stark","erfolgreich","verbessert","gewinnt","begrüßt","optimistisch","stabil","steigerung","gewinn",
    "sicher","förder","förderung","unterstützt","erholen","aufwind","positive","verbesserung","win"
}
NEGATIVE_LEXICON = {
    "kritisch","warn","warnen","risiko","risiken","verlust","problem","schwier","krise","fragil","stagn","einbruch",
    "verzöger","engpass","kritik","mangel","unsicher","verlust","sorge","problematisch"
}

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+", flags=re.UNICODE)

def tokenize(text):
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

# IDF-like map (lazily computed)
def compute_tf_idf_map(all_texts):
    docs = [tokenize(t) for t in all_texts]
    df = Counter()
    for tokens in docs:
        for term in set(tokens):
            df[term] += 1
    N = len(docs) if docs else 1
    idf = {term: math.log((N+1)/(df_count+1)) + 1 for term, df_count in df.items()}
    return idf

def score_headline(article, idf_map=None, important_terms=None):
    # Score-Bestandteile:
    # - Basis: importance (1-5) -> 10-50 Punkte
    # - Sentiment: -8..+8 (stärkere positive Sprache erhöht Score)
    # - Länge: ideal 6-12 Tokens -> Bonus
    # - IDF/Keyword Boost: seltene/wichtige Tokens erhöhen Score
    score = 0.0
    importance = float(article.get("importance", 3))
    score += importance * 10.0  # 10-50
    txt = (article.get("title","") + " " + article.get("description",""))
    s = sentiment_score_text(txt)
    score += s * 8.0  # -8..+8

    t_tokens = tokenize(article.get("title",""))
    l = len(t_tokens)
    # ideal length gets up to +8
    opt_bonus = max(0, 8 - abs(l - 9))
    score += opt_bonus

    # IDF boost
    if idf_map:
        boost = 0.0
        for w in set(t_tokens):
            boost += idf_map.get(w, 0.0) * 2.0
        score += boost

    # important terms (manual boost)
    if important_terms:
        lowtxt = txt.lower()
        for it in important_terms:
            if it in lowtxt:
                score += 4.0

    # normalize and cap to 0..100
    score = max(-100.0, min(100.0, score))
    normalized = (score + 100.0) / 2.0
    return round(normalized, 1)

# ------------------------------
# NewsAnalyzer (lazily evaluates heavy parts)
# ------------------------------
class NewsAnalyzer:
    def __init__(self, dataset):
        self.dataset = dataset  # dict: cat -> list articles
        self._initialized = False
        # cached structures
        self.idf_map = {}
        self.global_top_tokens = []
        self.category_stats = {}  # per category computed stats

    def initialize(self):
        if self._initialized:
            return
        # build corpus texts
        all_texts = []
        for cat, arts in self.dataset.items():
            for a in arts:
                all_texts.append(a.get("title","") + " " + a.get("description",""))
        self.idf_map = compute_tf_idf_map(all_texts)
        # global token frequency
        global_counter = Counter()
        for txt in all_texts:
            global_counter.update(tokenize(txt))
        self.global_top_tokens = [t for t,_ in global_counter.most_common(50)]
        # per-category stats
        for cat, arts in self.dataset.items():
            texts = [a.get("title","") + " " + a.get("description","") for a in arts]
            tokens = []
            for t in texts:
                tokens.extend(tokenize(t))
            freq = Counter(tokens)
            sentiments = [sentiment_score_text(t) for t in texts if t.strip()]
            avg_sent = round(sum(sentiments)/len(sentiments),3) if sentiments else 0.0
            avg_imp = round(sum(a.get("importance",3) for a in arts)/len(arts),3) if arts else 0.0
            month_counts = Counter()
            for a in arts:
                try:
                    dt = datetime.strptime(a.get("date","1970-01-01"), "%Y-%m-%d")
                    month_counts[dt.strftime("%Y-%m")] += 1
                except Exception:
                    pass
            self.category_stats[cat] = {
                "token_freq": freq,
                "top_terms": [t for t,_ in freq.most_common(20)],
                "avg_sentiment": avg_sent,
                "avg_importance": avg_imp,
                "month_counts": dict(month_counts)
            }
        self._initialized = True

    def get_global_top_keywords(self, top_n=20):
        self.initialize()
        return self.global_top_tokens[:top_n]

    def get_category_summary(self, category):
        self.initialize()
        return self.category_stats.get(category, {})

    def sentiment_distribution(self, category=None):
        self.initialize()
        def cls(s):
            if s > 0.2: return "positive"
            if s < -0.2: return "negative"
            return "neutral"
        buckets = Counter()
        if category:
            arts = self.dataset.get(category, [])
        else:
            arts = [a for lst in self.dataset.values() for a in lst]
        for a in arts:
            txt = a.get("title","") + " " + a.get("description","")
            s = sentiment_score_text(txt)
            buckets[cls(s)] += 1
        return dict(buckets)

    def top_headlines(self, category, top_n=10):
        self.initialize()
        arts = list(self.dataset.get(category, []))
        important_terms = self.get_global_top_keywords(8)
        scored = []
        for a in arts:
            sc = score_headline(a, idf_map=self.idf_map, important_terms=important_terms)
            scored.append((sc, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(s, art) for s, art in scored[:top_n]]

    def trend_time_series(self, category):
        self.initialize()
        stats = self.category_stats.get(category, {})
        months = stats.get("month_counts", {})
        return sorted(months.items(), key=lambda x: x[0])

    def top_terms_per_category(self, top_n=10):
        self.initialize()
        return {cat: stats["top_terms"][:top_n] for cat, stats in self.category_stats.items()}

# ------------------------------
# User management (simple)
# ------------------------------
class UserManager:
    def __init__(self):
        self.file = USERS_FILE
        self.users = safe_load_json(self.file, {})
        # users stored as: username -> {"password": "...", "created": "ISO"}
    def register(self, username, password):
        if username in self.users:
            return False, "Benutzer existiert bereits."
        self.users[username] = {"password": password, "created": datetime.utcnow().isoformat()}
        safe_save_json(self.file, self.users)
        return True, "Registrierung erfolgreich."
    def login(self, username, password):
        u = self.users.get(username)
        if not u:
            return False, "Benutzer nicht gefunden."
        if u.get("password") != password:
            return False, "Falsches Passwort."
        return True, "Login erfolgreich."

# ------------------------------
# CLI (sauber, schnell, responsiv)
# ------------------------------
class CLI:
    def __init__(self):
        print("Starte Lumina News (Offline) ...")
        # Build dataset quickly
        self.news = build_news_dataset()
        # Analyzer created but heavy init is lazy
        self.analyzer = NewsAnalyzer(self.news)
        self.user_mgr = UserManager()
        self.settings = safe_load_json(SETTINGS_FILE, {"sort_mode":"neueste"})
        self.current_user = None

    def run(self):
        # Welcome (immediately sichtbar)
        print("\n🌐 Willkommen bei Lumina News (Offline)")
        # Authentication loop
        while True:
            print("\nBitte wählen:")
            print("1) Login")
            print("2) Registrierung")
            print("3) Als Gast fortfahren")
            print("0) Beenden")
            choice = input("Auswahl: ").strip()
            if choice == "1":
                self._login()
                if self.current_user:
                    break
            elif choice == "2":
                self._register()
            elif choice == "3":
                self.current_user = "Gast"
                break
            elif choice == "0":
                print("Auf Wiedersehen.")
                sys.exit(0)
            else:
                print("Ungültige Auswahl. Bitte 0-3 eingeben.")

        # Main interactive menu
        self._main_menu()

    def _login(self):
        u = input("Benutzername: ").strip()
        p = input("Passwort: ").strip()
        ok, msg = self.user_mgr.login(u, p)
        print(msg)
        if ok:
            self.current_user = u

    def _register(self):
        u = input("Gewünschter Benutzername: ").strip()
        if not u:
            print("Benutzername darf nicht leer sein.")
            return
        p = input("Passwort: ").strip()
        ok, msg = self.user_mgr.register(u, p)
        print(msg)

    def _main_menu(self):
        while True:
            print(f"\n--- Hauptmenü (Angemeldet als: {self.current_user}) ---")
            print("1-7) Kategorie anzeigen (1=Powi, 2=Wirtschaft, 3=Politik, 4=Sport, 5=Technologie, 6=Weltweit, 7=Allgemein)")
            print("8) Analyzer / Trends")
            print("9) Suche (Titel/Beschreibung)")
            print("10) Export Kategorie -> JSON")
            print("11) Einstellungen (Sortierung)")
            print("0) Abmelden & Beenden")
            choice = input("Auswahl: ").strip()
            if choice in [str(i) for i in range(1,8)]:
                cats = list(self.news.keys())
                cat = cats[int(choice)-1]
                self._show_category(cat)
            elif choice == "8":
                self._analyzer_menu()
            elif choice == "9":
                self._search()
            elif choice == "10":
                self._export_category()
            elif choice == "11":
                self._settings()
            elif choice == "0":
                print("Abmelden. Auf Wiedersehen.")
                sys.exit(0)
            else:
                print("Ungültige Eingabe.")

    def _show_category(self, category):
        arts = list(self.news.get(category, []))
        # Sort
        sort_mode = self.settings.get("sort_mode", "neueste")
        if sort_mode in ("wichtig","importance"):
            arts.sort(key=lambda x: x.get("importance",0), reverse=True)
        else:
            def pd(a):
                try:
                    return datetime.strptime(a.get("date","1970-01-01"), "%Y-%m-%d")
                except Exception:
                    return datetime(1970,1,1)
            arts.sort(key=lambda x: pd(x), reverse=True)
        # Paging
        page_size = 5
        page = 0
        total_pages = max(1, math.ceil(len(arts)/page_size))
        while True:
            start = page*page_size
            end = start + page_size
            print(f"\n--- {category} (Seite {page+1}/{total_pages}) ---")
            slice_ = arts[start:end]
            for idx, a in enumerate(slice_, start=1):
                print(f"{idx}) {a['title']}  [{a['date']}]  W:{a['importance']}")
            print("\nBefehle: n=next, p=prev, v#=view (z.B. v2), t=headlines, b=back")
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
                    num = int(cmd[1:]) - 1
                    idx = start + num
                    if idx < 0 or idx >= len(arts):
                        print("Ungültige Nummer.")
                        continue
                    self._view_article(arts[idx])
                except Exception:
                    print("Ungültiges Format. Beispiel: 'v2' um Artikel 2 zu öffnen.")
            elif cmd == "t":
                tops = self.analyzer.top_headlines(category, top_n=10)
                print(f"\nTop Headlines ({category}):")
                for r, (score, art) in enumerate([(s,a) for s,a in tops], start=1):
                    print(f"{r}. [{score}] {art['title']} ({art['date']}) W:{art['importance']}")
                input("Enter zum Weitermachen.")
            elif cmd == "b":
                return
            else:
                print("Unbekannter Befehl.")

    def _view_article(self, article):
        print("\n--- Artikel Ansicht ---")
        print(f"Titel: {article.get('title')}")
        print(f"Datum: {article.get('date')}  |  Wichtigkeit: {article.get('importance')}")
        print(f"Link: {article.get('link')}")
        print("\nBeschreibung:\n" + article.get("description"))
        # On-the-fly Analysen
        s = sentiment_score_text(article.get("title","") + " " + article.get("description",""))
        print(f"\n[Analyse] Sentiment-Score (Proxy): {s}")
        # Headline score (lazy uses analyzer idf map)
        # Ensure analyzer initialized
        self.analyzer.initialize()
        hs = score_headline(article, idf_map=self.analyzer.idf_map, important_terms=self.analyzer.get_global_top_keywords(8))
        print(f"[Analyse] Headline-Score: {hs}/100")
        input("Enter zum Zurückkehren.")

    def _analyzer_menu(self):
        while True:
            print("\n--- Analyzer / Trends ---")
            print("1) Globale Top-Keywords")
            print("2) Top-Terme pro Kategorie")
            print("3) Kategorie-Summaries")
            print("4) Sentiment-Verteilung (global oder spezifisch)")
            print("5) Trend-Zeitreihe (Kategorie)")
            print("0) Zurück")
            c = input("Auswahl: ").strip()
            if c == "1":
                print("Globale Top-Keywords:")
                print(", ".join(self.analyzer.get_global_top_keywords(30)))
            elif c == "2":
                dd = self.analyzer.top_terms_per_category(10)
                for cat, terms in dd.items():
                    print(f"\n{cat}: {', '.join(terms)}")
            elif c == "3":
                for cat in self.news.keys():
                    s = self.analyzer.get_category_summary(cat)
                    print(f"\n{cat}: AvgSent={s.get('avg_sentiment')} | AvgImp={s.get('avg_importance')} | TopTerms={', '.join(s.get('top_terms',[])[:8])}")
            elif c == "4":
                cat = input("Kategorie (leer für global): ").strip()
                res = self.analyzer.sentiment_distribution(cat if cat else None)
                print("Sentiment-Verteilung:", res)
            elif c == "5":
                cat = input("Kategorie (Name): ").strip()
                if not cat:
                    print("Ungültig.")
                    continue
                ts = self.analyzer.trend_time_series(cat)
                if not ts:
                    print("Keine Zeitdaten.")
                else:
                    for m, cnt in ts:
                        print(f"{m}: {cnt} Artikel")
            elif c == "0":
                return
            else:
                print("Ungültig.")

    def _search(self):
        q = input("Suchbegriff (Titel oder Beschreibung): ").strip().lower()
        if not q:
            print("Leere Suche.")
            return
        hits = []
        for cat, arts in self.news.items():
            for a in arts:
                if q in a.get("title","").lower() or q in a.get("description","").lower():
                    hits.append((cat, a))
        if not hits:
            print("Keine Treffer.")
            return
        print(f"{len(hits)} Treffer:")
        for i, (cat, a) in enumerate(hits, start=1):
            print(f"{i}) [{cat}] {a['title']} ({a['date']}) W:{a['importance']}")
        sel = input("Artikelnummer öffnen (Enter = Abbrechen): ").strip()
        if sel:
            try:
                idx = int(sel)-1
                if 0 <= idx < len(hits):
                    self._view_article(hits[idx][1])
            except Exception:
                print("Ungültige Eingabe.")

    def _export_category(self):
        cats = list(self.news.keys())
        for i, c in enumerate(cats, start=1):
            print(f"{i}) {c}")
        sel = input("Kategorie wählen (Nummer) oder 0 abbrechen: ").strip()
        if sel == "0" or not sel:
            return
        try:
            idx = int(sel)-1
            if not (0 <= idx < len(cats)):
                print("Ungültig.")
                return
            cat = cats[idx]
            fname = f"export_{cat.replace(' ','_')}.json"
            safe_save_json(fname, self.news[cat])
            print(f"Export erfolgreich: {fname}")
        except Exception as e:
            print("Fehler beim Export:", e)

    def _settings(self):
        print("\n--- Einstellungen ---")
        cur = self.settings.get("sort_mode","neueste")
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

# ------------------------------
# Start
# ------------------------------
def main():
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()
             
