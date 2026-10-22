# MCP-Werkzeuge

65 Werkzeuge. Automatisch aus dem Tool-Register erzeugt.

Die vollständigen JSON-Eingabeschemas stehen in [tools.json](tools.json). Native Einstellungsfelder lassen sich mit `native_schema` abfragen.

| Werkzeug | Zugriff | Zweck |
| --- | --- | --- |
| `collection_info` | Lesen | Current collection counts, scheduler day, FSRS enabled, due tree and undo status. |
| `list_decks` | Lesen | All deck names, IDs, hierarchy and scheduler counts. |
| `get_deck` | Lesen | Read a deck's full native record, including per-deck overrides. |
| `create_deck` | Schreiben | Create a normal deck. Hierarchy uses ::, e.g. Medizin::Anatomie. |
| `rename_deck` | Schreiben | Rename or move a deck and its children using :: hierarchy. |
| `delete_decks` | Schreiben, `confirm=true` | Delete decks, subdecks and their cards. Inspect first; confirm required. |
| `update_deck` | Schreiben | Patch description and per-deck daily limits. get_deck shows native key names. |
| `get_deck_options` | Lesen | Full modern deck presets, FSRS parameters, retention, limits, defaults and shared preset use counts. Integers may be protobuf strings. |
| `set_deck_options` | Schreiben | Patch every native preset option (snake_case). Default clones preset for this deck. shared=true changes all decks using it. global_fsrs explicitly changes collection-wide FSRS. |
| `assign_deck_preset` | Schreiben | Assign an existing options preset to a normal deck. |
| `filtered_deck` | Schreiben | Create, configure, rebuild or empty a filtered/custom-study deck. Query uses Anki search. Does not change the active deck. |
| `get_preferences` | Lesen | Read all native scheduling, reviewing, editing and backup preferences. |
| `set_preferences` | Schreiben | Recursively patch native Anki preferences; get_preferences gives valid keys. |
| `list_notetypes` | Lesen | List native note type IDs, names and use counts. |
| `get_notetype` | Lesen | Read all fields, HTML templates, CSS and native note type options. |
| `create_notetype` | Schreiben | Create a standard or cloze note type with arbitrary fields, HTML templates, CSS, MathJax/LaTeX support. |
| `update_notetype` | Schreiben, `confirm=true` | Update native note type fields, templates and CSS. Supply full ordered flds/tmpls arrays from get_notetype to add, remove, reorder or rename; preserve ord for existing entries. Can remove cards. |
| `clone_notetype` | Schreiben | Clone all fields, templates and styling of a note type. |
| `delete_notetype` | Schreiben, `confirm=true` | Delete a note type and its notes/cards. confirm required. |
| `undo` | Schreiben, `confirm=true` | Undo the last Anki operation; also affects changes made manually in the GUI. |
| `redo` | Schreiben, `confirm=true` | Redo the last undone Anki operation. |
| `native_schema` | Lesen | Discover every native field, enum value and nested structure accepted by settings, custom study and package import. Schemas reflect the running Anki version. |
| `search` | Lesen | Search existing cards or notes with full Anki browser syntax: deck:, tag:, is:due, is:suspended, prop:lapses>3, added:, rated:, etc. Paginated IDs. |
| `get_notes` | Lesen | Read fields as HTML, tags, GUIDs and generated card IDs. |
| `get_cards` | Lesen | Read scheduling and FSRS memory state. render=true includes question/answer HTML and CSS. due units depend on queue; see docs. |
| `add_notes` | Schreiben | Create rich HTML notes with images (<img src=...>), audio/video ([sound:...]), cloze syntax and tags. Upload media first. Native Anki generates cards. Validates the whole batch before adding. |
| `update_notes` | Schreiben | Patch named fields and optionally replace tags. Omitted fields/tags remain unchanged; all notes validated before saving. |
| `delete_notes` | Schreiben, `confirm=true` | Delete notes and every card generated from them, including review history. confirm required. |
| `list_tags` | Lesen | Read all registered tags and their hierarchy. |
| `edit_tags` | Schreiben | Add or remove tags on explicit note IDs. Supports hierarchical tags such as Medizin::Kardiologie. |
| `rename_tag` | Schreiben | Rename a tag and all its children across the collection. |
| `remove_tag` | Schreiben, `confirm=true` | Remove a tag and its children from the entire collection. confirm required. |
| `change_notetype` | Schreiben, `confirm=true` | Convert notes to a new note type using native field/template mapping. Maps are target-index -> source-index arrays; -1 means blank/new. May delete cards. Inspect types first. |
| `find_duplicates` | Lesen | Find duplicate note field content within an Anki search (e.g. identify redundant medical facts). |
| `find_replace` | Schreiben, `confirm=true` | Native find/replace on explicit notes, optionally in one field. Supports regex and case matching. confirm required. |
| `empty_cards` | Lesen | Report cards whose cloze, mask or template content was removed. Native Anki preserves these until explicitly deleted. |
| `delete_cards` | Schreiben, `confirm=true` | Delete explicit individual cards and any resulting orphan notes. Removes review history. Useful after inspecting empty_cards; confirm required. |
| `usage_guide` | Lesen | Read concrete Anki MCP workflows and examples. Call before image occlusion or custom note types. Explains localized fields, media, mask grouping, native vs third-party types and safe editing. |
| `card_statistics` | Lesen | Full native per-card statistics: review logs, FSRS difficulty/stability/retrievability, intervals, lapses and timing. |
| `review_history` | Lesen | Paginated native review history for a card. Timestamps, ratings, elapsed times and scheduling details. |
| `learning_statistics` | Lesen | Native Anki graphs for any search: review counts/time, intervals, card counts, answer ratings, FSRS retention/stability/difficulty and forecast. days=0 means all history. |
| `learning_overview` | Lesen | Study dashboard for a search: total/new/learning/review, due, suspended, buried, leeches, mature cards, repeated lapses and forecast by day. Counts are independent (some overlap). |
| `schedule_cards` | Schreiben, `confirm=true` | Suspend, unsuspend, bury, unbury, move, flag, set due dates, forget or reposition explicit cards. Forget resets scheduling; confirm required for all actions. Uses native scheduler. |
| `review_queue` | Lesen | Read the active deck's native review queue and next answer states, without answering cards. |
| `select_deck` | Schreiben | Select active deck for the Anki reviewer. Does not submit answers. |
| `answer_card` | Schreiben, `confirm=true` | Submit an actual review answer through Anki's scheduler and write review history. Only use when user explicitly requests reviewing. Rating 1=Again, 2=Hard, 3=Good, 4=Easy. Requires first card in active queue. |
| `custom_study_defaults` | Lesen | Read native custom study defaults for a deck: limits, tags and study options. |
| `custom_study` | Schreiben, `confirm=true` | Run native custom study: extend today's limits, study ahead, review forgotten cards, preview new cards, cram by tags. Request accepts native CustomStudyRequest JSON. Use custom_study_defaults first; confirm required. |
| `fsrs_parameters` | Lesen | Compute or evaluate native FSRS parameters from the matching review history without changing settings. Requires sufficient reviews; may take time. Apply computed parameters separately with set_deck_options(fsrs_params_6). |
| `store_media` | Schreiben | Store image, audio, video or other media from base64. Returns actual collision-safe filename and HTML/sound references. Never assumes requested filename was retained. |
| `read_media` | Lesen | Read local collection media as base64 in chunks; no arbitrary filesystem access. Default chunk 1 MiB. |
| `list_media` | Lesen | List collection media, optionally filtered by filename substring. |
| `check_media` | Schreiben | Native Anki missing/unused media report; may normalize filenames and take time on large collections. |
| `trash_media` | Schreiben, `confirm=true` | Move specified collection media into Anki media trash. Not covered by collection undo; restore with restore_media_trash. |
| `restore_media_trash` | Schreiben | Restore Anki's media trash (all files). |
| `create_image_occlusion` | Schreiben | Create native Image Occlusion cards for anatomy/histology etc. Upload image first. Rectangles use normalized 0..1 coordinates and ordinal >=1; same ordinal groups masks on one card. Alternatively provide native cloze occlusions markup for ellipse/polygon/text and all advanced shapes. |
| `get_image_occlusion` | Lesen | Read native parsed occlusion shapes, grouping and note metadata. Image bytes use read_media. |
| `update_image_occlusion` | Schreiben | Update native Image Occlusion masks and optional header/back/tags. Rebuilds generated cards using Anki. Pass rectangles OR native occlusions to change masks. |
| `transfer_file` | Schreiben | Upload/download/list/delete staged .apkg files in the add-on's user_files/transfers folder. Upload chunks with offset (max 20 MiB per chunk, 512 MiB file). offset=0 creates a NEW file; delete first to replace. Never reads arbitrary paths. |
| `export_package` | Schreiben | Export a deck (including children) or entire collection to a staged .apkg, with media, scheduling and deck configs. Download with transfer_file. Does not close the collection. |
| `import_package` | Schreiben, `confirm=true` | Import a staged .apkg through Anki's native importer, including media, tags and optional scheduling. Native importer options can be provided. Not covered by collection undo; backup first. |
| `create_backup` | Schreiben | Create a native collection backup in add-on user_files/backups. Media are excluded by Anki; export_package includes them. Backup files are not sent to the model. |
| `get_image` | Lesen | View an existing collection image as actual MCP image content for vision-capable clients. Use before placing occlusion masks. Supports PNG/JPEG/GIF/WebP, maximum 4 MiB; SVG/PDF must be converted by the client first. |
| `preview_notes` | Lesen | Render proposed notes as native Anki question/answer HTML and CSS before saving. Does not add notes/cards. Standard note types preview every template; conditional templates may not generate a saved card. Cloze previews use actual cloze ordinals. Reports duplicates as warnings. |
| `audit_notes` | Lesen | Technical note-quality audit for an Anki search: empty fields, missing local image/audio/video files, optional required/source fields and absent cloze markup. Paginated, read-only. Does not verify medical accuracy, authenticity of sources or remote URLs. required_fields use exact localized names. |
