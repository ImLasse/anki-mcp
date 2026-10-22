- `enabled`: Lokalen MCP-Server beim Öffnen des Profils starten.
- `port`: Port auf `127.0.0.1` (Standard: `8766`). Neustart des Profils erforderlich.
- `token`: Wird beim ersten Start automatisch erzeugt. Leer setzen und Profil neu öffnen, um den Token zu erneuern. Niemals veröffentlichen.
- `read_only`: Bei `true` werden schreibende Werkzeuge gesperrt.

Verbindungsdaten: **Werkzeuge → Anki MCP – Verbindung**. Der Server akzeptiert ausschließlich lokale, authentifizierte Verbindungen. Die Python-stdio-Bridge liegt im Repository unter `scripts/anki_mcp_bridge.py`.
