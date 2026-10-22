# Architektur, Kompatibilität und Grenzen

## Aufbau

`addon/desktop.py` verbindet Ankis Profil-Hooks mit dem Server und plant jede Sammlungsoperation auf dem Qt-Hauptthread. `server.py` stellt `/mcp` auf `127.0.0.1` bereit. `protocol.py` implementiert JSON-RPC, MCP-Initialisierung, Ping und Werkzeuge. `registry.py` enthält explizite Eingabeschemas und deren Laufzeitprüfung. Die vier `tools_*.py`-Module verwenden native Anki-APIs. `api.py` kapselt Schreibschutz, Undo, Objektprüfung und die Serialisierung von Protobuf-Ergebnissen.

Das Add-on selbst benötigt ausschließlich Anki und dessen mitgelieferte Python-Bibliotheken. Es öffnet keine zweite Datenbankverbindung zur laufenden Sammlung. Es gibt kein `eval`, kein frei ausführbares Python und keinen SQL-Schreibzugriff. Eine interne, konstante SQL-Leseabfrage ermittelt den Schema-Zeitstempel für die native Notiztypkonvertierung.

Der HTTP-Transport verwendet zustandslose JSON-Antworten ohne SSE-Stream oder Session-ID. `GET` und `DELETE` liefern 405. Unterstützte MCP-Protokollversionen: `2025-11-25`, `2025-06-18`, `2025-03-26` und über die stdio-Bridge auch Clients mit `2024-11-05`. Der HTTP-Transport setzt Streamable-HTTP-Unterstützung im Client voraus. JSON-RPC-Batches werden abgewiesen. Fortschrittsnachrichten, Remote-OAuth, Roots, Sampling und serverseitige Ressourcen sind nicht implementiert.

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
