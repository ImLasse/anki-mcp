# Änderungen

## 0.3.0

- 65 MCP-Werkzeuge mit abrufbaren Anwendungsanleitungen und konkreten Beispielen für die KI.
- `get_image` liefert echte MCP-Bildinhalte an bildfähige Clients; Ende-zu-Ende-Tests über HTTP und stdio.
- `list_notetypes` zeigt Feldnamen und den nativen Bildverdeckungsstatus; kompatible Klone mit umbenannten deutschen Feldern sind geprüft.
- `preview_notes` rendert Karten vor dem Speichern, einschließlich Cloze-Ordinals und Duplikatwarnungen.
- `audit_notes` prüft technische Vollständigkeit, Pflicht-/Quellenfelder und lokale Medien ohne Änderungen.
- Neuer Reiter **KI-Funktionen** in der eingebauten Hilfe. Keine automatische medizinische Prüfung und keine pauschale Unterstützung fremder Maskeneditoren.

## 0.2.0

- Offline-Anleitung direkt in Anki: **Werkzeuge → Anki MCP – Einrichtung & Hilfe**, mit Fokus auf die KI-Verbindung unter Windows und macOS.
- Konkrete Schritte für Claude Desktop, Hinweise für Cursor/Codex sowie Grenzen der lokalen ChatGPT-Anbindung.
- Kopierbare Client-Konfiguration mit tatsächlichem Port und Dateipfaden, Python-Dateiauswahl und lesender MCP-Verbindungsprüfung.
- Die standalone stdio-Bridge wird im Add-on mitgeliefert; UTF-8-Ausgabe unabhängig von Windows-Pipe-Kodierungen.
- Tests der installierten Bridge aus Verzeichnissen mit Leerzeichen und der tatsächlichen Qt-Einrichtung; vorbereitete CI-Matrix für Windows und Mac (Apple Silicon/Intel). Native Tests auf diesen Systemen stehen noch aus.

## 0.1.0

Erste Version mit 61 MCP-Werkzeugen für bestehende und neue Anki-Sammlungen, native Deck-Einstellungen und FSRS, Lernstände und Statistiken, rich HTML/Cloze-Notizen, native Image Occlusion, Bilder/Audio/Video, Tags, Notiztypen, Lernplanung, echte Wiederholungen, Backups und Paketimport/-export.

Enthält authentifizierten Loopback-Server, Python-stdio-Bridge, Profil-Lebenszyklus, Hauptthread-Dispatch, Undo-Gruppierung, deutsche Dokumentation, reproduzierbaren Add-on-Build und Integrationsprüfungen mit echten Anki-Sammlungen und offiziellen MCP-Clients.

Bekannte Grenzen: kein Login/Sync oder Profilmanagement, keine Medienerzeugung/OCR; lange native Operationen können die GUI blockieren. Noch keine manuelle Endabnahme mit einer persönlichen Sammlung. Siehe README und Architektur-Dokumentation.
