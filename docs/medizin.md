# Beispiele für das Medizinstudium

Die Beispiele verwenden symbolische IDs. Vor Änderungen die tatsächlichen IDs mit `list_decks`, `list_notetypes` und `search` ermitteln. Kartentexte sind HTML; Cloze-Syntax und MathJax bleiben erhalten. Quellenangaben gehören in ein eigenes Feld oder auf die Rückseite.

## Bestehende Decks analysieren

1. `list_decks` und `collection_info` lesen.
2. `learning_overview` mit `{"query":"deck:Medizin tag:Kardiologie","forecast_days":14}` aufrufen.
3. `search` mit `{"query":"deck:Medizin prop:lapses>=3 -is:suspended","kind":"cards"}` findet Karten mit wiederholten Fehlversuchen.
4. Mit `get_cards`, `get_notes`, `card_statistics` und `review_history` Inhalte und Lernprobleme untersuchen. Die Notiz-ID steht bei `get_cards` unter `nid`.
5. `learning_statistics` mit derselben Suchabfrage liefert native Statistikdaten. Die KI kann daraus Lernempfehlungen ableiten; sie sollte tatsächliche Messwerte und ihre Interpretation unterscheiden.

Die Fälligkeitsvorschau zählt bereits geplante Wiederholungskarten. Neu hinzukommende Karten und zukünftige Lernantworten können die tatsächliche Arbeitslast verändern.

## Cloze-Notiz erstellen

`add_notes` mit der tatsächlichen ID des Cloze-Notiztyps:

```json
{
  "notes": [{
    "deck_id": 123,
    "notetype_id": 456,
    "fields": {
      "Text": "Der {{c1::N. phrenicus}} entspringt aus {{c2::C3–C5}}.",
      "Back Extra": "Quelle: vom Nutzer genanntes Lehrbuch, Kapitel und Seite"
    },
    "tags": ["Medizin::Anatomie::Nerven", "Examen::M1"]
  }]
}
```

Anki generiert zwei Karten. Bei übersetzten oder eigenen Notiztypen vorher die exakten Feldnamen mit `get_notetype` auslesen.

## Anatomie oder Histologie verdecken

Zuerst `store_media` mit `filename` und `data_base64` aufrufen. Den **zurückgegebenen** Dateinamen verwenden: Anki kann bei Namenskollisionen einen anderen vergeben.

```json
{
  "deck_id": 123,
  "filename": "plexus.png",
  "rectangles": [
    {"ordinal": 1, "left": 0.10, "top": 0.20, "width": 0.25, "height": 0.08},
    {"ordinal": 2, "left": 0.55, "top": 0.35, "width": 0.20, "height": 0.08}
  ],
  "header": "Benenne die verdeckte Struktur.",
  "back_extra": "Quelle: eigenes Schema",
  "tags": ["Medizin::Anatomie::Plexus"]
}
```

Dies sind Argumente für `create_image_occlusion`. Alle Koordinaten sind Anteile der Bildgröße, unabhängig von den Pixelmaßen. Gleiche `ordinal`-Werte fassen mehrere Masken zu einer Karte zusammen. Für Ellipsen, Polygone und andere native Formen kann stattdessen das Feld `occlusions` mit Ankis vollständiger Maskensyntax übergeben werden. `get_image_occlusion` liest bestehende Formen, `update_image_occlusion` bearbeitet sie.

Audio oder Video wird nach `store_media` beispielsweise als `[sound:herzgeraeusch.mp3]` in einem Notizfeld verwendet. Das Add-on speichert vorhandene Dateien; Aufnahme und Erzeugung erfolgen außerhalb des Add-ons.

## Einstellungen für die Prüfungsvorbereitung

Erst `get_deck_options` lesen. `native_schema` mit `{"name":"deck_config"}` beschreibt alle verfügbaren Optionsfelder deiner Anki-Version.

```json
{
  "deck_id": 123,
  "preset_name": "Medizin – Prüfungsvorbereitung",
  "patch": {
    "new_per_day": 30,
    "reviews_per_day": 250,
    "desired_retention": 0.90,
    "learn_steps": [1, 10],
    "bury_new": true,
    "bury_reviews": true
  },
  "limits": { "new": 30, "review": 250 }
}
```

Dies sind Argumente für `set_deck_options`. Die Werte sind ein Syntaxbeispiel, keine allgemeine Lernempfehlung. Es wird standardmäßig eine eigene Vorlage erzeugt. `global_fsrs: true` aktiviert FSRS für die gesamte Sammlung. `fsrs_parameters` kann Parameter anhand vorhandener Lernhistorie berechnen; erst nach Prüfung über `patch.fsrs_params_6` anwenden. Die Evaluation benötigt ausreichend echte Wiederholungen.

## Karten gezielt aussetzen

`search` mit `{"query":"tag:Medizin::Anatomie::Altstoff","kind":"cards"}` aufrufen und die Treffer mit `get_cards` prüfen. Anschließend:

```json
{
  "card_ids": [1001, 1002],
  "action": "suspend",
  "confirm": true
}
```

Dies sind Argumente für `schedule_cards`. `unsuspend` aktiviert die Karten erneut. Tags hängen an **Notizen**, Aussetzung und Flags an **Karten**. Eine Notiz kann mehrere Karten erzeugen.

## Individuelles Lernen

`filtered_deck` kann zum Beispiel `deck:Medizin tag:Kardiologie is:due` zu einem Prüfungsdeck zusammenstellen. `custom_study_defaults` liest die Ausgangswerte; `native_schema` mit `custom_study` zeigt die vollständigen Optionen. Beispiel zum Erhöhen des heutigen Neukartenlimits:

```json
{"request": {"deck_id": 123, "new_limit_delta": 10}, "confirm": true}
```

Dies sind Argumente für `custom_study`. Die Prüfungsvorbereitung lässt sich auch über `review_ahead_days`, `forgot_days`, `preview_days` oder native `cram`-Optionen steuern.
