"""Decks, full native options, note types, preferences and collection tools."""

from .api import plain, patch_message
from .registry import tool, S, I, B, O, arr, enum, ToolError


@tool("collection_info", "Current collection counts, scheduler day, FSRS enabled, due tree and undo status.")
def info(s):
    return {
        "notes": s.col.note_count(),
        "cards": s.col.card_count(),
        "scheduler_day": s.col.sched.today,
        "day_cutoff_unix": s.col.sched.day_cutoff,
        "studied_today": s.col.studied_today(),
        "fsrs_enabled": s.col.get_config("fsrs", False),
        "read_only": s.read_only,
        "due_tree": plain(s.col.sched.deck_due_tree()),
        "undo": plain(s.col.undo_status()),
    }


@tool("list_decks", "All deck names, IDs, hierarchy and scheduler counts.")
def decks(s):
    return {"decks": s.col.decks.get_all_legacy(), "due_tree": plain(s.col.sched.deck_due_tree())}


@tool("get_deck", "Read a deck's full native record, including per-deck overrides.", {"deck_id": I}, ("deck_id",))
def get_deck(s, deck_id):
    return s.deck(deck_id)


@tool("create_deck", "Create a normal deck. Hierarchy uses ::, e.g. Medizin::Anatomie.", {"name": S}, ("name",), write=True)
def create_deck(s, name):
    if not name.strip():
        raise ToolError("Deck name must not be empty")
    existing = s.col.decks.id_for_name(name)
    return {"deck_id": existing or s.col.decks.add_normal_deck_with_name(name).id, "created": existing is None}


@tool(
    "rename_deck", "Rename or move a deck and its children using :: hierarchy.", {"deck_id": I, "name": S}, ("deck_id", "name"), write=True
)
def rename_deck(s, deck_id, name):
    s.deck(deck_id)
    return s.col.decks.rename(deck_id, name)


@tool(
    "delete_decks",
    "Delete decks, subdecks and their cards. Inspect first; confirm required.",
    {"deck_ids": arr(I), "confirm": B},
    ("deck_ids", "confirm"),
    write=True,
    destructive=True,
)
def delete_decks(s, deck_ids, confirm):
    for did in deck_ids:
        s.deck(did)
    return s.col.decks.remove(deck_ids)


@tool(
    "update_deck",
    "Patch description and per-deck daily limits. get_deck shows native key names.",
    {"deck_id": I, "patch": O},
    ("deck_id", "patch"),
    write=True,
)
def update_deck(s, deck_id, patch):
    deck = s.deck(deck_id)
    allowed = {"desc", "dailyLimits", "newLimit", "reviewLimit", "newLimitToday", "reviewLimitToday", "desiredRetention"}
    if set(patch) - allowed:
        raise ToolError("Use dedicated tools for names, options and filtered decks. Allowed: " + ", ".join(sorted(allowed)))
    if set(patch) - deck.keys():
        raise ToolError("Unsupported deck property on this Anki version; inspect get_deck")
    deck.update(patch)
    return s.col.decks.update_dict(deck)


@tool(
    "get_deck_options",
    "Full modern deck presets, FSRS parameters, retention, limits, defaults and shared preset use counts. Integers may be protobuf strings.",
    {"deck_id": I},
    ("deck_id",),
)
def get_options(s, deck_id):
    s.deck(deck_id)
    return s.col.decks.get_deck_configs_for_update(deck_id)


@tool(
    "set_deck_options",
    "Patch every native preset option (snake_case). Default clones preset for this deck. shared=true changes all decks using it. global_fsrs explicitly changes collection-wide FSRS.",
    {"deck_id": I, "patch": O, "shared": B, "preset_name": S, "global_fsrs": B, "limits": O},
    ("deck_id", "patch"),
    write=True,
)
def set_options(s, deck_id, patch, shared=False, preset_name=None, global_fsrs=None, limits=None):
    from anki.decks import UpdateDeckConfigs

    s.deck(deck_id)
    state = s.col.decks.get_deck_configs_for_update(deck_id)
    current = next(x.config for x in state.all_config if x.config.id == state.current_deck.config_id)
    updated = patch_message(current.config, patch)
    clone = type(current)()
    clone.CopyFrom(current)
    clone.config.CopyFrom(updated)
    if not shared:
        clone.id = 0
        clone.name = preset_name or f"{state.current_deck.name} (MCP)"
    elif preset_name:
        clone.name = preset_name
    req = UpdateDeckConfigs(
        target_deck_id=deck_id,
        configs=[clone],
        card_state_customizer=state.card_state_customizer,
        new_cards_ignore_review_limit=state.new_cards_ignore_review_limit,
        fsrs=state.fsrs if global_fsrs is None else global_fsrs,
        apply_all_parent_limits=state.apply_all_parent_limits,
        limits=patch_message(state.current_deck.limits, limits) if limits is not None else state.current_deck.limits,
        fsrs_health_check=state.fsrs_health_check,
    )
    s.col.decks.update_deck_configs(req)
    return s.col.decks.get_deck_configs_for_update(deck_id)


@tool(
    "assign_deck_preset",
    "Assign an existing options preset to a normal deck.",
    {"deck_id": I, "preset_id": I},
    ("deck_id", "preset_id"),
    write=True,
)
def assign_preset(s, deck_id, preset_id):
    deck = s.deck(deck_id)
    if deck["dyn"] or s.col.decks.get_config(preset_id) is None:
        raise ToolError("Expected a normal deck and an existing preset")
    deck["conf"] = preset_id
    return s.col.decks.update_dict(deck)


@tool(
    "filtered_deck",
    "Create, configure, rebuild or empty a filtered/custom-study deck. Query uses Anki search. Does not change the active deck.",
    {
        "action": enum("create", "update", "rebuild", "empty"),
        "deck_id": I,
        "name": S,
        "query": S,
        "limit": {"type": "integer", "minimum": 1, "maximum": 10000},
        "reschedule": B,
    },
    ("action",),
    write=True,
)
def filtered(s, action, deck_id=None, name=None, query=None, limit=100, reschedule=True):
    if action == "create":
        if not name or not query or s.col.decks.id_for_name(name):
            raise ToolError("Provide a new name and nonempty query")
        deck = s.col.decks.new_deck_legacy(filtered=True)
        deck.update(name=name, terms=[[query, limit, 0]], resched=reschedule)
        deck_id = s.col.decks.add_deck_legacy(deck).id
    else:
        if not deck_id:
            raise ToolError("deck_id required")
        deck = s.deck(deck_id)
        if not deck["dyn"]:
            raise ToolError("Expected a filtered deck")
        if action == "update":
            if not query:
                raise ToolError("query required")
            deck.update(terms=[[query, limit, 0]], resched=reschedule)
            s.col.decks.update_dict(deck)
    changes = s.col.sched.empty_filtered_deck(deck_id) if action == "empty" else s.col.sched.rebuild_filtered_deck(deck_id)
    return {"deck_id": deck_id, "changes": plain(changes)}


@tool("get_preferences", "Read all native scheduling, reviewing, editing and backup preferences.")
def preferences(s):
    return s.col.get_preferences()


@tool(
    "set_preferences", "Recursively patch native Anki preferences; get_preferences gives valid keys.", {"patch": O}, ("patch",), write=True
)
def set_preferences(s, patch):
    return s.col.set_preferences(patch_message(s.col.get_preferences(), patch))


@tool("list_notetypes", "List native note type IDs, names and use counts.")
def models(s):
    return [{"id": x.id, "name": x.name, "use_count": x.use_count} for x in s.col.models.all_use_counts()]


@tool("get_notetype", "Read all fields, HTML templates, CSS and native note type options.", {"notetype_id": I}, ("notetype_id",))
def get_model(s, notetype_id):
    return s.model(notetype_id)


@tool(
    "create_notetype",
    "Create a standard or cloze note type with arbitrary fields, HTML templates, CSS, MathJax/LaTeX support.",
    {
        "name": S,
        "fields": arr(S, 100),
        "templates": arr(
            {
                "type": "object",
                "properties": {"name": S, "qfmt": S, "afmt": S},
                "required": ["name", "qfmt", "afmt"],
                "additionalProperties": False,
            },
            100,
        ),
        "css": S,
        "cloze": B,
    },
    ("name", "fields", "templates"),
    write=True,
)
def create_model(s, name, fields, templates, css="", cloze=False):
    if s.col.models.by_name(name):
        raise ToolError("Note type name already exists")
    if len(set(fields)) != len(fields) or any(not x.strip() for x in fields):
        raise ToolError("Fields must be unique and nonempty")
    model = s.col.models.new(name)
    model["type"] = 1 if cloze else 0
    for name in fields:
        s.col.models.add_field(model, s.col.models.new_field(name))
    for data in templates:
        template = s.col.models.new_template(data["name"])
        template.update(data)
        s.col.models.add_template(model, template)
    model["css"] = css
    result = s.col.models.add_dict(model)
    return s.model(result.id)


@tool(
    "update_notetype",
    "Update native note type fields, templates and CSS. Supply full ordered flds/tmpls arrays from get_notetype to add, remove, reorder or rename; preserve ord for existing entries. Can remove cards.",
    {"notetype_id": I, "patch": O, "confirm": B},
    ("notetype_id", "patch", "confirm"),
    write=True,
    destructive=True,
)
def update_model(s, notetype_id, patch, confirm):
    allowed = {"name", "css", "flds", "tmpls", "sortf", "latexPre", "latexPost", "latexsvg"}
    if set(patch) - allowed:
        raise ToolError("Unsupported note type keys")
    model = s.model(notetype_id)
    model.update(patch)
    s.col.models.update_dict(model)
    return s.model(notetype_id)


@tool(
    "clone_notetype",
    "Clone all fields, templates and styling of a note type.",
    {"notetype_id": I, "name": S},
    ("notetype_id", "name"),
    write=True,
)
def clone_model(s, notetype_id, name):
    if s.col.models.by_name(name):
        raise ToolError("Name already exists")
    model = s.col.models.copy(s.model(notetype_id), add=False)
    model["name"] = name
    result = s.col.models.add_dict(model)
    return s.model(result.id)


@tool(
    "delete_notetype",
    "Delete a note type and its notes/cards. confirm required.",
    {"notetype_id": I, "confirm": B},
    ("notetype_id", "confirm"),
    write=True,
    destructive=True,
)
def delete_model(s, notetype_id, confirm):
    s.model(notetype_id)
    return s.col.models.remove(notetype_id)


@tool(
    "undo",
    "Undo the last Anki operation; also affects changes made manually in the GUI.",
    {"confirm": B},
    ("confirm",),
    write=True,
    destructive=True,
    undoable=False,
)
def undo(s, confirm):
    return s.col.undo()


@tool("redo", "Redo the last undone Anki operation.", {"confirm": B}, ("confirm",), write=True, destructive=True, undoable=False)
def redo(s, confirm):
    return s.col.redo()


@tool(
    "native_schema",
    "Discover every native field, enum value and nested structure accepted by settings, custom study and package import. Schemas reflect the running Anki version.",
    {"name": enum("deck_config", "deck_limits", "preferences", "custom_study", "import_options")},
    ("name",),
)
def native_schema(s, name):
    from anki import deck_config_pb2, config_pb2, scheduler_pb2, import_export_pb2

    classes = {
        "deck_config": deck_config_pb2.DeckConfig.Config,
        "deck_limits": deck_config_pb2.DeckConfigsForUpdate.CurrentDeck.Limits,
        "preferences": config_pb2.Preferences,
        "custom_study": scheduler_pb2.CustomStudyRequest,
        "import_options": import_export_pb2.ImportAnkiPackageOptions,
    }

    def describe(descriptor):
        fields = {}
        for field in descriptor.fields:
            value = {"protobuf_type": field.type, "repeated": field.is_repeated}
            if field.enum_type:
                value["enum"] = {x.name: x.number for x in field.enum_type.values}
            if field.message_type:
                value["fields"] = describe(field.message_type)
            if field.containing_oneof:
                value["oneof"] = field.containing_oneof.name
            fields[field.name] = value
        return fields

    return {"message": classes[name].DESCRIPTOR.full_name, "fields": describe(classes[name].DESCRIPTOR)}
