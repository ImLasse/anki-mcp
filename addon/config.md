- `enabled`: Lokalen MCP-Server beim Öffnen des Profils starten.
- `port`: Port auf `127.0.0.1` (Standard: `8766`). Neustart des Profils erforderlich.
- `token`: Wird beim ersten Start automatisch erzeugt. Leer setzen und Profil neu öffnen, um den Token zu erneuern. Niemals veröffentlichen.
- `read_only`: Bei `true` werden schreibende Werkzeuge gesperrt.

Schritt-für-Schritt-Anleitung für Windows/macOS und KI-Client-Konfiguration: **Werkzeuge → Anki MCP – Einrichtung & Hilfe**.

Verbindungsdaten: **Werkzeuge → Anki MCP – Verbindung**. Der Server akzeptiert ausschließlich lokale, authentifizierte Verbindungen. Die eigenständig ausführbare Python-stdio-Bridge wird als `bridge.py` direkt mit dem Add-on installiert.
