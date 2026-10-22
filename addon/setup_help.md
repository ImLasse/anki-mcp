# Anki MCP einrichten

Mit diesem Add-on kann ein KI-Assistent deine geöffnete Anki-Sammlung lesen und bearbeiten. Anki muss während der Verbindung laufen und das gewünschte Profil geöffnet sein.

## 1. Add-on installieren

1. Die Datei mit der Endung `.ankiaddon` herunterladen. Manche Browser hängen `.zip` an: Die Datei nicht entpacken, sondern mit ihrer ursprünglichen Endung `.ankiaddon` verwenden.
2. In Anki **Werkzeuge → Erweiterungen → Aus Datei installieren…** wählen.
3. Die Datei auswählen und Anki vollständig beenden und neu starten. Auf dem Mac über **Anki → Anki beenden** oder **⌘Q**; das Schließen des Fensters allein reicht nicht immer.
4. Dein Lernprofil öffnen. Anschließend **Werkzeuge → Anki MCP – Einrichtung & Hilfe** aufrufen.

Voraussetzung ist Anki Desktop ab **25.09.5**. Dieses Add-on wird auf macOS, Windows und Linux ausgerichtet. Anki auf iPhone/iPad und AnkiDroid können keine Desktop-Add-ons laden.

## 2. Verbindungsart auswählen

Öffne hier den Reiter **Verbindung**. Wähle die Variante, die dein KI-Client unterstützt. Die angezeigten Dateipfade und der Port stammen direkt aus deiner Installation.

### Streamable HTTP

Wenn dein Client lokale Streamable-HTTP-Server mit eigenen Headern unterstützt, nutze die angezeigte HTTP-Konfiguration. Dafür ist keine zusätzliche Python-Installation nötig.

- Adresse: `http://127.0.0.1:8766/mcp`, sofern du den Port nicht geändert hast.
- Anmeldung: Header `Authorization` mit dem angezeigten `Bearer`-Token.
- Einige Clients erwarten zusätzlich `type: "http"` oder ein anderes Dateiformat. Die angezeigte JSON-Struktur ist ein Konfigurationsbeispiel, kein für alle Clients einheitliches Format.
- Ein reiner Cloud-Dienst kann deinen lokalen Server nicht direkt erreichen. Verwende einen lokalen MCP-fähigen Client bzw. eine unterstützte lokale Verbindung.

### stdio, zum Beispiel Claude Desktop

Die Datei `bridge.py` wird mit diesem Add-on installiert. Du musst das Repository nicht separat herunterladen. Der Reiter **Verbindung** erzeugt eine passende Konfiguration mit dem Pfad zur Bridge und zur Token-Datei.

1. Installiere bei Bedarf **Python 3.10 oder neuer** zusätzlich zu Anki. Für HTTP benötigst du diesen Schritt nicht.
2. Trage den **absoluten Pfad zur Python-Datei** in das Python-Feld ein oder wähle sie mit **Auswählen…**. Ankis eigener Programmstarter ist kein Ersatz dafür.
3. Wähle **stdio** und kopiere die erzeugte Konfiguration in die MCP-Einstellungen deines Clients.
4. Existieren dort bereits andere Server, füge nur den Eintrag `anki` unter `mcpServers` hinzu. Die vorhandene Konfiguration nicht vollständig überschreiben.
5. Beende den KI-Client vollständig und starte ihn neu. Ein erneutes Öffnen des Chatfensters reicht je nach Client nicht aus.

## 3. Die KI verbinden: konkrete Schritte

### Claude Desktop mit Erweiterungsdatei: Windows und macOS

Dieser Weg benötigt keine separate Python-Installation. Du brauchst eine aktuelle Claude-Desktop-Version mit Unterstützung für lokale MCPB-Erweiterungen. Der tatsächliche Menüname kann je nach Version variieren.

1. Das Anki-Add-on wie oben installieren und das gewünschte Profil geöffnet lassen.
2. Unter [GitHub Releases](https://github.com/ImLasse/anki-mcp/releases/tag/v0.4.0) zusätzlich **anki-mcp-claude-0.4.0.mcpb** herunterladen. Diese Datei gehört in Claude Desktop, die `.ankiaddon`-Datei gehört in Anki.
3. In Claude **Einstellungen → Erweiterungen** öffnen und die lokale Erweiterungsdatei installieren, je nach Version unter **Erweiterte Einstellungen → Erweiterung installieren**. Falls `.mcpb` per Doppelklick geöffnet wird, kannst du auch diesen Weg verwenden. Den angezeigten Zugriff auf deine Anki-Sammlung prüfen.
4. In Anki **Verbindung → Claude Desktop – Erweiterungsdatei (.mcpb)** auswählen. Der Dialog zeigt den tatsächlichen Pfad zur **Token-Datei** und den Port.
5. Im Claude-Erweiterungsdialog diese Datei auswählen und den Port übernehmen, standardmäßig **8766**. Die Datei heißt `token` ohne Endung und liegt im Add-on-Unterordner `user_files`. Den angezeigten tatsächlichen Pfad verwenden, damit auch Leerzeichen und AnkiWeb-Installationen stimmen.
6. Erweiterung aktivieren, Claude bei Bedarf vollständig neu starten und fragen: **„Lies meine Decknamen und ändere nichts.“**

Das Paket verwendet eine lokale Node-Bridge ohne zusätzliche npm-Pakete; Claude Desktop stellt für Node-Erweiterungen seine Laufzeit bereit. Es verbindet sich ausschließlich mit Anki auf diesem Rechner. Ohne Unterstützung lokaler Erweiterungen kannst du die nachfolgende manuelle stdio-Einrichtung verwenden. Das Paket wurde mit dem offiziellen MCP-Client getestet; die Installation im vollständigen Claude-Desktop-Fenster muss für deine jeweilige App-Version geprüft werden. Es ist nicht als geprüftes Verzeichnis-Listing veröffentlicht.

Für **Codex** bleibt die kopierbare TOML-Konfiguration weiter unten verfügbar. **ChatGPT** verwendet weiterhin die gesondert erklärte Tunnel-Verbindung; die Claude-Datei ist dafür nicht geeignet.

### Claude Desktop auf Windows

1. Installiere **Claude Desktop** und öffne darin **Einstellungen → Entwickler**. Je nach App-Version heißen die Menüpunkte leicht anders; gesucht ist die MCP-Server-Konfiguration.
2. Wähle **Konfiguration bearbeiten**. Die Datei heißt normalerweise `claude_desktop_config.json` und liegt unter `%APPDATA%\Claude\`. Du kannst diesen Ordner im Windows-Explorer in die Adresszeile eingeben. Falls der Client einen anderen Speicherort öffnet, verwende diesen.
3. In Anki hier den Reiter **Verbindung** öffnen und **stdio** auswählen.
4. Falls kein Python gefunden wurde: Python 3.10 oder neuer von python.org installieren. Ein typischer Interpreter-Pfad ist `C:\Users\DEINNAME\AppData\Local\Programs\Python\Python312\python.exe`. Wähle deine tatsächliche `python.exe` mit **Auswählen…**. Ein WindowsApps-Store-Platzhalter ist kein geeigneter Interpreter.
5. **Konfiguration kopieren** anklicken. Den `anki`-Eintrag in der Client-Datei unter `mcpServers` ergänzen. Wenn noch keine Server eingerichtet sind, kann die vollständige erzeugte JSON-Konfiguration verwendet werden. Die Datei muss gültiges JSON enthalten, ohne Kommentare oder Markdown-Codezäune.
6. Claude über sein Menü bzw. das Symbol im Infobereich vollständig beenden und neu starten. Anki mit geöffnetem Profil laufen lassen.
7. In Claude prüfen, ob die Anki-Werkzeuge angeboten werden. Frage: **„Lies meine Decknamen und ändere nichts.“** Gegebenenfalls die vom Client angefragte Werkzeugnutzung erlauben.

**Leerzeichen und Backslashes:** Die Kopierfunktion erzeugt korrekt maskiertes JSON. Ein Pfad wie `C:\Users\Dein Name\…` bleibt genau ein Argument. Keine zusätzlichen Anführungszeichen in das Python-Feld schreiben. Die von Anki verwendete Token-Datei muss nicht manuell geöffnet oder kopiert werden.

### Claude Desktop auf macOS

1. Claude Desktop öffnen und **Einstellungen → Entwickler → Konfiguration bearbeiten** wählen. Normalerweise liegt die Datei unter `~/Library/Application Support/Claude/claude_desktop_config.json`.
2. Im Finder kannst du mit **⌘⇧G** den Ordner `~/Library/Application Support/Claude/` öffnen, falls du die Datei manuell suchen musst.
3. In Anki den Reiter **Verbindung**, **stdio** und den tatsächlichen absoluten Python-Pfad wählen. Unten stehen die typischen Mac-Pfade.
4. Den erzeugten `anki`-Eintrag unter `mcpServers` in der Client-Konfiguration ergänzen und speichern. Die übrigen Server behalten.
5. Claude mit **⌘Q** vollständig beenden und neu starten. Anki mit geöffnetem Profil laufen lassen.
6. Die Anki-Werkzeuge im Client prüfen und **„Lies meine Decknamen und ändere nichts.“** testen.

### Codex, Cursor und andere lokale MCP-Clients

Wähle für Codex im Verbindungsreiter **Codex – lokale stdio-Verbindung (TOML)**. Die Kopierfunktion liefert dafür direkt einen fertigen TOML-Abschnitt mit deinen Pfaden.

Diese Clients haben eigene Konfigurationsformate. Für **Cursor** lässt sich üblicherweise die erzeugte stdio-JSON-Konfiguration in einer globalen `mcp.json` oder über die MCP-Einstellungen übernehmen. Den aktuell vom Client angezeigten Speicherort verwenden; projektbezogene Konfigurationen nur in vertrauenswürdigen Projekten verwenden.

**Codex** verwendet TOML. In den Einstellungen die Benutzerdatei `~/.codex/config.toml` öffnen; unter Windows entspricht das normalerweise `%USERPROFILE%\.codex\config.toml`. Beispiel:

```toml
[mcp_servers.anki]
command = "/ABSOLUTER/PFAD/ZU/python3"
args = ["/ABSOLUTER/PFAD/ZUM/ADDON/bridge.py", "--url", "http://127.0.0.1:8766/mcp", "--token-file", "/ABSOLUTER/PFAD/ZUM/ADDON/user_files/token"]
```

Die tatsächlichen Pfade aus Ankis Verbindungsreiter übernehmen. In TOML auf Windows entweder Backslashes doppelt schreiben oder einfache Literal-Zeichenketten wie `'C:\Users\Dein Name\…\python.exe'` nutzen. Anschließend Codex neu starten und seine MCP-Server bzw. Werkzeuge prüfen. Für Codex die oben genannte TOML-Auswahl verwenden. Über `codex mcp list` und im laufenden Codex über `/mcp` den Status prüfen. Windows-Codex dabei nativ auf demselben Windows wie Anki betreiben: WSL und Cloud-Umgebungen haben andere Pfade und ein eigenes `localhost`. [Offizielle Codex-MCP-Dokumentation](https://developers.openai.com/codex/mcp).

### ChatGPT im Browser oder als App

Für ChatGPT gibt es einen zusätzlichen Verbindungsweg: **OpenAI Secure MCP Tunnel**. ChatGPT kann nicht direkt `127.0.0.1` erreichen. Der Tunnel verbindet den lokalen Server ausgehend mit OpenAI; Anki bleibt auf Loopback. Verfügbarkeit von Werkzeugen und Schreibaktionen hängt von Tarif und Workspace-Rechten ab. Die Einrichtung wurde hier noch nicht mit einem persönlichen ChatGPT-Konto geprüft.

1. In [OpenAI Platform → Tunnels](https://platform.openai.com/settings/organization/tunnels) einen passenden Tunnel einrichten und dem Ziel-ChatGPT-Workspace zuordnen. Dafür sind Tunnel-Verwaltungsrechte notwendig; der laufende Client benötigt Read/Use und einen passenden Runtime-API-Key.
2. Den offiziellen [tunnel-client](https://github.com/openai/tunnel-client/releases/latest) für dein System herunterladen: Windows bzw. macOS, jeweils Intel/AMD64 oder ARM64 passend zum Rechner. Die aktuelle Hilfe `tunnel-client help quickstart` beachten.
3. Hier **Verbindung → ChatGPT – Secure MCP Tunnel** wählen, die Tunnel-ID eintragen und die erzeugte YAML-Konfiguration lokal als `anki-tunnel.yaml` speichern. Sie enthält den Anki-Token; den OpenAI-Key enthält sie nicht.
4. Den Runtime-Key nur lokal in der Umgebung des Tunnelclients als `CONTROL_PLANE_API_KEY` bereitstellen. Beispiele zur verdeckten Eingabe stehen unten.
5. `tunnel-client doctor --config PFAD_ZUR_YAML --explain` ausführen, danach `tunnel-client run --config PFAD_ZUR_YAML`. Anki und Tunnelclient laufen lassen.
6. In ChatGPT unter **Plugins → + → Add custom MCP server** als Verbindung **Tunnel** wählen und die passende ID auswählen. Anmeldung, Rechte und Werkzeugerkennung abschließen. Bei älteren Oberflächen können die Einstellungen unter Apps liegen.
7. In einem neuen Chat das Plugin auswählen und zuerst **„Lies meine Decknamen und ändere nichts.“** testen. Erst ein erfolgreicher Werkzeugaufruf aus ChatGPT bestätigt diese Verbindung.

Offizielle Anleitungen: [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) und [MCP-Server in ChatGPT verbinden](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt). Fehlen die nötigen Kontorechte, kann das Add-on sie nicht ersetzen.

**macOS-Terminal:** Die Pfade an deine Dateien anpassen. Nach `read` den Runtime-Key eingeben und Enter drücken; die Eingabe wird nicht angezeigt.

```sh
read -r -s CONTROL_PLANE_API_KEY
export CONTROL_PLANE_API_KEY
./tunnel-client doctor --config "/Users/DEINNAME/anki-tunnel.yaml" --explain
./tunnel-client run --config "/Users/DEINNAME/anki-tunnel.yaml"
```

**Windows PowerShell:** Nach der ersten Zeile den Runtime-Key verdeckt eingeben. Die Befehle im Ordner des heruntergeladenen Tunnelclients ausführen und den YAML-Pfad anpassen.

```powershell
$ankiTunnelKey = Read-Host 'OpenAI Runtime API-Key' -AsSecureString
$env:CONTROL_PLANE_API_KEY = [System.Net.NetworkCredential]::new('', $ankiTunnelKey).Password
.\tunnel-client.exe doctor --config 'C:\Users\DEINNAME\anki-tunnel.yaml' --explain
.\tunnel-client.exe run --config 'C:\Users\DEINNAME\anki-tunnel.yaml'
```

Die YAML ist ein vorbereitetes Profil für den separaten offiziellen Tunnelclient. Der Anki-Verbindungstest prüft diesen Tunnel nicht. Die vollständige ChatGPT-Einrichtung muss mit deinem berechtigten Konto erfolgen. Bei einer Token-Erneuerung die YAML neu aus Anki kopieren. Tunnel-Größen- und Zeitlimits können große Medienübertragungen und lange Operationen zusätzlich begrenzen.

## 4. Hinweise speziell für macOS

Das Add-on enthält keine eigenen kompilierten Erweiterungen. Anki stellt die passende Python-/Qt-Umgebung bereit. Ziel sind sowohl **Apple Silicon (M1/M2/M3/M4 und neuer)** als auch **Intel-Macs**, soweit die verwendete Anki-Version dein macOS unterstützt. Ein grüner Test auf einem Mac ist von einer bloßen technischen Kompatibilitätsprüfung zu unterscheiden: Die vorbereitete macOS-Testmatrix muss vor einer bestätigten Mac-Freigabe auf GitHub laufen.

### Python auswählen

Bei über Finder gestarteten Apps ist der Suchpfad häufig anders als im Terminal. Verwende daher in der MCP-Konfiguration einen absoluten Pfad. Typische Installationen:

- Apple Silicon mit Homebrew: `/opt/homebrew/bin/python3`
- Intel mit Homebrew: `/usr/local/bin/python3`
- Python von python.org: beispielsweise `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`

Das sind Beispiele; entscheidend ist deine tatsächliche Installation. Die automatische Auswahl sucht nach vorhandenen Dateien und garantiert nicht die Python-Version. Prüfe sie im Terminal mit dem ausgewählten Pfad und `--version`. Es muss **3.10 oder neuer** sein. `/usr/bin/python3` wird auf Macs nicht automatisch gewählt, weil darüber gegebenenfalls Entwicklerwerkzeuge nachinstalliert werden oder eine ältere Version bereitsteht.

### Pfade mit Leerzeichen

Anki speichert Add-ons normalerweise unter `~/Library/Application Support/Anki2/addons21/`. Der Reiter **Verbindung** zeigt deinen tatsächlichen, vollständig aufgelösten Pfad an. Innerhalb eines JSON-`args`-Arrays bleibt ein Pfad mit Leerzeichen genau **ein** Eintrag. Keine zusätzlichen Anführungszeichen in den Pfad schreiben und dort keine Shell-Escapes wie `\ ` verwenden.

Bei Claude Desktop liegt die Konfiguration üblicherweise unter `~/Library/Application Support/Claude/claude_desktop_config.json`. Öffne nach Möglichkeit die MCP-/Entwicklereinstellungen des Clients, um den gültigen Speicherort deiner Version zu finden. `~` wird in Programmargumenten nicht zuverlässig aufgelöst: Für Bridge und Token immer die absoluten Pfade aus Anki verwenden.

## 5. Verbindung prüfen

Klicke im Reiter **Verbindung** auf **Verbindung prüfen**. Der Test prüft den lokalen Server, die Anmeldung, die MCP-Initialisierung, die angebotenen Werkzeuge und den Zugriff auf das geöffnete Profil. Er erzeugt oder verändert keine Karten. Er prüft nicht, ob dein KI-Client seine Konfiguration bereits übernommen hat oder ob der gewählte Python-Interpreter korrekt installiert ist.

Bitte deinen KI-Assistenten danach: **„Lies meine Decknamen und meinen Lernstand. Ändere noch nichts.“** Wenn Decks und Lernzahlen erscheinen, funktioniert auch die Verbindung vom Client aus.

Danach kannst du zum Beispiel fragen:

- „Zeige mir fällige Kardiologie-Karten und Karten mit vielen Fehlversuchen.“
- „Erstelle fünf Cloze-Notizen mit meinen Quellen und dem Tag Medizin::Anatomie.“
- „Erkläre mir die FSRS-Einstellungen dieses Decks.“
- „Erstelle aus meinem Anatomiebild native Bildverdeckungskarten.“

Die KI braucht für Medien eigene Datei-/Bildwerkzeuge oder die von dir übergebenen Medienbytes. Das Add-on stellt Anki-Funktionen bereit; es erzeugt selbst keine Bilder oder Audiodateien.

## Fehler beheben

### Der Server ist gestoppt

Ein Profil öffnen. Unter **Werkzeuge → Erweiterungen → Anki MCP → Konfiguration** muss `enabled` auf `true` stehen. Nach Änderungen das Profil schließen und erneut öffnen oder Anki neu starten.

### Der Port ist bereits belegt

In der Add-on-Konfiguration einen anderen Port setzen, etwa `8767`, und Anki neu starten. Danach die Client-Konfiguration aus dem Reiter **Verbindung** erneut kopieren. Mehrere Anki-Instanzen benötigen unterschiedliche Ports.

### 401 – Anmeldung fehlgeschlagen

Die Client-Konfiguration erneut aus Anki kopieren. Nach einer Token-Erneuerung muss die HTTP-Konfiguration aktualisiert werden. Die stdio-Bridge liest den Token bei jedem Start aus der angegebenen Datei; den KI-Client neu starten.

### Python oder Bridge wird nicht gefunden

Prüfe den absoluten Python-Pfad und die angezeigte Version. Der Pfad zur Bridge muss auf `bridge.py` im installierten Add-on zeigen, nicht auf die `.ankiaddon`-Datei. Pfade exakt als einzelne JSON-Argumente übernehmen. Unter Windows Backslashes in JSON doppelt schreiben; „Konfiguration kopieren“ übernimmt das automatisch.

### Anki ist beschäftigt

Eine laufende Synchronisation, ein Export oder ein anderer Dialog kann Sammlungsoperationen blockieren. Den Vorgang abschließen und anschließend erneut versuchen. Für echte MCP-Lernantworten vorher die GUI-Wiederholung verlassen.

### Der KI-Client zeigt keine Werkzeuge

Prüfe die unterstützte Verbindungsart und das Konfigurationsformat des Clients. Den Client vollständig neu starten. „Verbindung prüfen“ bestätigt den Anki-Endpunkt; anschließend muss zusätzlich der Test aus deinem KI-Client funktionieren.

## Änderungen verstehen

Tags gehören zu Notizen; Fälligkeiten, Aussetzungen und Flags gehören zu den daraus erzeugten Karten. Änderungen werden soweit unterstützt über Anki rückgängig gemacht. Medienänderungen und Paketimporte haben kein Sammlungs-Undo. Vor größeren Änderungen ein Backup einschließlich der benötigten Medien anlegen.

Mit `read_only: true` in der Add-on-Konfiguration kannst du schreibende MCP-Werkzeuge sperren. Nach Konfigurationsänderungen Anki neu starten. Verbindungsdaten enthalten einen lokalen Zugangstoken und gehören nur in die Client-Konfiguration, nicht in öffentliche Screenshots oder Repositorys.

## Aktueller Qualitätsstand

Diese Version bietet umfangreiche Sammlungs- und Lernfunktionen. Automatisierte Tests ersetzen keine manuelle Prüfung mit deinem Anki-Profil und deinem KI-Client. Login/Sync, Profilverwaltung, OCR und Medienerzeugung sind nicht Bestandteil dieser Version. Der Nutzer berichtet erfolgreiche Nutzung unter Windows und macOS. Die automatisierte Plattformmatrix für die Basisversion ist erfolgreich; nicht jede Funktion oder Client-Version ist damit manuell abgenommen. Der erste Client-Test sollte deshalb nur Daten lesen.

## Offizielle Client-Dokumentation

- [Lokale MCP-Server in Claude Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop)
- [Codex und MCP](https://developers.openai.com/codex/mcp)
- [ChatGPT-MCP-Verbindungen](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt)

Lokale Claude-Server hier beziehen sich auf die Desktop-Chat-Anbindung. Claude im Browser, Remote-Connectors und Cowork können andere Verbindungswege verwenden. Konten und Organisationen können lokale MCP-Server einschränken.

## Einfach aktualisieren: Windows und macOS

Neue `.ankiaddon` aus dem GitHub-Release herunterladen, in Anki **Werkzeuge → Erweiterungen → Aus Datei installieren…** auswählen und danach Anki sowie den KI-Client vollständig neu starten. Alte Version vorher nicht löschen; `user_files` mit Token und lokalen Metadaten bleibt erhalten. Eine neue Claude-MCPB-Datei bei Bedarf separat in Claude installieren. Codex- und HTTP-Konfigurationen bleiben bei unveränderten Pfaden und Port gültig.

Nach Veröffentlichung auf AnkiWeb kann die per numerischem Code installierte Version über **Werkzeuge → Erweiterungen → Auf Aktualisierungen überprüfen** aktualisiert werden. GitHub allein stellt keine AnkiWeb-Updates bereit. Beim Wechsel von der manuellen Installation zum AnkiWeb-Code entsteht ein anderer Add-on-Ordner: `user_files` zuerst sichern, alte Kopie deaktivieren, nur eine Kopie aktiv lassen und Client-Pfade neu übernehmen. Die vollständige [AnkiWeb-Anleitung](https://github.com/ImLasse/anki-mcp/blob/main/docs/ankiweb.md) erklärt Veröffentlichung und Umstellung.
