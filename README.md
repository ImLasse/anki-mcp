# Anki MCP

Ein natives **Anki-Desktop-Add-on**, mit dem KI-Assistenten deine bestehende Sammlung bearbeiten und deinen Lernstand auswerten können. Entwickelt für umfangreiche Lernsammlungen, insbesondere im Medizinstudium. Kein AnkiConnect erforderlich; keine zusätzlichen Python-Pakete im Add-on erforderlich.

**61 MCP-Werkzeuge** für Decks, Notizen, Karten, Medien, native Bildverdeckung, Tags, Lernplanung, Statistiken und vollständige native Deck-Optionsvorlagen. Verbindung über lokales Streamable HTTP oder eine mitgelieferte Python-stdio-Bridge.

## Funktionen

| Bereich | Unterstützung |
| --- | --- |
| Bestehende Sammlung | Decks, Notizen und Karten lesen; vollständige Anki-Suchsyntax, paginierte Ergebnisse |
| Decks | Anlegen, umbenennen, verschachteln, löschen, Beschreibungen, Karten verschieben, Optionsvorlagen zuweisen |
| Notizen und Karten | Einzeln oder in Batches anlegen/bearbeiten; HTML, Cloze, Basic, umgekehrte Karten, eigene Felder, Vorlagen und CSS; Notiztyp wechseln |
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

1. `anki-mcp-0.1.0.ankiaddon` unter [Releases](https://github.com/ImLasse/anki-mcp/releases) herunterladen.
2. In Anki: **Werkzeuge → Erweiterungen → Aus Datei installieren…** und die Datei auswählen.
3. Anki neu starten und dein Profil öffnen.
4. **Werkzeuge → Anki MCP – Verbindung** öffnen. Dort stehen die lokalen Verbindungsdaten und der Pfad zur automatisch erzeugten Token-Datei.
5. Deinen MCP-Client wie unten konfigurieren. Anki und das gewünschte Profil müssen geöffnet bleiben.

Unterstützte Basis: **Anki 25.09.5 oder neuer**. Automatisierte Integrationsprüfungen verwenden **25.09.5 und 26.09.3**. Das Add-on funktioniert unter Anki Desktop; AnkiMobile/AnkiDroid laden keine Desktop-Add-ons. Die Python-Bridge benötigt separat **Python 3.10+** auf deinem Computer.

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

### stdio-Clients, zum Beispiel Claude Desktop

Das Repository herunterladen/klonen und die Datei `scripts/anki_mcp_bridge.py` dauerhaft lokal speichern. Anschließend in der MCP-Konfiguration absolute Pfade verwenden:

```json
{
  "mcpServers": {
    "anki": {
      "command": "/ABSOLUTER/PFAD/ZU/python3",
      "args": [
        "/ABSOLUTER/PFAD/anki-mcp/scripts/anki_mcp_bridge.py",
        "--token-file",
        "/ABSOLUTER/PFAD/ZUM/ANKI-ADDON/user_files/token"
      ]
    }
  }
}
```

Unter Windows zum Beispiel `C:\\Python312\\python.exe` und entsprechend doppelt maskierte Dateipfade verwenden. Alternativ akzeptiert die Bridge die Umgebungsvariable `ANKI_MCP_TOKEN`. Bei geändertem Port zusätzlich `--url http://127.0.0.1:DEIN_PORT/mcp` übergeben.

**Cloud-Clients:** Ein entfernter KI-Dienst kann deinen lokalen `127.0.0.1`-Server nicht direkt erreichen. Er benötigt einen lokalen MCP-fähigen Client bzw. eine passende lokale Verbindung. Dieses Projekt richtet keinen öffentlichen Server oder Tunnel ein.

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

Ausgabe: `dist/anki-mcp-0.1.0.ankiaddon`. Der Build ist reproduzierbar und nimmt ausschließlich Add-on-Quellcode, statische Konfiguration und Lizenz auf; Laufzeitdaten und Zugangstoken werden ausgeschlossen.

## Umfang und Grenzen dieser Version

Version **0.1.0** ist eine breite erste Implementierung der oben aufgeführten Sammlungs- und Lernfunktionen. Sie ist kein Nachweis einer vollständigen 1:1-Abdeckung jeder Anki-GUI-Funktion oder fremder Add-ons. Nicht enthalten sind AnkiWeb-Login/Sync, Profilverwaltung, Aufnahme/TTS/Transkription von Audio, OCR oder automatische medizinische Quellenrecherche. Bilder und Audiodateien können von einem KI-Client erzeugt und anschließend importiert werden. CSV-/Textdateien lassen sich vom Client in `add_notes`-Aufrufe umsetzen; der native Dateiaustausch hier verwendet `.apkg`.

Es gibt automatisierte Backend-, MCP- und Qt-Adaptertests. Eine manuelle Endabnahme mit deinem Desktop, deinem konkreten KI-Client und deiner persönlichen Sammlung steht noch aus. Große Exporte, Statistiken oder FSRS-Berechnungen können die Oberfläche während des Aufrufs blockieren. Details zu Versionen, Dateneinheiten und weiteren Grenzen stehen in [architecture.md](docs/architecture.md).

Lizenz: [GNU AGPL v3 oder neuer](LICENSE). Anki ist ein separates Projekt von Ankitects und seinen Beitragenden.
