Erste Vorabversion des nativen Anki-MCP-Add-ons mit **61 Werkzeugen** für Decks, Karten, Notizen, Tags, Medien, Bildverdeckung, Lernstände und vollständige native Deck-Optionsvorlagen inklusive FSRS.

**Installation:** `anki-mcp-0.1.0.ankiaddon` herunterladen, in Anki über **Werkzeuge → Erweiterungen → Aus Datei installieren…** installieren und Anki neu starten. Verbindungsdaten: **Werkzeuge → Anki MCP – Verbindung**.

**MCP-Verbindung:** Direktes lokales Streamable HTTP mit Bearer-Token oder `anki_mcp_bridge.py` mit Python 3.10+. Die Bridge ist ebenfalls als Release-Datei beigefügt. Einrichtung und Beispiele stehen in der README.

**Geprüft:** 40 automatisierte Tests je Anki-Version (25.09.5 und 26.09.3), darunter echte Sammlungen, Medien, Bildverdeckung, FSRS/Deck-Optionen, Lernantworten, APKG-Austausch, Qt-Hauptthread/Profilende sowie offizieller MCP-Client über HTTP und stdio.

Diese Version wurde noch nicht manuell mit deiner persönlichen Sammlung und deinem Desktop-Client abgenommen. Funktionsumfang und bekannte Grenzen stehen in der README. Größere Änderungen zuerst an einer Kopie prüfen; native Backups enthalten keine Medien.
