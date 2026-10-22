Version **0.2.0** ergänzt die Einrichtung der Verbindung zwischen Anki und einem KI-Client direkt im Add-on.

- Offline-Anleitung unter **Werkzeuge → Anki MCP – Einrichtung & Hilfe**, mit konkreten Schritten für Claude Desktop unter **Windows und macOS**, Cursor-/Codex-Hinweisen und einer Erklärung der ChatGPT-Grenzen.
- Verbindungsreiter mit Python-Dateiauswahl, tatsächlichen Installationspfaden und kopierbarer Client-Konfiguration.
- Lesender Test von Anmeldung, MCP-Initialisierung, Werkzeugen und Zugriff auf das geöffnete Profil.
- Standalone-stdio-Bridge direkt im Add-on; kein zusätzlicher Repository-Download nötig. UTF-8-Ausgabe auch bei abweichender Windows-Pipe-Kodierung.
- Weiterhin 61 Werkzeuge für Sammlung, Medien, Bildverdeckung, Lernstände und Deck-Einstellungen inklusive FSRS.

**Installation oder Update:** `anki-mcp-0.2.0.ankiaddon` herunterladen, über **Werkzeuge → Erweiterungen → Aus Datei installieren…** installieren und Anki vollständig neu starten. Das Paket verwendet dieselbe Add-on-ID wie 0.1.0.

**Geprüft:** Automatisierte Linux-Prüfungen mit echten Anki-Sammlungen, offiziellen MCP-Clients und realem Qt-Dialog. Tests der installierten Bridge aus einem Pfad mit Leerzeichen, Unicode-Medizinbegriffen und abweichender Pipe-Kodierung.

**Plattformstatus:** Windows und macOS (Apple Silicon/Intel) sind feste Zielplattformen. Die entsprechende GitHub-Actions-Matrix ist vorbereitet, aber noch nicht ausgeführt. Eine bestätigte Freigabe nach nativen Tests und manueller Endabnahme steht noch aus. GitHub-Veröffentlichung bleibt bis zur Bereitstellung eines Repositorys offen.
