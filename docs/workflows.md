# Änderungen, Quellen und Prüfungsplanung

Diese Abläufe sind über die Tool-Beschreibungen, die MCP-Initialisierung und `usage_guide` auch für die KI zugänglich. Das hilft dem Modell beim Vorgehen, garantiert aber keine fehlerfreie fachliche Bewertung.

## Bestehende Inhalte prüfen und ändern

Nach einer Anki-Suche die vollständigen Zielnotizen/-karten lesen und die vorgesehenen Änderungen mit `plan_changes` vorbereiten:

```json
{
  "calls": [
    {"tool": "update_notes", "arguments": {"updates": [
      {"note_id": 1234567890, "fields": {"Antwort": "Vom Nutzer geprüfte Antwort"}}
    ]}}
  ]
}
```

IDs und Feldnamen sind Beispiele: zuerst die tatsächlichen Namen mit `get_notetype` lesen. Die Antwort enthält `id`, `previews`, Ablaufzeit und den beantragten Umfang. Die Vorschau dem Nutzer zeigen, dann innerhalb seines Auftrags `apply_change_plan(plan_id, confirm=true)` verwenden. Ankis Scheduler bestimmt bei Aussetzen/Vergraben die endgültigen Werte; die Vorschau bezeichnet hierfür die geplante Aktion. Tags werden von Anki beim Speichern kanonisiert.

Ein Plan läuft nach 24 Stunden ab, ist nur einmal anwendbar und prüft seine Zielzustände unmittelbar vor der ersten Änderung. Bei veränderten Zielen eine neue Vorschau erstellen. Maximal 20 Operationen, höchstens 200 explizite Ziele pro Operation; wiederholte Ziele in einem Plan zusammenfassen. Änderungen an Decks/Optionsvorlagen werden zur Vermeidung geteilter Wechselwirkungen einzeln geplant. Umbenennen von Decks mit Unterdecks und weitergehende Scheduler-Aktionen bleiben direkte native Werkzeuge mit vorheriger Prüfung.

Mehrere Sammlungsänderungen werden für Undo zusammengefasst; sie sind keine atomare Transaktion. Ein Fehler kann Teiländerungen hinterlassen. Vor erneutem Aufruf Ziele und `change_history` lesen. Nach erfolgreichem Anwenden wird der Plan auch durch Anki-Undo nicht wieder zum unbenutzten Plan: für weitere Änderungen neu planen.

## Dauerhaftes Protokoll

`change_history` liefert paginierte Einträge; mit `entry_id` die Vorher-/Nachher-Schnappschüsse. In Anki findet sich dieselbe Ansicht unter **Einrichtung & Hilfe → Änderungsprotokoll → Protokoll laden / aktualisieren**. Die Oberfläche zeigt die letzten 100 Einträge, ältere sind über das MCP-Werkzeug erreichbar.

Protokolliert werden MCP-Schreibzugriffe nach erfolgreicher Schema-/Berechtigungsprüfung. Das Protokoll erfasst keine manuellen GUI-Änderungen und ist kein vollständiges Backup. Explizite Notiz-, Karten- und Deckziele werden bis zu 200 Objekten erfasst; große Schnappschüsse sind auf 2 MiB begrenzt. Medienbytes werden nicht protokolliert. Globale Operationen und Importe haben nur begrenzte Zustandsdaten. Status `pending` bedeutet nach einem Absturz einen unbekannten Ausgang; `failed_may_have_partial_effects` erfordert Prüfung. Eine fehlgeschlagene Protokollfinalisierung macht eine bereits gespeicherte Operation nicht rückgängig.

Die SQLite-Datei liegt lokal in `user_files`, getrennt von Ankis Datenbank und nach Sammlungspfad zugeordnet. Sie enthält private Karteninhalte. Für die Sicherung Anki schließen und `user_files` kopieren. Metadatenänderungen wie Quellen und gespeicherte Pläne liegen außerhalb von Ankis Undo und Sync.

## Ähnliche Karten

`similar_notes(query, fields, max_notes, min_score, max_pairs)` findet Textüberschneidungen mit lokalen TF-IDF-Wort- und Zeichenmerkmalen. Die Suche untersucht maximal 500 nach ID sortierte Notizen und meldet eine Beschränkung ausdrücklich. Felder werden nach ihren tatsächlichen Namen ausgewählt. Ohne Feldliste wird über alle Felder verglichen; gemeinsame Quellen-/Vorlagentexte können den Wert erhöhen.

Die KI soll Kandidaten mit `get_notes` vollständig lesen und Bedeutung, Verneinungen, Lernziel und Quelle vergleichen. Hohe Ähnlichkeit kann gerade bei widersprüchlichen Aussagen auftreten. Die Bewertung ist keine medizinische Prüfung; es gibt kein automatisches Zusammenführen oder Löschen.

## Prüfungstermin und Zeitbudget

```json
{
  "exam_date": "2026-12-15",
  "daily_minutes": 60,
  "query": "deck:Medizin::Anatomie",
  "new_card_seconds": 120,
  "review_card_seconds": 30,
  "topics": [{"name": "Plexus", "query": "tag:Anatomie::Plexus"}]
}
```

`exam_plan` reserviert zuerst Zeit für derzeit terminierte Wiederholungskarten einschließlich Rückständen und verteilt danach neue Karten auf die verbleibende Kapazität bis zum Tag vor der Prüfung. `weekly_minutes` kann sieben Tagesbudgets von Montag bis Sonntag angeben, auch 0 für freie Tage. Der Start muss heute oder später liegen, der Planungshorizont beträgt maximal 365 Tage. Themenzählungen können sich überschneiden.

Neue Karten werden nach Kapazität verteilt; es gibt keine Priorisierung der Themen und keine automatische Änderung von Deck-Limits. Zusätzliche Wiederholungen neu gelernter Karten, spätere Antworten und Lernschritte sind nicht prognostiziert. Ausgesetzte/vergrabene Karten sind ausgeschlossen. Zeitwerte sind ausdrücklich Annahmen. Einen Zeitpuffer einplanen, regelmäßig neu berechnen und `unallocated_new_cards` sowie `review_overload_minutes` beachten.

`save_exam_plan(name, request)` speichert den Auftrag und den damaligen Schätzwert lokal. `saved_exam_plans` liest diese Daten; für aktuelle Lernstände erneut `exam_plan` aufrufen.

## Quellen mit Revisionen

1. `create_source(source)` mit vom Nutzer bereitgestelltem Titel, Autoren, Ausgabe, Jahr, URL/ISBN und Fundstelle aufrufen. Es wird nichts erfunden, heruntergeladen oder auf fachliche Richtigkeit geprüft.
2. `link_source(source_id, note_ids, locator)` verknüpft Notizen mit der aktuellen Quellenrevision. Optional `citation_field` angeben: Das bestehende Feld erhält einen HTML-maskierten Quellenhinweis, der wie normaler Notizinhalt über Anki synchronisiert wird.
3. Bei einer neuen Ausgabe/Korrektur `update_source(source_id, source)` aufrufen. Die Revision steigt; `source_notes(needs_review_only=true)` meldet betroffene Notizen. Karten und vorhandene Quellenfelder bleiben unverändert.
4. Nach tatsächlicher Überprüfung der Karten `acknowledge_source_review(source_id, note_ids, confirm=true)` verwenden. Erneutes Verknüpfen allein bestätigt keine geänderte Quelle. Eine Quellenrevision bedeutet auch bei reinen Metadatenänderungen eine neue Prüfanforderung.
5. `export_workspace` sichern. `import_workspace(data, confirm=true)` kann Quellen, Verknüpfungen und gespeicherte Prüfungsaufträge mit derselben Sammlung auf einen anderen Rechner übertragen. Gleiche IDs werden ersetzt; vorab exportieren. Es ist kein vollständiger Sammlungs- oder Medienexport. Journal und temporäre Änderungspläne werden nicht übertragen.

Quellen und Links werden lokal gespeichert und nicht von Anki synchronisiert. Ein Quellenfeld synchronisiert nur den eingetragenen Text, nicht die Metadaten-Datenbank. Nicht in eine fremde Sammlung importieren: Notiz-IDs sind sammlungsspezifisch.
