# -*- coding: utf-8 -*-
"""
Lumina News - Offline CLI mit starkem lokalem Analyzer
Speichern als: main.py
Start: python main.py
"""

import json
import os
import sys
import math
from datetime import datetime
from collections import Counter, defaultdict
import re

# ----------------------------
# Helfer: Dateien / IO
# ----------------------------
USERS_FILE = "users.json"
SETTINGS_FILE = "settings.json"

def safe_load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return default
    except Exception as e:
        print(f"[WARN] Fehler beim Laden {path}: {e}. Standarddaten werden benutzt.")
        return default

def safe_save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Konnte {path} nicht speichern: {e}")

# ----------------------------
# Offline News-Daten (7 Kategorien x 10 Artikel)
# Jeder Artikel: title, description (5 Sätze), link, importance (1-5), date (YYYY-MM-DD)
# ----------------------------
def build_news_dataset():
    # Für Übersichtlichkeit generiere ich realistische, kurze Artikel pro Kategorie.
    # Du kannst diese Texte bei Bedarf ersetzen.
    dataset = {
        "Powi": [
            {"title":"Neue Lehrpläne stärken kritisches Denken",
             "description":"Das Kultusministerium hat neue Lehrpläne vorgestellt, die kritisches Denken und Medienkompetenz stärker betonen. "
                          "Schwerpunkte liegen auf Quellenkritik und Projektlernen. "
                          "Lehrkräfte erhalten dafür spezielle Fortbildungen. "
                          "Pilotprojekte starten im nächsten Schuljahr an 200 Schulen. "
                          "Eltern- und Schülervertretungen wurden in die Entwicklung eingebunden.",
             "link":"https://example.org/powi/lehrplaene","importance":5,"date":"2025-09-15"},
            {"title":"Digitaler Unterricht: Schulen erhalten Ausstattung",
             "description":"Ein neues Förderprogramm stellt Tablets und Infrastruktur für Schulen bereit. "
                          "Lehrkräfte sollen sukzessive in digitale Methoden geschult werden. "
                          "Datenschutz und pädagogische Konzepte stehen im Fokus. "
                          "Ziel ist eine breite und nachhaltige Digitalisierung. "
                          "Die ersten Lieferungen treffen noch vor Schuljahresbeginn ein.",
             "link":"https://example.org/powi/digital","importance":4,"date":"2025-10-01"},
            {"title":"Schülervertretungen bekommen mehr Mitspracherechte",
             "description":"Auf Landesebene wurden Regelungen zur stärkeren Einbindung von Schülervertretungen beschlossen. "
                          "SV-Mitglieder sollen künftig an Schulkonferenzen teilnehmen. "
                          "Kritiker wünschen sich jedoch konkrete Umsetzungspläne. "
                          "Die Maßnahme zielt auf mehr demokratische Beteiligung ab. "
                          "Pilotphasen werden in ausgewählten Schulen evaluiert.",
             "link":"https://example.org/powi/sv","importance":3,"date":"2025-08-20"},
            {"title":"Berufsorientierung wird an Gymnasien ausgebaut",
             "description":"Gymnasien führen verpflichtende Module zur Berufsorientierung ein. "
                          "Unternehmen bieten Praktikumsplätze und Workshops an. "
                          "Schüler erhalten Unterstützung bei Bewerbung und Studienwahl. "
                          "Die Maßnahme soll Studienabbrüche reduzieren. "
                          "Erste Standorte berichten von positiven Rückmeldungen.",
             "link":"https://example.org/powi/berufsorientierung","importance":3,"date":"2025-06-10"},
            {"title":"MINT-Förderung: Talente gezielt fördern",
             "description":"Ein Förderprogramm sucht frühzeitig MINT-Talente und bietet Mentoring. "
                          "Schulen erhalten Materialien und Wettbewerbe zur Stärkung des Interesses. "
                          "Besonderer Fokus liegt auf Mädchenförderung in MINT-Fächern. "
                          "Regionale Partnerschaften unterstützen die Umsetzung. "
                          "Langfristig soll so der Fachkräftemangel adressiert werden.",
             "link":"https://example.org/powi/mint","importance":4,"date":"2025-05-05"},
            {"title":"Schulsozialarbeit wird ausgebaut",
             "description":"Aufgrund steigender Nachfrage sollen mehr Schulsozialarbeiter eingestellt werden. "
                          "Frühinterventionen und Präventionsprogramme werden ausgebaut. "
                          "Elternarbeit und Kooperation mit Jugendämtern sind Teil der Maßnahmen. "
                          "Langfristig erwartet man stabilere Lernbedingungen. "
                          "Pilotregionen berichten bereits von positiven Effekten.",
             "link":"https://example.org/powi/sozialarbeit","importance":4,"date":"2025-04-12"},
            {"title":"Sprachförderung in Grundschulen intensiviert",
             "description":"Grundschulen erhalten zusätzliche Fördermittel für Sprachprogramme. "
                          "Besonders Kinder mit Migrationshintergrund werden unterstützt. "
                          "Materialien und Trainings für Lehrkräfte sind vorgesehen. "
                          "Ziel ist es, Lernrückstände früh zu verringern. "
                          "Regionale Netzwerke koordinieren die Maßnahmen.",
             "link":"https://example.org/powi/sprachfoerderung","importance":3,"date":"2025-02-18"},
            {"title":"Schulbauoffensive für moderne Klassenzimmer",
             "description":"Bund und Länder investieren in die Sanierung alter Schulgebäude. "
                          "Ein Schwerpunkt ist energieeffiziente Heizung und moderne IT-Ausstattung. "
                          "Kommunen erhalten Planungsmittel für schnelle Umsetzung. "
                          "Prioritär sind Schulen mit dringendem Handlungsbedarf. "
                          "Förderbescheide werden in den nächsten Monaten erwartet.",
             "link":"https://example.org/powi/schulbau","importance":5,"date":"2025-03-28"},
            {"title":"Wettbewerb fördert Nachhaltigkeitsprojekte an Schulen",
             "description":"Schüler entwickeln praktische Projekte zu Energieeinsparung und Recycling. "
                          "Gewinnerprojekte erhalten Finanzierung und Mentoring. "
                          "Die Aktion stärkt praktisches Lernen und Verantwortungsbewusstsein. "
                          "Viele Schulen vernetzen sich über regionale Plattformen. "
                          "Die Teilnahme ist offen für alle Schulformen.",
             "link":"https://example.org/powi/nachhaltigkeit","importance":2,"date":"2025-01-31"},
            {"title":"Pilotprojekt: Hybridunterricht nach der Pandemie",
             "description":"Mehrere Schulen testen hybride Lernformen mit wechselnden Präsenz- und Onlinephasen. "
                          "Ziel ist flexible Gestaltung von Lehr- und Lernzeiten. "
                          "Lehrer erhalten Unterstützung durch digitale Coaches. "
                          "Evaluationen sollen Best-Practices identifizieren. "
                          "Erste Rückmeldungen zeigen gesteigerte Motivation bei Schülern.",
             "link":"https://example.org/powi/hybrid","importance":3,"date":"2025-11-03"},
        ],
        "Wirtschaft": [
            {"title":"Industrieproduktion zeigt Aufwärtstrend",
             "description":"Die Industrieproduktion verzeichnet ein moderates Wachstum im dritten Quartal. "
                          "Maschinenbau und erneuerbare Energien treiben die Entwicklung. "
                          "Unternehmen investieren verstärkt in Automatisierung. "
                          "Analysten warnen jedoch vor Lieferkettenrisiken. "
                          "Die Stimmung in der Industrie bleibt aber positiv.",
             "link":"https://example.org/wirtschaft/industrie","importance":4,"date":"2025-10-20"},
            {"title":"Mittelstand investiert in KI-Lösungen",
             "description":"Immer mehr mittelständische Firmen setzen KI zur Effizienzsteigerung ein. "
                          "Anwendungsfelder reichen von Produktion bis Kundendienst. "
                          "Förderprogramme unterstützen Pilotprojekte. "
                          "Datenschutz und Qualifizierung bleiben Herausforderungen. "
                          "Langfristig werden Produktivitätsgewinne erwartet.",
             "link":"https://example.org/wirtschaft/ki","importance":4,"date":"2025-09-05"},
            {"title":"Arbeitsmarkt stabil trotz Konjunktursorgen",
             "description":"Die Arbeitslosenquote bleibt niedrig und offene Stellen sind zahlreich. "
                          "Besonders IT, Pflege und Handwerk melden hohen Bedarf. "
                          "Gewerkschaften verhandeln branchenweite Lohnanpassungen. "
                          "Unternehmen fördern Weiterbildungskampagnen. "
                          "Die Lage wird insgesamt als robust bewertet.",
             "link":"https://example.org/wirtschaft/arbeitsmarkt","importance":3,"date":"2025-08-14"},
            {"title":"Inflation beruhigt sich",
             "description":"Die Inflationsrate hat sich im Vergleich zum Vorjahr abgeschwächt. "
                          "Energiepreise zeigen regionale Unterschiede. "
                          "Zentralbanksignale bleiben vorsichtig, aber optimistisch. "
                          "Konsumenten spüren leichte Erleichterung bei Basiskosten. "
                          "Langfristige Stabilisierung hängt von Rohstoffpreisen ab.",
             "link":"https://example.org/wirtschaft/inflation","importance":4,"date":"2025-07-30"},
            {"title":"Startups sichern sich Wagniskapital",
             "description":"Finanzierungsrunden für grüne Tech-Startups haben zugenommen. "
                          "Investorengelder fließen in Energiespeicher und Mobilitätslösungen. "
                          "Accelerator-Programme unterstützen Wachstum. "
                          "Skalierungsfragen bleiben Kernherausforderung. "
                          "Talentakquise entscheidet zunehmend über Erfolg.",
             "link":"https://example.org/wirtschaft/startups","importance":3,"date":"2025-06-22"},
            {"title":"Exportsektor profitiert von asiatischer Nachfrage",
             "description":"Deutsche Exporte in Asien steigen, insbesondere Maschinenbau. "
                          "Unternehmen bauen regionale Vertriebsnetzwerke aus. "
                          "Logistikoptimierungen reduzieren Lieferzeiten. "
                          "Wechselkurse beeinflussen dennoch Margen. "
                          "Chance und Wettbewerb prägen die Entwicklung.",
             "link":"https://example.org/wirtschaft/export","importance":3,"date":"2025-05-12"},
            {"title":"Immobilienmarkt: Regionen zeigen Unterschiede",
             "description":"Während Metropolen hohe Preise halten, normalisieren sich Randregionen. "
                          "Förderprogramme für bezahlbares Wohnen werden ausgeweitet. "
                          "Bauunternehmen berichten Material- und Personalengpässe. "
                          "Mietpolitik bleibt politischer Diskussionspunkt. "
                          "Trend bleibt heterogen.",
             "link":"https://example.org/wirtschaft/immobilien","importance":3,"date":"2025-04-01"},
            {"title":"Lieferketten: More Resilienz durch Nearshoring",
             "description":"Unternehmen diversifizieren Zulieferer und setzen auf Nearshoring. "
                          "Ziel ist höhere Resilienz gegenüber globalen Störungen. "
                          "Digitale Tools verbessern Transparenz entlang der Kette. "
                          "Kostendruck bleibt Entscheidungsfaktor. "
                          "Strategien variieren je nach Branche.",
             "link":"https://example.org/wirtschaft/lieferkette","importance":3,"date":"2025-03-18"},
            {"title":"Energieeffizienz wächst als Unternehmensstrategie",
             "description":"Steigende Energiepreise treiben Investitionen in Effizienzmaßnahmen. "
                          "Abwärmenutzung und Energiemanagementsysteme sind verbreitet. "
                          "Förderprogramme erleichtern Investitionsentscheidungen. "
                          "Wirtschaftlichkeit steht im Vordergrund. "
                          "Langfristig sinken Betriebskosten.",
             "link":"https://example.org/wirtschaft/energie","importance":2,"date":"2025-02-10"},
            {"title":"Finanzbildung in Schulen verbessert",
             "description":"Programme zur Finanzbildung werden unter Beteiligung von Schulen ausgebaut. "
                          "Workshops und Planspiele vermitteln Finanzkompetenz. "
                          "Kritiker mahnen Unabhängigkeit bei Inhalten an. "
                          "Trotzdem steigt die Nachfrage nach Angeboten. "
                          "Initiativen werden weiter ausgerollt.",
             "link":"https://example.org/wirtschaft/finanzbildung","importance":2,"date":"2025-01-05"},
        ],
        "Politik": [
            {"title":"Koalitionsgespräche erreichen finale Phase",
             "description":"Verhandlungen über Regierungsbildung gehen in die finale Runde. "
                          "Kernfragen sind Klima, Finanzen und Infrastruktur. "
                          "Parteien zeigen Kompromissbereitschaft in Teilfragen. "
                          "Öffentlichkeit und Medien verfolgen Diskussionen genau. "
                          "Eine Einigung wird in den kommenden Tagen erwartet.",
             "link":"https://example.org/politik/koalition","importance":5,"date":"2025-11-01"},
            {"title":"Transparenzgesetz: Lobbykontakte im Fokus",
             "description":"Diskussionen um Registries für Lobbykontakte haben zugenommen. "
                          "Ziele sind mehr Nachvollziehbarkeit politischer Einflussnahme. "
                          "Verbände sprechen von erhöhtem Verwaltungsaufwand. "
                          "Befürworter sehen größeren Vertrauensgewinn. "
                          "Das Gesetz durchläuft mehrere Beratungsstufen.",
             "link":"https://example.org/politik/transparenz","importance":4,"date":"2025-07-02"},
            {"title":"Digital-Politik: Anpassungen für KI",
             "description":"Parlamentarier beraten über Datenschutzanpassungen im Kontext KI. "
                          "Balance zwischen Innovation und Grundrechtsschutz ist zentral. "
                          "Branchenvertreter und Wissenschaft werden eingeladen. "
                          "Ergebnisoffenheit prägt die Anhörungen. "
                          "Regulatorische Leitplanken sind gefordert.",
             "link":"https://example.org/politik/datenschutz","importance":5,"date":"2025-05-19"},
            {"title":"Kommunen erhalten Unterstützung für Investitionen",
             "description":"Bundesprogramme stärken kommunale Haushalte und Digitalisierungsprojekte. "
                          "Ziel ist nachhaltige Investitionsfähigkeit vor Ort. "
                          "Regionale Unterschiede bestimmen Verteilmechanismen. "
                          "Förderbedingungen wurden vereinfacht. "
                          "Kommunen begrüßen die Unterstützung.",
             "link":"https://example.org/politik/kommunen","importance":3,"date":"2025-10-18"},
            {"title":"Integration: Programme für Arbeitsmarktzugang",
             "description":"Neue Maßnahmen fördern Sprach- und Qualifizierungsangebote. "
                          "Ziel ist nachhaltige Teilhabe im Arbeitsmarkt. "
                          "Besondere Programme unterstützen Ausbildungseintritte. "
                          "Kooperationen mit Unternehmen erleichtern Praktika. "
                          "Erste Evaluationen zeigen positive Trends.",
             "link":"https://example.org/politik/integration","importance":3,"date":"2025-06-25"},
            {"title":"Innenpolitik: Cyberabwehr gestärkt",
             "description":"Bund und Länder erhöhen Ressourcen für Cyberabwehr und IT-Sicherheit. "
                          "Kritische Infrastrukturen stehen im Fokus. "
                          "Zusammenarbeit mit Forschungseinrichtungen wird ausgebaut. "
                          "Ziel ist ein robusterer Schutz vor Angriffen. "
                          "Ausbildungskapazitäten für Spezialisten werden erhöht.",
             "link":"https://example.org/politik/cyber","importance":4,"date":"2025-04-10"},
            {"title":"Wahlrecht: Diskussion um Senkung des Wahlalters",
             "description":"Debatten über eine mögliche Absenkung des Wahlalters auf kommunaler Ebene werden geführt. "
                          "Befürworter sehen Chancen zur stärkeren Jugendbeteiligung. "
                          "Gegner mahnen Reife- und Informationsfragen an. "
                          "Pilotprojekte könnten nächste Schritte zeigen. "
                          "Thema bleibt kontrovers und medial präsent.",
             "link":"https://example.org/politik/wahlrecht","importance":2,"date":"2025-03-03"},
            {"title":"Rentenkommission legt Zwischenbericht vor",
             "description":"Eine Kommission präsentiert erste Optionen für Reformen im Rentensystem. "
                          "Diskutiert werden flexible Übergänge und Stabilitätsmechanismen. "
                          "Breiter gesellschaftlicher Austausch ist geplant. "
                          "Konkrete Vorschläge sollen im kommenden Jahr folgen. "
                          "Stakeholder zeigen unterschiedliche Perspektiven.",
             "link":"https://example.org/politik/rente","importance":4,"date":"2025-02-14"},
            {"title":"Außenpolitik: Dialog wird intensiviert",
             "description":"Die Regierung intensiviert diplomatischen Austausch mit Nachbarstaaten. "
                          "Fokus liegt auf Energie, Handel und Forschung. "
                          "Regelmäßige Ministertreffen sind vorgesehen. "
                          "Analysten sehen strategischen Mehrwert. "
                          "Kernabkommen sollen in den nächsten Monaten finalisiert werden.",
             "link":"https://example.org/politik/aussen","importance":3,"date":"2025-01-21"},
            {"title":"Sozialpolitik: Maßnahmen gegen Armut",
             "description":"Neue Programme unterstützen Familien und vulnerable Gruppen. "
                          "Ziele sind bessere Integration und Arbeitsmarktchancen. "
                          "Regionale Projekte werden speziell gefördert. "
                          "Verbände werden in die Planung eingebunden. "
                          "Erste Pilotmaßnahmen starten im Frühjahr.",
             "link":"https://example.org/politik/sozial","importance":3,"date":"2025-11-02"},
        ],
        "Sport": [
            {"title":"Nationalteam triumphiert im Qualifikationsspiel",
             "description":"Das Team gewann ein enges Spiel dank taktischer Disziplin. "
                          "Der Trainer lobt kämpferische Leistung und Teamgeist. "
                          "Fans feierten den Erfolg in vielen Städten. "
                          "Der Sieg stärkt die Chancen in der nächsten Runde. "
                          "Spieler zeigten individuelle Lichtblicke.",
             "link":"https://example.org/sport/qualifikation","importance":5,"date":"2025-10-31"},
            {"title":"Bundesligist investiert in Nachwuchsakademie",
             "description":"Ein Club investiert stark in Jugendakademien und Scouting. "
                          "Ziel ist, langfristig Talente zu fördern und zu integrieren. "
                          "Kooperationen mit Schulen stärken die Ausbildung. "
                          "Trainer setzen moderne Trainingsmethoden ein. "
                          "Erste Erfolge sind in Jugendligen sichtbar.",
             "link":"https://example.org/sport/nachwuchs","importance":3,"date":"2025-09-12"},
            {"title":"Olympia-Vorbereitung läuft planmäßig",
             "description":"Athleten präsentieren starke Leistungen in Vorbereitungswettkämpfen. "
                          "Verbände und Trainer arbeiten an finalen Formkurven. "
                          "Medaillenkandidaten zeigen Zuversicht. "
                          "Trainingslager optimieren die Wettkampfvorbereitung. "
                          "Fans und Medien verfolgen die Entwicklung intensiv.",
             "link":"https://example.org/sport/olympia","importance":4,"date":"2025-08-01"},
            {"title":"Tennis: Überraschungssieger sorgt für Furore",
             "description":"Ein Newcomer gewann ein großes Turnier überraschend. "
                          "Der Sieg sorgt für Aufmerksamkeit und Sponsoreninteresse. "
                          "Trainer loben mentale Stärke und Technik. "
                          "Der Erfolg verbessert Ranglistenpositionen deutlich. "
                          "Weitere Turniere werden genau beobachtet.",
             "link":"https://example.org/sport/tennis","importance":3,"date":"2025-07-18"},
            {"title":"Basketball: Entscheidungsspiel endet dramatisch",
             "description":"Ein Entscheidungsspiel entschied über Playoff-Platzierungen in der Liga. "
                          "Die Partie ging in die Verlängerung und bot Spannung bis zur letzten Sekunde. "
                          "Fans füllten die Halle und sorgten für Atmosphäre. "
                          "Trainer lobten die taktische Cleverness einiger Teams. "
                          "Die Playoffs versprechen weitere packende Duelle.",
             "link":"https://example.org/sport/basketball","importance":3,"date":"2025-06-11"},
            {"title":"Handball: Nationalteam startet siegreich",
             "description":"Die Mannschaft gewann ihr Auftaktspiel deutlich. "
                          "Defensive Stabilität war Schlüssel zum Erfolg. "
                          "Einsatzzeiten für junge Spieler wurden erweitert. "
                          "Trainer betonte die Kollektivleistung. "
                          "Fans zeigten sich optimistisch für die Saison.",
             "link":"https://example.org/sport/handball","importance":2,"date":"2025-05-09"},
            {"title":"Radsport: Etappensieg und neue Führung",
             "description":"Ein Fahrer gewann die Etappe und übernahm die Gesamtführung. "
                          "Teamstrategien prägten den Rennverlauf. "
                          "Bergankünfte werden zukünftig entscheidend sein. "
                          "Zuschauer loben die packenden Duelle im Feld. "
                          "Die nächsten Etappen bleiben spannend.",
             "link":"https://example.org/sport/radsport","importance":3,"date":"2025-04-22"},
            {"title":"Leichtathletik: Nachwuchsmeeting mit Bestleistungen",
             "description":"Bei einem Meeting erzielten mehrere junge Athleten persönliche Bestwerte. "
                          "Trainer sehen positiven Trend für kommende Großereignisse. "
                          "Sprung- und Sprintdisziplinen standen im Fokus. "
                          "Das Event stärkte den Austausch regionaler Verbände. "
                          "Zukunftshoffnungen wurden sichtbar.",
             "link":"https://example.org/sport/leichtathletik","importance":2,"date":"2025-03-30"},
            {"title":"Eishockey: Überraschungsteam erreicht Playoffs",
             "description":"Ein Aufsteiger sicherte überraschend einen Playoff-Platz. "
                          "Hartes Forechecking und Teamgeist prägten die Saison. "
                          "Clubs und Fans feiern den Erfolg als Saisonhöhepunkt. "
                          "Trainer betonen Fokus und Disziplin. "
                          "Die Playoffs bieten Chancen für Überraschungen.",
             "link":"https://example.org/sport/eishockey","importance":2,"date":"2025-02-12"},
            {"title":"Fußball: Lokales Derby sorgt für volle Stadien",
             "description":"Ein regionales Derby lockte viele Zuschauer und viel Emotion ins Stadion. "
                          "Die Partie war intensiv und von vielen Höhepunkten geprägt. "
                          "Sicherheitskonzepte wurden erfolgreich umgesetzt. "
                          "Organisatoren ziehen mehr Besucherzahlen in Betracht. "
                          "Die Rivalität bleibt sportlich spannend.",
             "link":"https://example.org/sport/derby","importance":3,"date":"2025-01-18"},
        ],
        "Technologie": [
            {"title":"Neuer KI-Chip verbessert Effizienz",
             "description":"Ein Halbleiterhersteller kündigt einen KI-Chip mit höherer Energieeffizienz an. "
                          "Der Chip ist für Rechenzentren und Edge-Anwendungen optimiert. "
                          "Partnerschaften mit Cloud-Anbietern sind geplant. "
                          "Forschungsteams evaluieren Leistungsdaten. "
                          "Markteinführung ist für 2026 vorgesehen.",
             "link":"https://example.org/tech/ki-chip","importance":5,"date":"2025-10-30"},
            {"title":"5G-Privatnetze fördern Industrieanwendungen",
             "description":"Unternehmen bauen private 5G-Netze für Produktionsstätten. "
                          "Echtzeitkommunikation und autonome Steuerung profitieren davon. "
                          "Regulatorische Fragen zur Frequenzzuteilung bleiben relevant. "
                          "Pilotprojekte zeigen deutliche Effizienzgewinne. "
                          "Skalierung ist die nächste Herausforderung.",
             "link":"https://example.org/tech/5g","importance":4,"date":"2025-08-20"},
            {"title":"Quantenforschung macht Fortschritte bei Fehlerkorrektur",
             "description":"Forscher berichten über verbesserte Methoden zur Quantenfehlerkorrektur. "
                          "Die Stabilität von Qubits könnte sich erhöhen. "
                          "Industriepartner prüfen mögliche Anwendungen. "
                          "Langfristig könnten neue Simulationen möglich werden. "
                          "Die Forschung bleibt anspruchsvoll, aber erfolgversprechend.",
             "link":"https://example.org/tech/quanten","importance":5,"date":"2025-07-09"},
            {"title":"Open-Source-Tool vereinfacht Testautomatisierung",
             "description":"Ein Community-Projekt bietet modulare Tools zur Automatisierung von Tests. "
                          "Unternehmen sparen Zeit in CI/CD-Prozessen. "
                          "Contributors aus vielen Ländern beteiligen sich. "
                          "Das Projekt fördert Best-Practices in Entwicklungsteams. "
                          "Adoption steigt langsam.",
             "link":"https://example.org/tech/opensource","importance":3,"date":"2025-06-16"},
            {"title":"Cloudanbieter veröffentlichen Nachhaltigkeits-Tools",
             "description":"Neue Werkzeuge messen Workload-Emissionen und helfen bei Optimierung. "
                          "Standardisierte Berichte erleichtern ESG-Reporting. "
                          "Kunden planen energieeffizientere Workloads. "
                          "Die Tools sind in frühen Phasen verfügbar. "
                          "Branchenstandards werden diskutiert.",
             "link":"https://example.org/tech/cloud","importance":3,"date":"2025-03-12"},
            {"title":"Robotics: Service-Roboter in Lagerlogistik",
             "description":"Autonome Roboter steigern Effizienz in Logistikzentren. "
                          "Integration mit Warehouse-Systemen optimiert Abläufe. "
                          "Arbeitskräfte werden umgeschult für höhere Wertschöpfung. "
                          "Pilotprojekte zeigen deutliche Zeitgewinne. "
                          "Wirtschaftliche Effekte werden weiter evaluiert.",
             "link":"https://example.org/tech/robotics","importance":3,"date":"2025-04-18"},
            {"title":"Bildverarbeitung verbessert medizinische Diagnostik",
             "description":"KI-Modelle erreichen bessere Genauigkeit bei Bildanalysen. "
                          "Ärzte nutzen Systeme zur Unterstützung von Diagnosen. "
                          "Regulatorische Prüfungen laufen parallel. "
                          "Pilotprojekte laufen in mehreren Kliniken. "
                          "Ziel ist ergänzende Nutzung, nicht Ersatz.",
             "link":"https://example.org/tech/med","importance":5,"date":"2025-02-25"},
            {"title":"Edge-Computing-Anwendungen gewinnen an Bedeutung",
             "description":"Mehr Anwendungen verlagern Rechenlast an die Edge. "
                          "Das reduziert Latenz und Bandbreitenbedarf. "
                          "Heterogene Hardware stellt Herausforderungen dar. "
                          "Anwendungsfälle in Smart City und Industrie entstehen. "
                          "Entwicklerteams adaptieren neue Architekturen.",
             "link":"https://example.org/tech/edge","importance":3,"date":"2025-01-16"},
            {"title":"Datensicherheit: Zero-Trust-Ansätze verbreiten sich",
             "description":"Unternehmen setzen zunehmend auf Zero-Trust-Modelle. "
                          "Fokus liegt auf Identitätssicherung und Mikrosegmentierung. "
                          "Migrationen sind anspruchsvoll, aber effektiv. "
                          "Beratungsbedarf steigt stark an. "
                          "Sicherheitsarchitekturen werden modernisiert.",
             "link":"https://example.org/tech/secure","importance":4,"date":"2025-11-02"},
            {"title":"Neue Open-Data-Initiativen fördern Forschung",
             "description":"Institutionen veröffentlichen mehr Datensets für Forschung und Innovation. "
                          "Transparenz und Reproduzierbarkeit werden gestärkt. "
                          "Forscherteams nutzen die Daten für neue Anwendungen. "
                          "Zugangsregelungen und Ethik bleiben wichtige Themen. "
                          "Initiativen wachsen langsam, aber stetig.",
             "link":"https://example.org/tech/opendata","importance":3,"date":"2025-09-10"},
        ],
        "Weltweit": [
            {"title":"Internationale Klimapartnerschaften vereinbart",
             "description":"Mehrere Staaten verpflichten sich zu Technologieaustausch und Emissionsreduktion. "
                          "Finanzierung für Anpassungsmaßnahmen ist enthalten. "
                          "Monitoring-Mechanismen sollen Fortschritt sichern. "
                          "Entwicklungsländer erhalten gezielte Unterstützung. "
                          "Die Initiative wird international begrüßt.",
             "link":"https://example.org/welt/klima","importance":5,"date":"2025-10-05"},
            {"title":"Friedensgespräche starten in Konfliktregion",
             "description":"Diplomatische Vermittler haben Gesprächsrunden zur Deeskalation begonnen. "
                          "Humanitäre Zugänge und Gefangenenaustausch stehen auf der Agenda. "
                          "Der Prozess gilt als fragil, aber notwendig. "
                          "Internationale Organisationen unterstützen die Gespräche. "
                          "Beobachter bleiben vorsichtig optimistisch.",
             "link":"https://example.org/welt/frieden","importance":5,"date":"2025-09-22"},
            {"title":"Weltbank finanziert Infrastrukturprojekte",
             "description":"Neue Kredite unterstützen nachhaltige Infrastruktur in Entwicklungsregionen. "
                          "Projekte umfassen Wasser, Energie und Verkehr. "
                          "Umweltprüfungen begleiten die Vorhaben. "
                          "Regierungen verpflichten sich zu Offenheit bei Vergaben. "
                          "Die Initiative zielt auf Beschäftigung und Wachstum.",
             "link":"https://example.org/welt/weltbank","importance":4,"date":"2025-08-11"},
            {"title":"Pandemieprävention: Impfstofflager ausgebaut",
             "description":"Strategische Lager für Impfstoffe werden global eingerichtet. "
                          "Schnelle Verfügbarkeit bei regionalen Ausbrüchen ist Ziel. "
                          "Logistiknetzwerke und Kühlketten werden optimiert. "
                          "Finanzierung erfolgt durch multilaterale Fonds. "
                          "Regionale Kooperationen stärken Verteilung.",
             "link":"https://example.org/welt/impfstoffe","importance":4,"date":"2025-06-05"},
            {"title":"Regionale Handelsverhandlungen neu gestartet",
             "description":"Mehrere Staaten verhandeln die Modernisierung von Handelsabkommen. "
                          "Digitale Wirtschaft und Nachhaltigkeit stehen im Fokus. "
                          "Zollfragen und Standards werden diskutiert. "
                          "Unternehmer hoffen auf klarere Rahmenbedingungen. "
                          "Verhandlungen werden über Monate fortgeführt.",
             "link":"https://example.org/welt/handel","importance":3,"date":"2025-07-01"},
            {"title":"Humanitäre Konvois erreichen Krisenregion",
             "description":"Internationale Hilfsorganisationen lieferten dringend benötigte Güter an betroffene Gebiete. "
                          "Medizinische Versorgung und Lebensmittel konnten bereitgestellt werden. "
                          "Logistische Herausforderungen wurden teils gemeistert. "
                          "Lokale Helfer unterstützen Verteilung. "
                          "Weitere Hilfstransporte sind geplant.",
             "link":"https://example.org/welt/hilfe","importance":4,"date":"2025-04-20"},
            {"title":"Kultureller Austausch stärkt Dialog",
             "description":"Ein internationales Festival fördert Zusammenarbeit zwischen Künstlern. "
                          "Workshops und Ausstellungen dienen Verständigung. "
                          "Programme betonen lokale Teilhabe und Bildung. "
                          "Besucherzahlen stiegen gegenüber dem Vorjahr. "
                          "Initiativen werden fortgesetzt.",
             "link":"https://example.org/welt/kultur","importance":2,"date":"2025-03-08"},
            {"title":"Wasserprojekte starten gegen Dürre",
             "description":"Regionale Projekte zur effizienten Wassernutzung werden umgesetzt. "
                          "Techniken zur Rückgewinnung werden getestet. "
                          "Landwirte erhalten Schulungen für nachhaltige Bewässerung. "
                          "Projekte erhalten internationale Unterstützung. "
                          "Ziele sind Ertragsstabilisierung und Ressourcenschonung.",
             "link":"https://example.org/welt/wasser","importance":3,"date":"2025-02-14"},
            {"title":"Internationale Konferenz zu digitalen Rechten",
             "description":"Vertreter diskutierten Datenschutz, Zugang zu Netzen und digitale Bildung. "
                          "Abschlusserklärungen betonen Menschenrechte im digitalen Raum. "
                          "Konkrete nationale Umsetzungen wurden vereinbart. "
                          "Weiterer Austausch über Governance ist geplant. "
                          "Die Konferenz zog Vertreter aus vielen Ländern an.",
             "link":"https://example.org/welt/digital","importance":3,"date":"2025-05-16"},
            {"title":"Regionale Infrastrukturfinanzierung angekündigt",
             "description":"Finanzierungsprogramme für kleinere Infrastrukturprojekte wurden angekündigt. "
                          "Fokus liegt auf Straßen, Wasser und lokalen Energieprojekten. "
                          "Partizipation lokaler Gemeinden ist vorgesehen. "
                          "Zugänge zu Kreditlinien werden erleichtert. "
                          "Projekte sollen kurzfristig Arbeitsplätze schaffen.",
             "link":"https://example.org/welt/infrastruktur","importance":3,"date":"2025-01-30"},
        ],
        "Allgemein": [
            {"title":"Deutsche Bahn verbessert Pünktlichkeit",
             "description":"Die Bahn meldet bessere Pünktlichkeitswerte nach Umstellungen im Fahrplan. "
                          "Instandhaltungsmaßnahmen und digitale Tools halfen der Koordination. "
                          "Fahrgäste zeigen vorsichtigen Optimismus. "
                          "Weitere Investitionen sind angekündigt. "
                          "Langfristige Effekte sollen dann sichtbar werden.",
             "link":"https://example.org/allgemein/bahn","importance":3,"date":"2025-10-01"},
            {"title":"Kommunen fördern Grünprojekte",
             "description":"Städte starten neue Begrünungsprojekte zur Verbesserung des Mikroklimas. "
                          "Bürger werden in Planungsprozesse eingebunden. "
                          "Fördermittel flankieren kommunale Maßnahmen. "
                          "Naherholungsflächen werden erweitert. "
                          "Projekte werden wissenschaftlich begleitet.",
             "link":"https://example.org/allgemein/gruen","importance":2,"date":"2025-06-05"},
            {"title":"Verbraucherschutz bei Onlinekäufen verbessert",
             "description":"Neue Regeln stärken Informationspflichten und Rückgabeoptionen. "
                          "Konsumentenrechte werden klarer formuliert. "
                          "Kontrollen werden verschärft. "
                          "Händler müssen transparente Preisangaben machen. "
                          "Maßnahmen sollen Vertrauen in E-Commerce stärken.",
             "link":"https://example.org/allgemein/verbraucher","importance":4,"date":"2025-08-01"},
            {"title":"Bibliotheken bauen digitale Angebote aus",
             "description":"Städtische Bibliotheken öffnen digitale Lernräume und Medienwerkstätten. "
                          "Kooperationen mit Schulen werden intensiviert. "
                          "Flexiblere Öffnungszeiten erhöhen Nutzerzahlen. "
                          "Bildungsangebote werden gezielt erweitert. "
                          "Programme zielen auf inklusive Bildung.",
             "link":"https://example.org/allgemein/bibliothek","importance":2,"date":"2025-02-01"},
            {"title":"Katastrophenschutz übt Evakuierungen",
             "description":"Behörden führten groß angelegte Evakuierungsübungen. "
                          "Szenarien reichten von Fluten bis Industrieunfällen. "
                          "Kooperation zwischen Rettungskräften und Verwaltung wurde geprobt. "
                          "Kommunikation und Routenplanung wurden überprüft. "
                          "Ergebnisse fließen in künftige Pläne ein.",
             "link":"https://example.org/allgemein/katastrophen","importance":3,"date":"2025-01-08"},
            {"title":"Ehrenamtsbörsen vermitteln lokale Helfer",
             "description":"Freiwilligenbörsen vernetzen Ehrenamtliche und Projekte in Nachbarschaften. "
                          "Besonders Senioren- und Bildungsprojekte profitieren von neuen Angeboten. "
                          "Plattformen bieten Schulungen und Absicherungen an. "
                          "Engagement stärkt lokale Gemeinschaften. "
                          "Die Reichweite der Vermittlung wächst.",
             "link":"https://example.org/allgemein/ehrenamt","importance":2,"date":"2025-03-22"},
            {"title":"Gesundheitsämter starten Impfkampagnen",
             "description":"Regionale Impfaktionen werden mobil und in ländlichen Regionen angeboten. "
                          "Mobile Impfstationen verbessern Erreichbarkeit. "
                          "Informationskampagnen begleiten die Maßnahmen. "
                          "Kooperationen mit Apotheken erleichtern Logistik. "
                          "Maßnahmen zielen auf erhöhte Prävention.",
             "link":"https://example.org/allgemein/impfungen","importance":3,"date":"2025-04-10"},
            {"title":"Stadtplanung: Fahrradstraßen getestet",
             "description":"Pilotprojekte für Fahrradstraßen sollen sichere Verbindungen schaffen. "
                          "Verkehrsberuhigung und Infrastruktur sind Teil der Tests. "
                          "Nutzerbefragungen fließen in Entscheidungen ein. "
                          "Maßnahmen werden wissenschaftlich begleitet. "
                          "Erste Tests verliefen positiv.",
             "link":"https://example.org/allgemein/fahrrad","importance":2,"date":"2025-05-20"},
            {"title":"Lokale Kulturförderung unterstützt Initiativen",
             "description":"Förderprogramme stärken kleine Kulturprojekte und Jugendinitiativen. "
                          "Finanzielle Mittel und Coaching werden bereitgestellt. "
                          "Projekte verbessern kulturelle Vielfalt vor Ort. "
                          "Erfolgreiche Vorhaben werden als Modell adaptiert. "
                          "Bewerbungen sind offen für viele Träger.",
             "link":"https://example.org/allgemein/kultur","importance":2,"date":"2025-09-09"},
            {"title":"Mobilität: Neue Tests zu Car-Sharing-Konzepten",
             "description":"Städte testen alternative Mobilitätslösungen inklusive Car-Sharing-Modellen. "
                          "Ziel ist Reduktion städtischen Verkehrs und Emissionen. "
                          "Datenauswertung begleitet Pilotphasen. "
                          "Kooperationen mit Anbietern werden geprüft. "
                          "Erfahrungen fließen in Verkehrsplanung ein.",
             "link":"https://example.org/allgemein/mobilitaet","importance":3,"date":"2025-11-03"},
        ],
    }
    return dataset

# ----------------------------
# Analyzer: Tokenisierung, Stopwords, Sentiment, TF-like scoring
# ----------------------------
GERMAN_STOPWORDS = {
    # verkürzt; ausreichend für gute Ergebnisse offline
    "und","oder","aber","auch","als","an","auf","bei","der","die","das","ein","eine","in","im","ist","sind",
    "mit","zu","von","den","des","für","dass","dem","nicht","vor","nach","wie","er","sie","es","wir","ihr","ich",
    "bei","hat","haben","werden","wird","seit","mehr","dies","diese","sehr","nur","noch","auch","so","werden"
}

POSITIVE_LEXICON = {
    "gut","stark","erfolgreich","verbessert","gewinnt","begrüßt","optimistisch","stabil","steigerung","gewinn",
    "sicher","förder","förderung","unterstützt","erholen","aufwind"
}
NEGATIVE_LEXICON = {
    "kritisch","warn","warnen","risiko","risiken","verlust","problem","schwier","krise","fragil","stagn","einbruch",
    "verzöger","engpass","kritik","mangel"
}

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÄäÖöÜüß0-9]+", flags=re.UNICODE)

def tokenize(text):
    # Rückgabe: Liste von Tokens in Kleinschreibung, ohne Stopwords
    tokens = WORD_RE.findall(text.lower())
    tokens = [t for t in tokens if t not in GERMAN_STOPWORDS and len(t) > 2]
    return tokens

def sentiment_score_text(text):
    # einfacher Lexikon-basierter Score: pos_count - neg_count normalized
    tokens = tokenize(text)
    pos = sum(1 for t in tokens if any(p in t for p in POSITIVE_LEXICON))
    neg = sum(1 for t in tokens if any(n in t for n in NEGATIVE_LEXICON))
    total = pos + neg
    # Normalisierung: -1 .. 1
    if total == 0:
        return 0.0
    return (pos - neg) / total

# TF-IDF-like importance within dataset (simplified)
def compute_term_frequencies(corpus_texts):
    # corpus_texts: list of strings
    doc_tokens = [tokenize(t) for t in corpus_texts]
    df = Counter()
    tf_list = []
    for tokens in doc_tokens:
        tf = Counter(tokens)
        tf_list.append(tf)
        for term in set(tokens):
            df[term] += 1
    N = len(doc_tokens) if doc_tokens else 1
    idf = {term: math.log((N+1)/(df_count+1)) + 1 for term, df_count in df.items()}  # smoothed idf
    # return tf_list and idf
    return tf_list, idf

# ----------------------------
# Headline Scorer: bewertet Schlagzeilen nach Länge, Sentiment, Keywords, Importance
# Ergebnis 0..100 (höher = wichtiger/potentiell attraktiver)
# ----------------------------
def score_headline(article, idf_map=None, important_terms=None):
    # Basispunkte
    score = 0.0
    title = article.get("title","")
    desc = article.get("description","")
    importance = float(article.get("importance",3))
    # 1) Basis von importance
    score += importance * 10  # 10-50
    # 2) Sentiment (Artikel-Text)
    s = sentiment_score_text(title + " " + desc)
    score += s * 8  # -8 .. +8
    # 3) Länge: ideal ~6-12 Wörter
    t_tokens = tokenize(title)
    l = len(t_tokens)
    if 6 <= l <= 12:
        score += 8
    else:
        # penalty from optimum
        score += max(0, 8 - abs(l-9))
    # 4) Keyword boost via idf_map or manual important_terms
    boost = 0.0
    if idf_map:
        for w in set(t_tokens):
            boost += idf_map.get(w, 0.0) * 2.0
    if important_terms:
        for it in important_terms:
            if it in title.lower() or it in desc.lower():
                boost += 4.0
    score += boost
    # Normalize to 0..100
    score = max(-100, min(100, score))
    # Soft scaling
    normalized = (score + 100) / 2.0  # map -100..100 to 0..100
    return round(normalized, 1)

# ----------------------------
# News Analyzer Class (umfangreich)
# ----------------------------
class NewsAnalyzer:
    def __init__(self, dataset):
        # dataset = dict: category -> list of articles
        self.dataset = dataset
        # build corpus-level TF/IDF on initialization (fast: ~70 docs)
        all_texts = []
        for cat, articles in self.dataset.items():
            for art in articles:
                all_texts.append(art["title"] + " " + art["description"])
        self.tf_list, self.idf_map = compute_term_frequencies(all_texts)
        # Precompute category-level stats
        self.category_stats = {}
        self._compute_category_stats()

    def _compute_category_stats(self):
        for cat, articles in self.dataset.items():
            texts = [a["title"] + " " + a["description"] for a in articles]
            tokens = [token for t in texts for token in tokenize(t)]
            freq = Counter(tokens)
            # sentiment per article
            sentiments = [sentiment_score_text(t) for t in texts]
            avg_sent = sum(sentiments)/len(sentiments) if sentiments else 0.0
            avg_imp = sum(a.get("importance",3) for a in articles)/len(articles) if articles else 0.0
            # collect monthly counts
            month_counts = Counter()
            for a in articles:
                try:
                    dt = datetime.strptime(a.get("date","1970-01-01"), "%Y-%m-%d")
                    month_counts[dt.strftime("%Y-%m")] += 1
                except Exception:
                    pass
            top_terms = [w for w,_ in freq.most_common(10)]
            self.category_stats[cat] = {
                "token_freq": freq,
                "top_terms": top_terms,
                "avg_sentiment": round(avg_sent,3),
                "avg_importance": round(avg_imp,3),
                "month_counts": dict(month_counts)
            }

    def top_keywords_global(self, top_n=15):
        all_tokens = Counter()
        for v in self.category_stats.values():
            all_tokens.update(v["token_freq"])
        return [t for t,_ in all_tokens.most_common(top_n)]

    def category_summary(self, category):
        return self.category_stats.get(category, {})

    def sentiment_distribution(self, category=None):
        # return counts of positive/neutral/negative per category or global
        def classif(s):
            if s > 0.2: return "positive"
            if s < -0.2: return "negative"
            return "neutral"
        buckets = Counter()
        if category:
            arts = self.dataset.get(category, [])
        else:
            arts = [a for lst in self.dataset.values() for a in lst]
        for a in arts:
            t = a["title"] + " " + a["description"]
            s = sentiment_score_text(t)
            buckets[classif(s)] += 1
        return dict(buckets)

    def top_headlines(self, category, top_n=10):
        # score each article using score_headline
        articles = list(self.dataset.get(category, []))
        # important terms: top global keywords
        important_terms = self.top_keywords_global(8)
        scored = []
        for art in articles:
            sc = score_headline(art, idf_map=self.idf_map, important_terms=important_terms)
            scored.append((sc, art))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(s, a) for s, a in scored[:top_n]]

    def trend_time_series(self, category):
        stats = self.category_stats.get(category, {})
        months = stats.get("month_counts", {})
        # return sorted month -> count
        return sorted(months.items(), key=lambda x:x[0])

# ----------------------------
# CLI Menu & Interaction
# ----------------------------
class UserManager:
    def __init__(self):
        self.file = USERS_FILE
        self.users = safe_load_json(self.file, {})
        # simple storage: username -> password (plaintext for offline demo)
        # for production bitte hashen (bcrypt)
    def register(self, username, password):
        if username in self.users:
            return False, "Benutzer existiert bereits."
        self.users[username] = {
            "password": password,
            "created": datetime.utcnow().isoformat()
        }
        safe_save_json(self.file, self.users)
        return True, "Registrierung erfolgreich."
    def login(self, username, password):
        user = self.users.get(username)
        if not user:
            return False, "Benutzer nicht gefunden."
        if user.get("password") != password:
            return False, "Falsches Passwort."
        return True, "Login erfolgreich."

class CLI:
    def __init__(self):
        self.news = build_news_dataset()
        self.analyzer = NewsAnalyzer(self.news)
        self.users = UserManager()
        self.settings = safe_load_json(SETTINGS_FILE, {"sort_mode":"neueste"})
        self.current_user = None

    def run(self):
        print("=== Lumina News (Offline) ===")
        # Login/Register Loop
        while True:
            print("\nBitte Einloggen oder Registrieren:")
            print("1) Login")
            print("2) Registrierung")
            print("3) Als Gast fortfahren")
            print("0) Beenden")
            choice = input("Auswahl: ").strip()
            if choice == "1":
                self._do_login()
                if self.current_user:
                    break
            elif choice == "2":
                self._do_register()
            elif choice == "3":
                self.current_user = "Gast"
                break
            elif choice == "0":
                print("Auf Wiedersehen.")
                sys.exit(0)
            else:
                print("Ungültige Auswahl.")

        # Main Menu
        self.main_menu_loop()

    def _do_login(self):
        u = input("Benutzername: ").strip()
        p = input("Passwort: ").strip()
        ok, msg = self.users.login(u,p)
        print(msg)
        if ok:
            self.current_user = u

    def _do_register(self):
        u = input("Gewünschter Benutzername: ").strip()
        p = input("Passwort: ").strip()
        ok, msg = self.users.register(u,p)
        print(msg)

    def main_menu_loop(self):
        while True:
            print(f"\n--- Hauptmenü (angemeldet als: {self.current_user}) ---")
            print("1) Kategorien anzeigen")
            print("2) Analyzer / Trends")
            print("3) Suche (Titel/Texte)")
            print("4) Einstellungen (Sortierung)")
            print("5) Export: Kategorie -> JSON")
            print("0) Abmelden / Beenden")
            choice = input("Auswahl: ").strip()
            if choice == "1":
                self.categories_menu()
            elif choice == "2":
                self.analyzer_menu()
            elif choice == "3":
                self.search_menu()
            elif choice == "4":
                self.settings_menu()
            elif choice == "5":
                self.export_menu()
            elif choice == "0":
                print("Abmelden. Auf Wiedersehen.")
                sys.exit(0)
            else:
                print("Ungültig.")

    def categories_menu(self):
        cats = list(self.news.keys())
        while True:
            print("\nKategorien:")
            for i, c in enumerate(cats, start=1):
                print(f"{i}) {c}")
            print("0) Zurück")
            sel = input("Kategorie wählen: ").strip()
            if sel == "0":
                return
            try:
                idx = int(sel)-1
                if idx < 0 or idx >= len(cats):
                    print("Ungültige Nummer.")
                    continue
                cat = cats[idx]
                self.show_category(cat)
            except ValueError:
                print("Bitte Zahl eingeben.")

    def show_category(self, category):
        articles = list(self.news.get(category, []))
        # sort according settings
        sort_mode = self.settings.get("sort_mode", "neueste")
        if sort_mode == "wichtig" or sort_mode == "importance":
            articles.sort(key=lambda x: x.get("importance",0), reverse=True)
        else:
            # parse dates, fallback to original order
            def parse_date(a):
                try:
                    return datetime.strptime(a.get("date","1970-01-01"), "%Y-%m-%d")
                except Exception:
                    return datetime(1970,1,1)
            articles.sort(key=lambda x: parse_date(x), reverse=True)

        # Paging: 5 pro Seite
        page_size = 5
        page = 0
        total_pages = math.ceil(len(articles)/page_size) if articles else 1
        while True:
            start = page*page_size
            end = start + page_size
            print(f"\n--- {category} (Seite {page+1}/{total_pages}) ---")
            for i, art in enumerate(articles[start:end], start=1):
                print(f"{i}) {art['title']}  [{art['date']}] (W:{art['importance']})")
            print("\nn) nächste Seite, p) vorherige Seite, v#) Ansicht Artikel (z.B. v2), h) Top Headlines, b) zurück")
            cmd = input("Auswahl: ").strip().lower()
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
                # view article number
                try:
                    num = int(cmd[1:]) - 1
                    idx = start + num
                    if idx < 0 or idx >= len(articles):
                        print("Ungültige Nummer.")
                        continue
                    self.view_article(articles[idx])
                except Exception:
                    print("Ungültiges Format. Beispiel 'v2' um Artikel 2 anzuzeigen.")
            elif cmd == "h":
                # show top headlines scored
                top = self.analyzer.top_headlines(category, top_n=10)
                print(f"\nTop Headlines in {category}:")
                for rank, (score, art) in enumerate(top, start=1):
                    print(f"{rank}. [{score}] {art['title']} ({art['date']}) - W:{art['importance']}")
                print("Enter zum Weitermachen.")
                input()
            elif cmd == "b":
                return
            else:
                print("Unbekannter Befehl.")

    def view_article(self, article):
        print("\n--- Artikel ---")
        print(f"Titel: {article.get('title')}")
        print(f"Datum: {article.get('date')} | Wichtigkeit: {article.get('importance')}")
        print(f"Link: {article.get('link')}")
        print("\nBeschreibung:")
        print(article.get("description"))
        # On-the-fly analyses
        s = sentiment_score_text(article.get("title","") + " " + article.get("description",""))
        print(f"\n[Analyse] Sentiment-Score (Proxy): {round(s,3)}")
        # headline score
        hs = score_headline(article, idf_map=self.analyzer.idf_map, important_terms=self.analyzer.top_keywords_global(8))
        print(f"[Analyse] Headline-Score: {hs}/100")
        print("\nAktionen: r) zurück")
        inp = input("Taste: ").strip().lower()
        return

    def analyzer_menu(self):
        while True:
            print("\n--- Analyzer / Trends ---")
            print("1) Top globale Keywords")
            print("2) Kategoriesummary")
            print("3) Sentiment-Verteilung (global oder Kategorie)")
            print("4) Trend Zeitreihe (Kategorie)")
            print("0) Zurück")
            choice = input("Auswahl: ").strip()
            if choice == "1":
                keys = self.analyzer.top_keywords_global(20)
                print("Top Keywords (global):")
                print(", ".join(keys))
            elif choice == "2":
                for cat in self.news.keys():
                    s = self.analyzer.category_summary(cat)
                    print(f"\n{cat}:")
                    print(f" Top Terms: {', '.join(s.get('top_terms',[])[:8])}")
                    print(f" Avg Sentiment: {s.get('avg_sentiment')} | Avg Importance: {s.get('avg_importance')}")
            elif choice == "3":
                sub = input("Für Kategorie spezifizieren? (leer für global): ").strip()
                res = self.analyzer.sentiment_distribution(sub if sub else None)
                print("Sentiment-Verteilung:", res)
            elif choice == "4":
                cat = input("Kategorie (genauer Name): ").strip()
                ts = self.analyzer.trend_time_series(cat)
                if not ts:
                    print("Keine zeitlichen Daten.")
                else:
                    for month, count in ts:
                        print(f"{month}: {count} Artikel")
            elif choice == "0":
                return
            else:
                print("Ungültig.")

    def search_menu(self):
        q = input("Suchbegriff (Titel/Beschreibung): ").strip().lower()
        if not q:
            print("Leere Suche.")
            return
        results = []
        for cat, arts in self.news.items():
            for a in arts:
                if q in a.get("title","").lower() or q in a.get("description","").lower():
                    results.append((cat, a))
        if not results:
            print("Keine Treffer.")
            return
        print(f"{len(results)} Treffer:")
        for i, (cat, a) in enumerate(results, start=1):
            print(f"{i}) [{cat}] {a['title']} ({a['date']}) - W:{a['importance']}")
        sel = input("Artikelnummer öffnen (oder Enter um zurück): ").strip()
        if sel:
            try:
                idx = int(sel)-1
                if 0 <= idx < len(results):
                    self.view_article(results[idx][1])
            except Exception:
                print("Ungültige Auswahl.")

    def settings_menu(self):
        print("\n--- Einstellungen ---")
        cur = self.settings.get("sort_mode","neueste")
        print(f"Aktuelle Sortierung: {cur} (Optionen: neueste / wichtig)")
        new = input("Neue Sortierung (leer = behalten): ").strip().lower()
        if new in ("neueste","wichtig","importance","date"):
            if new == "date": new = "neueste"
            if new == "importance": new = "wichtig"
            self.settings["sort_mode"] = new
            safe_save_json(SETTINGS_FILE, self.settings)
            print("Einstellung gespeichert.")
        elif new == "":
            print("Keine Änderung.")
        else:
            print("Ungültige Option.")

    def export_menu(self):
        print("\n--- Export: Kategorie -> JSON ---")
        cats = list(self.news.keys())
        for i,c in enumerate(cats, start=1):
            print(f"{i}) {c}")
        sel = input("Kategorie wählen (Nummer) oder 0 für abbrechen: ").strip()
        if sel == "0":
            return
        try:
            idx = int(sel)-1
            if idx < 0 or idx >= len(cats):
                print("Ungültig.")
                return
            cat = cats[idx]
            filename = f"export_{cat.replace(' ','_')}.json"
            safe_save_json(filename, self.news[cat])
            print(f"Exportiert: {filename}")
        except Exception as e:
            print("Fehler beim Export:", e)

# ----------------------------
# Start
# ----------------------------
def main():
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()
