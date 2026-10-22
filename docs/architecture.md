# Architektur, Kompatibilität und Grenzen

## Aufbau

`addon/desktop.py` verbindet Ankis Profil-Hooks mit dem Server und plant jede Sammlungsoperation auf dem Qt-Hauptthread. `server.py` stellt `/mcp` auf `127.0.0.1` bereit. `protocol.py` implementiert JSON-RPC, MCP-Initialisierung, Ping und Werkzeuge. `registry.py` enthält explizite Eingabeschemas und deren Laufzeitprüfung. Die `tools_*.py`-Module verwenden native Anki-APIs. `api.py` kapselt Schreibschutz, Undo, Objektprüfung und die Serialisierung von Protobuf-Ergebnissen.

Das Add-on selbst benötigt ausschließlich Anki und dessen mitgelieferte Python-Bibliotheken. Es öffnet keine zweite Datenbankverbindung zur laufenden Sammlung. Es gibt kein `eval`, kein frei ausführbares Python und keinen SQL-Schreibzugriff. Eine interne, konstante SQL-Leseabfrage ermittelt den Schema-Zeitstempel für die native Notiztypkonvertierung.

Der HTTP-Transport verwendet zustandslose JSON-Antworten ohne SSE-Stream oder Session-ID. `GET` und `DELETE` liefern 405. Unterstützte MCP-Protokollversionen: `2025-11-25`, `2025-06-18`, `2025-03-26` und über die stdio-Bridge auch Clients mit `2024-11-05`. Der HTTP-Transport setzt Streamable-HTTP-Unterstützung im Client voraus. JSON-RPC-Batches werden abgewiesen. Fortschrittsnachrichten, Remote-OAuth, Roots, Sampling und serverseitige Ressourcen sind nicht implementiert.

## Einrichtung und Betriebssysteme

`setup_help.md` ist die offline verfügbare Windows-/macOS-Anleitung. `setup_dialog.py` stellt sie in einem nativen Qt-Dialog dar und bietet JSON-Konfigurationen für Claude/stdio/HTTP, TOML für Codex und YAML-Profile für OpenAI Secure MCP Tunnel aus den tatsächlichen Installationspfaden. `connection.py` sucht nach Python-Dateien, ohne Programme zu starten; die Version muss separat geprüft werden. Unter macOS werden Homebrew-/Framework-Pfade berücksichtigt, unter Windows Standardinstallationen und der Suchpfad; WindowsApps-Aliasse werden nicht automatisch ausgewählt.

Die eigenständig ausführbare `bridge.py` gehört zum Add-on. Sie benötigt außerhalb Ankis Python 3.10+, aber keine Zusatzpakete. `scripts/anki_mcp_bridge.py` ist ein Repository-Einstiegspunkt. Die Bridge erzwingt UTF-8 für MCP-Ausgabe, damit internationale medizinische Texte auch bei abweichender Windows-Pipe-Kodierung funktionieren.

Der Verbindungstest läuft ohne Sammlungszugriff im Anki-Hintergrundthread und ruft anschließend ausschließlich die lesenden MCP-Methoden `initialize`, `tools/list` und `collection_info` auf. Der eigentliche Sammlungszugriff wird wie jeder MCP-Aufruf auf den Hauptthread delegiert. Das Ergebnis enthält Werkzeuganzahl und Sammlungszähler, aber keine Tokens oder Karteninhalte. Der Test kann nicht bestätigen, dass ein externer KI-Client seine Konfigurationsdatei eingelesen hat. Die Bridge bietet denselben Test über `--check`.

Windows- und Mac-Pfade mit Leerzeichen werden als einzelne Argumente in der JSON-Liste erzeugt. Es findet keine Shell-Ausführung statt. Lokale Linux-Tests prüfen die Standalone-Bridge nach Extraktion des Add-ons in einen Pfad mit Leerzeichen. Die GitHub-Matrix für 0.3.0 ist mit Windows, Linux sowie macOS Apple Silicon/Intel erfolgreich durchgelaufen. Der Nutzer berichtet erfolgreiche Nutzung auf Windows und macOS. Vollständige manuelle Client-/Funktionsprüfungen sind dadurch nicht ersetzt.

## Profil und Nebenläufigkeit

Prozessweit läuft ein Server für das aktuell geöffnete Profil. Beim Schließen des Profils werden wartende Befehle storniert und der Server beendet. Eine Profilgeneration verhindert, dass ein bereits eingeplanter Befehl nach einem Profilwechsel ausgeführt wird. Portkonflikte werden in Anki angezeigt. Mehrere gleichzeitig laufende Anki-Instanzen benötigen unterschiedliche Ports.

Bei Hintergrundoperationen oder einem aktiven Fortschrittsdialog werden neue Sammlungsbefehle abgewiesen. Befehle, die 30 Sekunden lang nicht gestartet werden konnten, werden storniert. Bereits gestartete Schreiboperationen erhalten keinen falschen Timeout-Befund; ein Verbindungsabbruch kann ihren Ausgang dennoch unklar lassen. Vor einem erneuten Schreibversuch die Sammlung abfragen.

Lange native Exporte, Medienprüfungen, Statistiken und FSRS-Berechnungen laufen ebenfalls auf dem Hauptthread und können die GUI vorübergehend blockieren. Dies ist eine bekannte Einschränkung. Bei geöffneter GUI-Wiederholung werden MCP-Lernantworten abgewiesen, damit keine veraltete Reviewer-Karte beantwortet wird.

## Rückgängig und Fehler

Schreibende Sammlungswerkzeuge erzeugen einen benannten Undo-Eintrag. Dabei werden mehrere native Teiloperationen zusammengefasst. Medien, Dateitransfers, Importe, Exporte und Backups sind davon ausgenommen. `undo` betrifft die letzte Anki-Operation, auch wenn sie manuell durchgeführt wurde.

Batches werden soweit möglich vorab validiert. Ein Werkzeugaufruf ist **keine allgemeine Transaktion über alle Anki- und Dateisystemoperationen**. Bei Fehlern können einzelne Schritte bereits erfolgt sein. Der Client muss den Zustand vor Wiederholung prüfen; Sammlungsänderungen lassen sich gegebenenfalls über Undo zurücknehmen. Medienpapierkorb und Staging-Dateien haben eigene Werkzeuge.

## Einheiten und Datenformate

- Karten-/Notiz-/Deck-IDs im JSON-Eingang sind positive Ganzzahlen. Native Protobuf-Ergebnisse stellen 64-Bit-Ganzzahlen gemäß Protobuf-JSON oft als Zeichenketten dar. Vor erneuter Übergabe entsprechend konvertieren.
- `get_cards.nid` ist die Notiz-ID, `did` die Deck-ID und `ord` der **nullbasierte** Kartenordinal. Cloze-/Masken-Markup verwendet **einsbasierte** Nummern.
- `queue`: -1 ausgesetzt, -2 automatisch vergraben, -3 manuell vergraben, 0 neu, 1 Lernen, 2 Wiederholung, 3 tagesübergreifendes Lernen. Weitere native Sonderfälle bleiben unverändert.
- `due`: bei neuen Karten die Position; bei kurzfristigem Lernen Unix-Sekunden; bei Wiederholung/tagesübergreifendem Lernen Tage relativ zu Ankis internem Sammlungsstart. Deshalb `scheduler_day` und native Statistikdaten zur Interpretation nutzen.
- `ivl`: Tage; `factor`: SM-2-Leichtigkeitsfaktor ×1000; FSRS-Werte stehen zusätzlich unter `memory_state` und in `card_statistics`.
- `learn_steps` und `relearn_steps`: Minuten; Behaltensquoten: 0 bis 1. Wiederholungszeiten und Ratings sind im jeweiligen nativen Statistikformat angegeben. `answer_card.milliseconds_taken` ist ausdrücklich in Millisekunden.
- HTML, MathJax, LaTeX-Markup, Bild- und `[sound:...]`-Referenzen werden als Feldinhalt gespeichert. Anki übernimmt Darstellung und native Kartengenerierung.
- Die Lernübersicht enthält teilweise überlappende Zählungen. Die Vorschau schätzt bereits terminierte Wiederholungskarten, nicht die zukünftigen Folgen weiterer Lernantworten.

## Medien und Dateien

Medienwerkzeuge akzeptieren ausschließlich Dateinamen innerhalb von Ankis Medienordner. Verzeichnispfade, Symlinks und Pfadtraversierung werden abgewiesen. Dateinamenskollisionen behandelt Ankis Medien-API; Clients müssen den zurückgegebenen Namen übernehmen. Medien sind auf 20 MiB je Upload begrenzt; Lesen erfolgt in Chunks bis 4 MiB.

Paketdateien liegen ausschließlich in `user_files/transfers`. Uploads können in Chunks bis 20 MiB angehängt werden; die Gesamtgrenze beträgt 512 MiB. Bestehende Dateien werden nicht still überschrieben. Der Client muss sie ausdrücklich löschen oder einen neuen Namen wählen. Paketexporte können größere Dateien erzeugen, die über Chunks heruntergeladen werden. `.colpkg`-Wiederherstellung ist nicht implementiert, weil sie das aktive Profil ersetzt.

Das Add-on bindet ausschließlich Loopback, prüft Bearer-Token, Host und Origin und sendet keine CORS-Freigaben. Maximal acht HTTP-Anfragen laufen gleichzeitig; Bodies sind auf 32 MiB begrenzt. Der Token wird lokal generiert und zusätzlich in `user_files/token` abgelegt. Unter POSIX erhält diese Datei Modus 0600. Unter Windows gelten zusätzlich die Dateisystemberechtigungen des Benutzerprofils. Die Bridge deaktiviert Proxys für lokale Aufrufe und folgt keinen Redirects.

`read_only` sperrt alle als schreibend registrierten Werkzeuge. Auch `transfer_file` (enthält Upload/Delete), Export und Backup sind dann gesperrt. Das Add-on enthält keine allgemeine Netzwerk-Downloadfunktion; ein Client lädt Medien herunter und übergibt deren Bytes.

## Kompatibilität und Prüfung

Anki 25.09.5 und 26.09.3 werden mit echten temporären Sammlungen geprüft. MCP-Tests verwenden den offiziellen Python-Client über Streamable HTTP und über einen separat gestarteten stdio-Bridge-Prozess. Der Qt-Test verwendet den echten Anki-TaskManager mit Qt-Ereignisschleife und einem kleinen Fensteradapter; er prüft Dispatch, Busy-Sperre und Stornierung bei Profilende. Er ersetzt keine manuelle Installation und Endabnahme im vollständigen Anki-Fenster.

`learning_statistics` und `fsrs_parameters` verwenden native Backend-Methoden, die Anki über `_backend` bereitstellt; diese können sich mit künftigen Versionen ändern. Einstellungen und Schemas werden aus den Protobuf-Deskriptoren der laufenden Anki-Version gelesen. Drittanbieter-Notiztypen lassen sich als normale Notiztypen bearbeiten; eigene Logik anderer Add-ons wird nicht automatisch zu MCP-Werkzeugen.

Der Funktionsumfang konzentriert sich auf Sammlung, Medien und Lernen. Login, Synchronisation, Profilwechsel, Einstellungen anderer Add-ons, Audioaufnahme und Medienerzeugung sind nicht Teil dieser Version. Ein KI-Client kann zusätzliche Werkzeuge für Recherche und Medienerzeugung kombinieren. Medizinische Aussagen und Quellen werden vom Nutzer bzw. KI-Client geliefert; dieses Add-on überprüft deren fachliche Richtigkeit nicht.

## ChatGPT-Tunnel-Profil

Die generierte YAML verwendet einen HTTP-MCP-Kanal zum lokalen Anki-Endpunkt mit lokalen Anki-Bearer-Headern für Runtime und Discovery. Der OpenAI-Runtime-Key wird ausschließlich als `env:CONTROL_PLANE_API_KEY` referenziert. Der Tunnelclient gehört nicht zum Add-on; Installation, Tunnel-Provisionierung und Kontoberechtigungen sind separate Einrichtungsschritte. Die YAML wird nur angezeigt und kopiert. Das Add-on startet keinen Tunnel und veröffentlicht keinen Endpunkt. Die Profilstruktur folgt der offiziellen Konfigurationsreferenz; ein echter Tunnel wurde mangels Konto-/Tunnel-Zugang noch nicht getestet.

Quellen: [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels), [Tunnelclient-Konfiguration](https://github.com/openai/tunnel-client/blob/master/docs/configuration.md).

## KI-Anleitungen, Bilder, Vorschau und Qualitätsprüfung ab 0.3.0

`ai_guide.json` enthält gebündelte Anwendungsanleitungen, abrufbar über `usage_guide`. Die Initialisierungsanweisungen verweisen bei komplexen Aufgaben darauf. Ob ein Client diese Hinweise vollständig berücksichtigt, hängt vom Modell und Client ab. Dies ist keine feinabgestimmte oder trainierte Anki-KI.

`get_image` liest ausschließlich Medien aus der Sammlung (PNG/JPEG/GIF/WebP, maximal 4 MiB), erkennt den MIME-Typ am Dateikopf und gibt einen typisierten MCP-ImageContent-Block zurück. `ContentResult` ist eine interne Rückgabeklasse; normale Notizdaten können nicht versehentlich als MCP-Bildantwort interpretiert werden. Der Client muss die Bildausgabe und Bildverarbeitung unterstützen. Es werden keine Masken automatisch durch das Add-on erkannt.

`preview_notes` verwendet Ankis nativen Card-Layout-Renderer, ohne Notizen oder Karten zu speichern. Es zeigt alle Standardvorlagen bzw. die nativen Cloze-Ordinals; die tatsächliche Erzeugung kann bedingte leere Vorlagen auslassen. Der Renderer kann dynamische Spezialfelder als Platzhalter ausgeben. Anki-Render-Hooks einschließlich anderer Add-ons bleiben aktiv; deren Nebenwirkungen bzw. mögliche LaTeX-Mediencaches fallen nicht unter die Aussage, dass keine Karten gespeichert werden.

`audit_notes` prüft HTML-Inhalte und lokale Medienreferenzen seitenweise. Es führt keine externen Downloads und keine LaTeX-Kompilierung aus. Es unterscheidet leere optionale Felder von ausdrücklich verlangten Pflichtfeldern. Das Fehlen eines Pflichtfelds im Modell wird separat gemeldet. Die fachliche Richtigkeit medizinischer Karten, die Existenz und Autorität von Quellen sowie externe URLs werden nicht verifiziert.

## Lokale Metadaten und Claude-Paket ab 0.4.0

`state.py` verwaltet eine separate lokale SQLite-Datei in `user_files`, abhängig vom Sammlungspfad. Die Anki-Datenbank wird dafür nicht separat geöffnet. Die Datei speichert MCP-Schreibprotokolle, temporäre Änderungspläne, Quellenrevisionen/-verknüpfungen und gespeicherte Prüfungsanfragen. Sie enthält private Inhalte, unter POSIX wird Modus 0600 gesetzt; unter Windows gelten die Profilberechtigungen. Es gibt keine automatische Aufbewahrungsfrist. Quellen, Links und Prüfungsaufträge sind über JSON exportierbar; Journal und Änderungspläne nicht. Anki-Sync und Anki-Backups umfassen diese Datei nicht. Anki schließen und `user_files` für eine vollständige lokale Metadatensicherung kopieren.

`tools_changes.py` prüft die expliziten Zielzustände direkt vor Anwendung auf dem Qt-Hauptthread. Mehrere Operationen werden in einer nativen Undo-Gruppe zusammengefasst, sind jedoch keine atomare Transaktion. Lokale Metadaten werden durch Collection-Undo nicht zurückgesetzt. Eine fehlgeschlagene Protokollfinalisierung lässt den Eintrag `pending`, anstatt eine bereits gespeicherte Operation als fehlgeschlagen auszugeben. Die Journalgrenzen und der genaue Ablauf stehen in [workflows.md](workflows.md).

`tools_study.py` berechnet lokale TF-IDF-Ähnlichkeitskandidaten und eine Budgetverteilung über aktuelle Fälligkeiten. Es verwendet keine externen Embeddings oder medizinische Bewertung. Prüfungsplanung prognostiziert keine späteren Antwortfolgen, Lernschritte oder neuen Wiederholungen und ändert keine Scheduler-Einstellungen.

`clients/claude` enthält das MCPB-Manifest und eine eigenständige Node-stdio-Bridge ohne Abhängigkeiten. Das Build-Skript erzeugt ein reproduzierbares ZIP mit Endung `.mcpb`. Die Bridge verbindet sich nur mit 127.0.0.1, liest den lokalen Token aus einer ausgewählten Datei, leitet MCP-Bildblöcke durch und wiederholt fehlgeschlagene Schreibanfragen nicht automatisch. Der Node-Transport wird aus dem tatsächlich extrahierten Paket mit dem offiziellen MCP-Client getestet. Manifest und Format folgen der [MCPB-Spezifikation](https://github.com/anthropics/mcpb/blob/main/MANIFEST.md); die Validierung verwendet MCPB CLI 2.1.2. Eine Installation in einer konkreten Claude-Desktop-Version ist eine separate manuelle Prüfung.
