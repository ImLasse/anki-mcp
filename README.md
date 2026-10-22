# Anki MCP

Ein natives **Anki-Desktop-Add-on**, mit dem KI-Assistenten deine bestehende Sammlung bearbeiten und deinen Lernstand auswerten können. Entwickelt für umfangreiche Lernsammlungen, insbesondere im Medizinstudium. Kein AnkiConnect erforderlich; keine zusätzlichen Python-Pakete im Add-on erforderlich.

**80 MCP-Werkzeuge** für Decks, Notizen, Karten, Medien, native Bildverdeckung, Tags, Lernplanung, Statistiken und vollständige native Deck-Optionsvorlagen. Verbindung über lokales Streamable HTTP oder eine mitgelieferte Python-stdio-Bridge.

## Neu in 0.4.0

- **Änderungsvorschau:** Vorher/Nachher für bestehende Notizen, Tags, Karten und Deck-Einstellungen. Gespeicherte Pläne laufen nach 24 Stunden ab und lehnen inzwischen veränderte Ziele ab.
- **Dauerhaftes Protokoll:** MCP-Schreibzugriffe und begrenzte Zustandsdaten über Neustarts hinweg; in Anki unter **Einrichtung & Hilfe → Änderungsprotokoll**.
- **Ähnliche Karten:** Lokale Textähnlichkeit liefert Kandidaten zur fachlichen Prüfung durch die KI, ohne automatische Zusammenführung.
- **Prüfungsplanung:** Termin, Tages-/Wochenbudget, Themen, vorhandene Fälligkeiten und neue Karten; Überlastung und nicht eingeplante Karten werden sichtbar.
- **Strukturierte Quellen:** Revisionen, Notizverknüpfungen und Prüfbedarf nach Quellenänderungen; exportierbare lokale Metadaten.
- **Einfachere Claude-Einrichtung:** Zusätzliches `.mcpb`-Paket für Claude Desktop unter Windows und macOS, ohne separate Python-Installation. Die bestehenden Claude-/Codex-/ChatGPT-Anleitungen bleiben enthalten.

Die Basisversion **0.3.0** wurde vor diesen Erweiterungen auf `main` gesichert. Details und Grenzen: [neue Abläufe](docs/workflows.md). Upload, vorbereitete Beschreibung und Umstellung auf eine AnkiWeb-ID: [AnkiWeb-Anleitung](docs/ankiweb.md).

**Einfach updaten:** Neue `.ankiaddon` über **Werkzeuge → Erweiterungen → Aus Datei installieren…** installieren; alte Version nicht vorher löschen. Danach Anki und KI-Client neu starten. Die Paket-ID bleibt `anki_mcp`, `user_files` bleibt erhalten. Nach der ersten AnkiWeb-Veröffentlichung sind Updates über **Auf Aktualisierungen überprüfen** möglich. GitHub-Updates allein erscheinen dort noch nicht.

## Funktionen

| Bereich | Unterstützung |
| --- | --- |
| Bestehende Sammlung | Decks, Notizen und Karten lesen; vollständige Anki-Suchsyntax, paginierte Ergebnisse |
| Decks | Anlegen, umbenennen, verschachteln, löschen, Beschreibungen, Karten verschieben, Optionsvorlagen zuweisen |
| Notizen und Karten | Vorschau ohne Speichern, technische Qualitätsprüfung; einzeln oder in Batches anlegen/bearbeiten; HTML, Cloze, Basic, umgekehrte Karten, eigene Felder, Vorlagen und CSS; Notiztyp wechseln |
| Bilder, Audio und Video | Medien hochladen/lesen, kollisionssichere Dateinamen, Referenzen in Feldern, fehlende/ungenutzte Medien finden, Medienpapierkorb |
| Bildverdeckung | Native Anki Image Occlusion erstellen, lesen und bearbeiten; Rechtecke mit normalisierten Koordinaten; native Maskensyntax für weitere Formen und Gruppen |
| Tags | Hierarchische Tags suchen, hinzufügen, entfernen, umbenennen und global löschen |
| Lernzustände | Fälligkeit, Intervalle, Wiederholungen, Fehlversuche, Aussetzung, Vergraben, Flags, FSRS-Stabilität/-Schwierigkeit und berechneter Gedächtniszustand |
| Lernanalyse | Native Diagrammdaten, Wiederholungshistorie, Zeiten und Bewertungen, Themenanalyse über Suchabfragen, Fälligkeitsvorschau, Leeches und häufige Fehlversuche |
| Deck-Einstellungen | Alle nativen Optionsfelder, inklusive FSRS-Parameter, Behaltensquote, tägliche Limits, Lernschritte, Reihenfolge, Geschwisterkarten, Timer und Audio; individuelle Deck-Limits |
| Lernplanung | Aussetzen/aktivieren, vergraben/ausgraben, Fälligkeit setzen, vergessen, neue Karten umsortieren; gefilterte Decks und natives benutzerdefiniertes Lernen |
| Wiederholen | Aktuelle Warteschlange lesen; echte Antworten über Ankis Scheduler mit Wiederholungshistorie abgeben |
| FSRS | Parameter aus bestehender Lernhistorie berechnen oder evaluieren; Vorschau und explizites Anwenden getrennt |
| Pflege und Austausch | Duplikate, Suchen/Ersetzen, leere Karten, Undo/Redo, native Backups, `.apkg` mit Medien und Lernständen importieren/exportieren |

Vollständiger [Werkzeugkatalog](docs/tools.md), [Eingabeschemas](docs/tools.json), [Medizin-Beispiele](docs/medizin.md) und [technische Details/Grenzen](docs/architecture.md).

## Installation

1. `anki-mcp-0.4.0.ankiaddon` unter [Releases](https://github.com/ImLasse/anki-mcp/releases) herunterladen.
2. In Anki: **Werkzeuge → Erweiterungen → Aus Datei installieren…** und die Datei auswählen.
3. Anki neu starten und dein Profil öffnen.
4. **Werkzeuge → Anki MCP – Einrichtung & Hilfe** öffnen. Die offline verfügbare Anleitung erklärt die Verbindung zur KI unter **Windows und macOS**. Der Reiter **Verbindung** zeigt deine tatsächlichen Pfade und kopierbare Client-Einstellungen.
5. Deinen MCP-Client wie unten konfigurieren. Anki und das gewünschte Profil müssen geöffnet bleiben.

Unterstützte Basis: **Anki 25.09.5 oder neuer**. Automatisierte Integrationsprüfungen verwenden **25.09.5 und 26.09.3**. Das Add-on funktioniert unter Anki Desktop; AnkiMobile/AnkiDroid laden keine Desktop-Add-ons. Die Python-Bridge benötigt separat **Python 3.10+**; das Claude-MCPB-Paket verwendet die Node-Laufzeit von Claude Desktop.

### MCP-Clients mit Streamable HTTP und eigenen Headern

Beispiel für Clients mit JSON-Konfiguration; das genaue Konfigurationsformat hängt vom Client ab:

```json
{
  "mcpServers": {
    "anki": {
      "url": "http://127.0.0.1:8766/mcp",
      "headers": { "Authorization": "Bearer DEIN_TOKEN_AUS_ANKI" }
    }
  }
}
```

Der Verbindungsdialog in Anki enthält diese Konfiguration mit deinem tatsächlichen Token. Manche Clients verlangen zusätzlich `type: "http"` oder einen anderen Konfigurationsschlüssel.

### Claude Desktop: Erweiterungsdatei unter Windows und macOS

`anki-mcp-claude-0.4.0.mcpb` aus demselben Release in Claude **Einstellungen → Erweiterungen** als lokale Erweiterung installieren. In Anki unter **Verbindung → Claude Desktop – Erweiterungsdatei (.mcpb)** den Token-Dateipfad und Port ablesen und in Claude übernehmen. Anki geöffnet lassen und zunächst nur Decknamen lesen. Das Paket ist separat vom Anki-Add-on; die vollständigen Schritte und eine manuelle Alternative stehen in der [eingebauten Hilfe](addon/setup_help.md).

### stdio-Clients, zum Beispiel Claude Desktop

Die eigenständig ausführbare Datei `bridge.py` ist bereits im installierten Add-on enthalten. Im Anki-Menü **Anki MCP – Einrichtung & Hilfe → Verbindung** die Verbindungsart **stdio** auswählen, den absoluten Pfad zu Python 3.10+ eintragen und die Konfiguration kopieren. Ein zusätzlicher Repository-Download ist nicht nötig. Für die Entwicklung bleibt `scripts/anki_mcp_bridge.py` als Einstiegspunkt verfügbar. Beispiel:

```json
{
  "mcpServers": {
    "anki": {
      "command": "/ABSOLUTER/PFAD/ZU/python3",
      "args": [
        "/ABSOLUTER/PFAD/ZUM/ANKI-ADDON/bridge.py",
        "--token-file",
        "/ABSOLUTER/PFAD/ZUM/ANKI-ADDON/user_files/token"
      ]
    }
  }
}
```

Unter Windows zum Beispiel `C:\Python312\python.exe` verwenden. JSON benötigt doppelte Backslashes; die Kopierfunktion in Anki übernimmt das automatisch. Alternativ akzeptiert die Bridge die Umgebungsvariable `ANKI_MCP_TOKEN`. Bei geändertem Port zusätzlich `--url http://127.0.0.1:DEIN_PORT/mcp` übergeben.

**Cloud-Clients:** Ein entfernter KI-Dienst kann deinen lokalen `127.0.0.1`-Server nicht direkt erreichen. Er benötigt einen lokalen MCP-fähigen Client bzw. eine passende lokale Verbindung. Dieses Projekt richtet keinen öffentlichen Server oder Tunnel ein.

## Windows und macOS: Verbindung zur KI

Die vollständige Anleitung wird mit dem Add-on ausgeliefert: **Werkzeuge → Anki MCP – Einrichtung & Hilfe**. Sie ist auch als [setup_help.md](addon/setup_help.md) lesbar und enthält:

- Claude Desktop unter Windows: MCP-Konfiguration öffnen, Python-Interpreter auswählen, JSON-Eintrag ergänzen und Client neu starten.
- Claude Desktop unter macOS: entsprechende Schritte mit Finder-/Library-Pfaden sowie Hinweisen für Apple Silicon und Intel.
- Kopierbare Claude-/stdio-JSON-, Codex-TOML- und ChatGPT-Tunnel-YAML-Profile sowie die Unterschiede der Verbindungswege.
- Einen ausdrücklich lesenden ersten KI-Aufruf und Hilfe bei Port-, Token-, Python- und Pfadfehlern.
- Einen integrierten Verbindungstest für MCP-Initialisierung, Werkzeuge und Zugriff auf das geöffnete Profil. Der Test bestätigt noch nicht die Konfiguration eines externen KI-Clients.

**ChatGPT:** Der Verbindungsreiter erzeugt ein vorbereitetes YAML-Profil für den offiziellen **Secure MCP Tunnel**. Tunnelclient, Tunnel-ID und berechtigtes OpenAI-/ChatGPT-Konto sind zusätzlich erforderlich; diese Verbindung wurde hier noch nicht mit einem echten Konto abgenommen. Die [eingebaute Anleitung](addon/setup_help.md) erklärt die Schritte für Windows und macOS. ChatGPT kann den lokalen Server nicht direkt erreichen. [Offizielle Tunnel-Dokumentation](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).

**Plattformstatus:** Der Nutzer bestätigt den Einsatz unter Windows und macOS. Die automatisierte Matrix prüft Windows und Linux mit Anki 25.09.5/26.09.3 sowie macOS auf Apple Silicon und Intel mit 26.09.3. Die Matrix für die Basisversion 0.3.0 ist [erfolgreich durchgelaufen](https://github.com/ImLasse/anki-mcp/actions/runs/39792517382). Aktuelle Ergebnisse stehen unter [Actions](https://github.com/ImLasse/anki-mcp/actions). Die Tests verwenden echte temporäre Sammlungen, Qt und den offiziellen MCP-Client; sie ersetzen keine vollständige manuelle Prüfung jeder Client-Version und Funktion.

## Direkt ausprobieren

Nach der Verbindung kannst du deinem Assistenten zum Beispiel schreiben:

> Lies meine Decks und fasse meinen Lernstand für Kardiologie zusammen. Zeige fällige Karten, wiederholte Fehlversuche, Leeches und die aktuellen FSRS-/Deck-Einstellungen.

> Erstelle im Deck Medizin::Anatomie zehn Cloze-Notizen zum Plexus brachialis. Verwende Tags Medizin::Anatomie::Plexus und speichere die von mir angegebenen Quellen in einem Quellenfeld.

> Suche Karten mit tag:Altfragen::M1, zeige mir zunächst die Treffer und setze danach die ausgewählten Karten aus.

> Erstelle aus diesem beschrifteten Anatomiebild native Bildverdeckungskarten. Nutze eine Karte pro Beschriftung und übernimm die Quelle auf die Rückseite.

## Verhalten bei Änderungen

- Änderungen an der Sammlung laufen auf Ankis Qt-Hauptthread. Wenn Anki mit einer anderen Operation beschäftigt ist, wird der MCP-Aufruf abgewiesen und kann anschließend erneut versucht werden.
- Zusammengehörige Sammlungsänderungen erhalten einen eigenen Undo-Eintrag. Löschen, echte Lernantworten, Suchen/Ersetzen und einige größere Änderungen verlangen `confirm: true` im Werkzeugaufruf. Die KI sollte zuerst die betroffenen Objekte zeigen.
- `set_deck_options` erzeugt standardmäßig eine eigene Optionsvorlage für das Zieldeck. `shared: true` ändert die geteilte Vorlage und damit alle zugeordneten Decks. `global_fsrs` ist ausdrücklich sammlungsweit.
- Das Entfernen einer Cloze-Lücke oder Bildmaske löscht vorhandene Kartenhistorie nicht automatisch. `empty_cards` und `delete_cards` ermöglichen die gezielte Bereinigung.
- Medienoperationen und Paketimporte/-exporte haben kein Sammlungs-Undo. Vor größeren Änderungen `create_backup` verwenden; ein natives Anki-Backup enthält keine Medien, ein Medienexport als `.apkg` schon.
- Jeder berechtigte Client kann deine Sammlung verändern. Verbindungsdaten lokal halten. Übermittelte Karteninhalte werden vom gewählten KI-Client verarbeitet.

## Entwicklung

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q
.venv/bin/ruff check addon scripts tests
.venv/bin/ruff format --check addon scripts tests
.venv/bin/python scripts/generate_tool_docs.py
.venv/bin/python scripts/build.py
```

Für die Qt-Integrationstests zusätzlich zur passenden Anki-Version `aqt`, `PyQt6` und `PyQt6-WebEngine` installieren und `QT_QPA_PLATFORM=offscreen` setzen. Ohne `aqt` wird dieser Test übersprungen. Tests erstellen temporäre echte Anki-Sammlungen und verwenden den offiziellen MCP-Python-Client für HTTP und stdio. Sie greifen nicht auf persönliche Profile zu.

Ausgabe: `dist/anki-mcp-0.4.0.ankiaddon` und `dist/anki-mcp-claude-0.4.0.mcpb`. Für die MCPB-Integrationstests zusätzlich Node 20+ installieren. Der Build ist reproduzierbar und nimmt ausschließlich Add-on-Quellcode, statische Konfiguration und Lizenz auf; Laufzeitdaten und Zugangstoken werden ausgeschlossen.

## Umfang und Grenzen dieser Version

Version **0.4.0** ist eine breite erste Implementierung der oben aufgeführten Sammlungs- und Lernfunktionen. Sie ist kein Nachweis einer vollständigen 1:1-Abdeckung jeder Anki-GUI-Funktion oder fremder Add-ons. Nicht enthalten sind AnkiWeb-Login/Sync, Profilverwaltung, Aufnahme/TTS/Transkription von Audio, OCR oder automatische medizinische Quellenrecherche. Bilder und Audiodateien können von einem KI-Client erzeugt und anschließend importiert werden. CSV-/Textdateien lassen sich vom Client in `add_notes`-Aufrufe umsetzen; der native Dateiaustausch hier verwendet `.apkg`.

Es gibt automatisierte Backend-, MCP- und Qt-Adaptertests. Der Nutzer berichtet erfolgreiche Nutzung unter Windows und macOS; eine vollständige manuelle Endabnahme aller Funktionen und KI-Clients ist damit noch nicht belegt. Große Exporte, Statistiken oder FSRS-Berechnungen können die Oberfläche während des Aufrufs blockieren. Details zu Versionen, Dateneinheiten und weiteren Grenzen stehen in [architecture.md](docs/architecture.md).

Lizenz: [GNU AGPL v3 oder neuer](LICENSE). Anki ist ein separates Projekt von Ankitects und seinen Beitragenden.
