Anki MCP **0.4.0** erweitert die vorhandene Basis und die Windows-/Mac-Einrichtungsanleitung. **80 MCP-Werkzeuge** für Sammlung, Medien und Lernen.

- Gespeicherte Vorher-/Nachher-Pläne für Änderungen an bestehenden Notizen, Tags, Karten und Deck-Einstellungen; Ablauf nach 24 Stunden und Prüfung auf inzwischen veränderte Ziele.
- Dauerhaftes lokales Änderungsprotokoll mit begrenzten Zustandsdaten, auch direkt in Anki lesbar.
- Lokale Textähnlichkeit als Kandidatensuche zur anschließenden fachlichen Prüfung.
- Prüfungsplanung mit Tages-/Wochenbudget, Themenzählungen, vorhandenen Fälligkeiten und sichtbarer Überlastung.
- Strukturierte Quellen, Revisionen, verknüpfte Notizen und Prüfbedarf nach Änderungen; Export/Import der lokalen Quellen- und Prüfungsmetadaten.
- Separates Claude-Desktop-MCPB-Paket, ohne zusätzliche Python-Installation; die bisherigen Claude-/Codex-/ChatGPT-Anleitungen bleiben im Add-on.
- [AnkiWeb-Veröffentlichung und Umstellung](https://github.com/ImLasse/anki-mcp/blob/main/docs/ankiweb.md) einschließlich vorbereiteter Beschreibung dokumentiert.

**Installation/Update unter Windows und macOS:** `anki-mcp-0.4.0.ankiaddon` herunterladen, in Anki über **Werkzeuge → Erweiterungen → Aus Datei installieren…** installieren und Anki sowie KI-Client vollständig neu starten. Alte Version nicht vorher löschen. Paket-ID `anki_mcp` und lokale Laufzeitdaten bleiben erhalten. Die zusätzliche `anki-mcp-claude-0.4.0.mcpb` gehört in Claude Desktop, nicht in Anki.

**Prüfung:** Echte temporäre Anki-Sammlungen, Qt-Dialoge und offizieller MCP-Client; aktuelle Plattform-Ergebnisse unter [Actions](https://github.com/ImLasse/anki-mcp/actions). Die Basisversion 0.3.0 hat die Matrix für Windows, Linux sowie macOS Apple Silicon/Intel bestanden. Der Nutzer berichtet erfolgreiche Nutzung auf Windows und macOS.

**Grenzen:** Die neuen Funktionen sind keine medizinische Prüfung. Textähnlichkeit beweist keine inhaltliche Gleichwertigkeit; Prüfungsbudgets prognostizieren keine zukünftigen Antwortfolgen oder zusätzlichen Wiederholungen. Quellenverknüpfungen, Prüfungspläne und Journal werden nicht von Anki synchronisiert. Metadatenexport und lokale Sicherung sind erklärt. Mehrere Änderungen können bei einem Fehler Teilwirkungen hinterlassen. ChatGPT benötigt weiterhin die zusätzliche Tunnel-/Kontoeinrichtung. Das Claude-Paket ist mit dem offiziellen MCP-Client geprüft, aber nicht im vollständigen Claude-Desktop-Fenster abgenommen. Die AnkiWeb-Veröffentlichung selbst erfolgt separat über das AnkiWeb-Konto.
