# Auf AnkiWeb veröffentlichen

Das GitHub-Repository ist https://github.com/ImLasse/anki-mcp. Ein GitHub-Release allein veröffentlicht das Add-on noch nicht auf AnkiWeb. Für den ersten Upload ist dein AnkiWeb-Konto erforderlich; das Projekt enthält keine Zugangsdaten.

## Erster Upload

1. Im [GitHub-Release](https://github.com/ImLasse/anki-mcp/releases/tag/v0.4.0) **anki-mcp-0.4.0.ankiaddon** herunterladen. Alternativ mit `python scripts/build.py` selbst bauen. Nur diese Datei auf AnkiWeb hochladen, weder das Projekt-ZIP noch die Claude-Datei `.mcpb`.
2. Bei [AnkiWeb](https://ankiweb.net/account/login) anmelden und auf der [Add-on-Seite](https://ankiweb.net/shared/addons) **Upload** öffnen.
3. Paket auswählen. Als Titel eignet sich **Anki MCP – AI collection tools**. Die [vorbereitete Beschreibung](ankiweb-description.html) übernehmen; im Upload-Formular auf passende HTML-Darstellung prüfen.
4. Projekt-/Support-Link: `https://github.com/ImLasse/anki-mcp`. Lizenz: **AGPL-3.0-or-later**. Unterstützte Mindestversion: **25.09.5**. Die Maske kann einzelne Angaben anders benennen; keine ältere Mindestversion behaupten.
5. Die Veröffentlichung abschließen und den von AnkiWeb vergebenen **numerischen Add-on-Code** und den Seitenlink notieren. Diesen Code anschließend in README, Anleitung und Release ergänzen. Vorher gibt es keinen installierbaren AnkiWeb-Code.
6. Download mit einem separaten Anki-Testprofil prüfen: Code installieren, Anki neu starten, Einrichtungshilfe öffnen, Verbindung testen und von der KI zunächst nur Decknamen lesen lassen. Windows und macOS prüfen; bestehende persönliche Lernsammlungen dafür nicht verändern.

Das erzeugte Paket enthält die Dateien direkt im ZIP-Wurzelverzeichnis und keinen einschließenden Projektordner. Token, private Sammlungen und Laufzeitdaten werden nicht mitgepackt. Offizielle Referenz zum Paketformat und Upload: [Anki-Handbuch – Sharing Add-ons](https://docs.ankiweb.net/addons/sharing).

## Bestehende Installation auf den AnkiWeb-Code umstellen

Die bisher aus Datei installierte Version heißt intern `anki_mcp`. AnkiWeb installiert unter dem vergebenen numerischen Code. Das sind unterschiedliche Add-on-Ordner. Zwei aktive Kopien würden denselben Port beanspruchen.

1. Vorher in Anki **Werkzeuge → Erweiterungen** das bisherige Anki-MCP-Add-on auswählen und **Dateien anzeigen** öffnen. Den Ordner `user_files` außerhalb des Add-on-Ordners sichern. Er enthält den lokalen Token, Journal, Quellenverknüpfungen, Prüfungspläne und Transferdateien; nicht öffentlich hochladen.
2. Das bisherige Add-on **deaktivieren**, die AnkiWeb-Version per Code installieren und Anki beenden.
3. Im Dateimanager den gesicherten Ordner `user_files` in den neuen numerischen Add-on-Ordner übernehmen. Bestehende Dateien dort vorher ebenfalls sichern. Port und `read_only` aus der bisherigen Konfiguration bei Bedarf in der neuen Add-on-Konfiguration übernehmen. Beim Start schreibt das Add-on den Token aus seiner Konfiguration in `user_files/token`; die neue Installation kann einen neuen Token erhalten.
4. Anki neu starten; nur eine Kopie aktivieren. Verbindung im neuen Dialog erneut kopieren. Bei Claude MCPB den neuen Pfad zur Token-Datei auswählen, bei Python-stdio/Codex den neuen Bridge-Pfad übernehmen. HTTP-Port überprüfen.
5. Journal und Quellen prüfen. Die lokale Metadaten-Datenbank wird anhand des Sammlungspfads zugeordnet. Bei geändertem Profilpfad/Rechner Quellen und Prüfungspläne vorher über `export_workspace` sichern und mit derselben Sammlung über `import_workspace` übernehmen. Das Journal wird dabei nicht importiert; die alte Sicherung aufbewahren.

Lernkarten liegen in Ankis Sammlung und werden durch das Deaktivieren des Add-ons nicht gelöscht. Den alten Add-on-Ordner erst nach erfolgreicher Prüfung entfernen.

## Weitere Updates

Neue Version bauen und auf **derselben AnkiWeb-Add-on-Seite** als Update hochladen. Den vorhandenen Code behalten, keine neue Veröffentlichung pro Version anlegen. Anki-Nutzer können danach **Werkzeuge → Erweiterungen → Auf Aktualisierungen überprüfen** verwenden und Anki neu starten.

Bis zur AnkiWeb-Veröffentlichung läuft das Update per neuer `.ankiaddon`-Datei: **Aus Datei installieren…**, alte Installation nicht vorher löschen, anschließend Anki und KI-Client neu starten. Dieselbe Paket-ID ersetzt den Code und erhält `user_files`. Das Claude-MCPB-Paket ist eine separate lokale Erweiterung und wird bei Bedarf in Claude aktualisiert. Es installiert oder aktualisiert das Anki-Add-on nicht selbst.
