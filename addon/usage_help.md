# Mit der KI lernen und Karten bearbeiten

Die KI bekommt beim Verbinden die Beschreibung der MCP-Werkzeuge, ihre Eingabefelder und Hinweise zum Vorgehen. Über `usage_guide` kann sie Beispiele zu Bildverdeckung, Notiztypen, Medien, Lernständen und Qualitätsprüfung abrufen. Das ist eine Anleitung für das Modell; es garantiert weder die richtige Werkzeugwahl noch fachlich richtige Karten.

Nach einem Update Anki und den KI-Client vollständig neu starten, damit die neuen Werkzeuge und Hinweise eingelesen werden. Die Einrichtung für Windows und macOS steht im ersten Reiter.

## Bildverdeckung erstellen

Beispiel für deinen Assistenten:

> Lies zuerst deine Anleitung zur Bildverdeckung und meine verfügbaren Notiztypen. Nutze dieses Anatomiebild, sieh es dir an und verdecke jede Beschriftung auf einer eigenen Karte. Zeige mir den vorgesehenen Umfang, bevor du speicherst. Die Quelle soll auf der Rückseite stehen.

Die KI kann ein bereits in Anki gespeichertes Bild mit `get_image` als tatsächliches Bild an einen bildfähigen Client ausgeben. Rechteckmasken verwenden Koordinaten relativ zur Bildgröße. Gleiche Maskennummern gruppieren mehrere Rechtecke zu einer Karte; verschiedene Nummern erzeugen verschiedene Karten.

Voraussetzungen:

- Der gewählte Client und das Modell können Bilder verarbeiten. Andernfalls sind ein zusätzliches Bildwerkzeug oder von dir vorgegebene Koordinaten nötig.
- Das Bild liegt in Ankis Medienordner. Die KI lädt es vorher mit `store_media` hoch, wenn sie Zugriff auf die tatsächlichen Dateibytes hat. Nicht jeder KI-Client kann Anhänge automatisch als Datei auslesen.
- Zum Ansehen werden PNG, JPEG, GIF und WebP bis 4 MiB unterstützt. Die tatsächlich unterstützten Formate hängen zusätzlich vom KI-Client ab. PDF und SVG müssen vorher außerhalb dieses Add-ons in ein geeignetes Bild umgewandelt werden.
- Die Anki-Funktion ist für native Bildverdeckung und kompatible Klone vorgesehen. Namen allein, beispielsweise „Ankiphil – iOcclusion“, beweisen keine Kompatibilität. Die KI soll den Notiztyp zuerst auslesen.

Vorhandene Masken können gelesen und geändert werden. Beim Entfernen einer Maske kann Anki eine leere Karte mit Lernhistorie behalten. Die KI soll diese über `empty_cards` prüfen und nur auf deinen ausdrücklichen Wunsch löschen.

## Eigene Notiztypen

Beispiel:

> Erstelle einen Notiztyp „Medizin – Quellenkarten“ mit den Feldern Frage, Antwort und Quelle. Er soll Vorwärts- und Rückwärtskarten erzeugen, linksbündig und gut lesbar sein. Zeige erst eine Vorschau an einer Beispielnotiz.

Die KI kann Felder, HTML-Vorlagen und CSS anlegen, bestehende Typen klonen und die erzeugten Karten lesen. Auch Cloze-Notiztypen sind möglich. Für ein eigenes Layout der nativen Bildverdeckung sollte sie den vorhandenen nativen Typ klonen und dessen Maskenfelder und Vorlagenlogik beibehalten.

Angepasste oder übersetzte Feldnamen werden aus Anki gelesen. Funktionen fremder Add-ons, etwa eigene Maskeneditoren oder Zusatzgeneratoren, werden dadurch nicht automatisch zu MCP-Werkzeugen. Ein Notiztypwechsel oder das Entfernen von Feldern/Vorlagen kann Daten und Karten löschen; vorher Zuordnung und Umfang prüfen.

## Vorschau vor dem Speichern

Beispiel:

> Entwirf zehn Kardiologie-Notizen. Verwende ausschließlich meine angegebenen Quellen und zeige zuerst die Kartenvorschau, ohne etwas zu speichern.

`preview_notes` rendert Frage, Antwort und CSS durch Ankis native Kartenvorschau. Dabei werden keine Notizen oder Karten gespeichert. Die KI erhält HTML, keine Bildschirmaufnahme. Doppelte erste Felder werden als Warnung gemeldet. Bei Standardtypen werden alle Vorlagen gezeigt; bedingte Vorlagen können bei der tatsächlichen Kartenerzeugung entfallen. Dynamische Spezialfelder wie der Deckname können in der Vorschau native Platzhalter enthalten.

Erst nach Prüfung kann die KI die tatsächlichen Notizen mit `add_notes` speichern.

## Sammlung auf Lücken prüfen

Beispiel:

> Prüfe mein Deck Medizin::Anatomie auf leere Antwort- und Quellenfelder sowie fehlende Bilder oder Audiodateien. Lies dafür zuerst die tatsächlichen Feldnamen. Berichte die Ergebnisse, ohne etwas zu ändern.

`audit_notes` arbeitet mit Ankis Suchsyntax und prüft seitenweise:

- Leere Felder und ausdrücklich verlangte Pflichtfelder.
- Pflichtfelder, die im verwendeten Notiztyp gar nicht existieren.
- Fehlende lokale Bild-, Audio- und Videodateien.
- Cloze-Notizen ohne erkennbare Cloze-Markierung.

Ein Bild als einziger Feldinhalt gilt als Inhalt. Externe URLs werden nicht aufgerufen oder auf Erreichbarkeit geprüft. Ein ausgefülltes Quellenfeld bestätigt nur, dass dort Inhalt steht. Es beweist nicht die Existenz oder Zuverlässigkeit der Quelle und prüft keine medizinische Aussage.

Die KI soll alle Ergebnis-Seiten lesen oder den tatsächlich geprüften Ausschnitt benennen. Keine Inhalte werden automatisch korrigiert oder gelöscht.

## Lernstand und Lernplanung

> Analysiere mein Kardiologie-Deck: Was ist fällig, welche Karten fallen häufig durch, und wie sehen die FSRS-Einstellungen aus? Schlage Änderungen vor, aber beantworte keine Lernkarten für mich.

Die Schnittstelle kann Lernzustände, Wiederholungshistorie und native Statistikdaten lesen. Eine echte Lernantwort, das Zurücksetzen von Karten oder Änderungen an Deck-Einstellungen beeinflussen die zukünftige Planung. Die KI soll solche Änderungen gezielt auf deinen Auftrag hin vornehmen.

## Bestehende Karten mit Änderungsvorschau bearbeiten

> Zeige zuerst, welche Antworten und Tags du ändern würdest. Erstelle dafür einen Änderungsplan und wende ihn erst im besprochenen Umfang an.

Die KI kann `plan_changes` für vorhandene Notizen, Tags, Karten und Deck-Einstellungen nutzen. Der Plan zeigt Vorher/Nachher und wird nach 24 Stunden ungültig. Haben sich die Ziele inzwischen geändert, muss sie neu planen. Mehrere Operationen können bei einem Fehler Teiländerungen hinterlassen; vor erneutem Aufruf den Zustand prüfen. Das dauerhafte MCP-Protokoll ist im Reiter **Änderungsprotokoll** lesbar. Es enthält keine manuellen GUI-Änderungen und ersetzt kein Backup.

## Ähnliche Karten finden

> Suche Textüberschneidungen in meinem Anatomie-Deck. Lies die Kandidaten vollständig und prüfe Lernziel, Verneinungen und Quellen, bevor du Änderungen empfiehlst. Lösche nichts automatisch.

Die Suche ist lokal und auf maximal 500 Notizen begrenzt. Ihr Wert misst Textähnlichkeit, keine medizinische Gleichwertigkeit. Gemeinsame Quellentexte können den Wert erhöhen; die Suche kann auf bestimmte Felder beschränkt werden.

## Prüfung mit Zeitbudget planen

> Ich schreibe am 15. Dezember 2026 Anatomie und habe täglich 60 Minuten. Plane bis zum Vortag aus meinem Lernstand und meinen Fälligkeiten. Zeige, was nicht ins Budget passt, und ändere keine Deck-Limits.

`exam_plan` plant mit ausdrücklichen Sekundenannahmen pro neuer Karte und Wiederholung. Wochenbudgets mit freien Tagen sind möglich. Nicht berücksichtigt sind spätere neue Wiederholungen, Lernschritte oder künftige Antworten. Einen Zeitpuffer lassen und regelmäßig neu berechnen. Mit `save_exam_plan` kann die KI den Auftrag lokal speichern.

## Quellen und neue Auflagen nachverfolgen

> Verknüpfe diese Notizen mit meiner angegebenen Quelle und Fundstelle. Wenn sich die Quelle ändert, zeige mir die betroffenen Notizen zur Überprüfung.

Quellen können strukturiert mit Ausgabe, Autoren, Jahr, URL/ISBN und Fundstelle gespeichert werden. Optional ergänzt die KI ein bestehendes Quellenfeld, das normal mit Anki synchronisiert wird. Die separaten Quellenverknüpfungen, Revisionen, Prüfungspläne und das Journal bleiben lokal in `user_files`; Anki-Sync überträgt sie nicht. `export_workspace` und `import_workspace` übertragen Quellen und gespeicherte Prüfungsaufträge zur selben Sammlung auf einem anderen Rechner. Journal separat sichern. Keine medizinischen Belege werden automatisch überprüft oder erfunden.
