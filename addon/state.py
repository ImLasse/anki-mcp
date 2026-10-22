"""Per-collection local metadata. Never opens Anki's SQLite database directly."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid
from .registry import ToolError


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


class Store:
    def __init__(self, root, collection_path):
        root = Path(root)
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        key = hashlib.sha256(str(Path(collection_path).resolve()).encode()).hexdigest()[:24]
        self.path = root / ("workspace-" + key + ".sqlite3")
        with self.db() as db:
            db.executescript("""
              create table if not exists objects(kind text not null,id text not null,data text not null,primary key(kind,id));
              create table if not exists journal(id text primary key,started text not null,finished text,tool text not null,
                status text not null,before_state text not null,after_state text,error_type text);
              create index if not exists journal_started on journal(started);
            """)
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def put(self, kind, data, object_id=None):
        object_id = object_id or uuid.uuid4().hex
        data = {**data, "id": object_id}
        with self.db() as db:
            db.execute("insert or replace into objects values(?,?,?)", (kind, object_id, json.dumps(data, ensure_ascii=False)))
        return data

    def get(self, kind, object_id):
        with self.db() as db:
            row = db.execute("select data from objects where kind=? and id=?", (kind, object_id)).fetchone()
        if not row:
            raise ToolError("Local " + kind + " record not found")
        return json.loads(row[0])

    def delete(self, kind, object_id):
        with self.db() as db:
            db.execute("delete from objects where kind=? and id=?", (kind, object_id))

    def objects(self, kind):
        with self.db() as db:
            rows = db.execute("select data from objects where kind=? order by id", (kind,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def begin(self, tool, before):
        entry_id = uuid.uuid4().hex
        with self.db() as db:
            db.execute(
                "insert into journal(id,started,tool,status,before_state) values(?,?,?,?,?)",
                (entry_id, now(), tool, "pending", self.encode_snapshot(before)),
            )
        return entry_id

    def finish(self, entry_id, after, error=None):
        with self.db() as db:
            db.execute(
                "update journal set finished=?,status=?,after_state=?,error_type=? where id=?",
                (
                    now(),
                    "failed_may_have_partial_effects" if error else "completed",
                    self.encode_snapshot(after),
                    type(error).__name__ if error else None,
                    entry_id,
                ),
            )

    @staticmethod
    def encode_snapshot(data):
        raw = json.dumps(data, ensure_ascii=False)
        if len(raw.encode()) > 2 * 1024 * 1024:
            return json.dumps({"truncated": True, "reason": "Snapshot exceeds 2 MiB; use collection backup for recovery"})
        return raw

    def history(self, offset=0, limit=100, entry_id=None):
        with self.db() as db:
            if entry_id:
                rows = db.execute("select * from journal where id=?", (entry_id,)).fetchall()
            else:
                rows = db.execute("select * from journal order by started desc,rowid desc limit ? offset ?", (limit, offset)).fetchall()
            total = db.execute("select count(*) from journal").fetchone()[0]
        items = []
        for row in rows:
            item = dict(zip(["id", "started", "finished", "tool", "status", "before", "after", "error_type"], row))
            if entry_id:
                item["before"] = json.loads(item["before"])
                item["after"] = json.loads(item["after"]) if item["after"] else None
            else:
                item.pop("before")
                item.pop("after")
            items.append(item)
        return {"items": items, "total": total, "next_offset": offset + limit if not entry_id and offset + limit < total else None}


def snapshot(s, name, args, result=None):
    """Bounded snapshots of explicit targets, not an automatic collection backup."""
    from .api import plain

    data = {"note_count": s.col.note_count(), "card_count": s.col.card_count()}
    if name == "apply_change_plan":
        plan = s.store.get("plan", args["plan_id"])
        data["operations"] = [snapshot(s, c["tool"], c["arguments"]) for c in plan["calls"]]
    nids = list(args.get("note_ids", [])) + [x["note_id"] for x in args.get("updates", [])]
    if name == "add_notes" and isinstance(result, list):
        nids += [x["id"] for x in result]
    cids = args.get("card_ids", []) or ([args["card_id"]] if args.get("card_id") else [])
    dids = list(args.get("deck_ids", [])) + ([args["deck_id"]] if args.get("deck_id") else [])
    for label, ids, getter in [
        ("notes", nids, lambda x: s.note_data(s.col.get_note(x))),
        ("cards", cids, lambda x: s.card_data(s.col.get_card(x))),
        ("decks", dids, s.deck),
    ]:
        if ids:
            unique = list(dict.fromkeys(ids))
            data[label] = {}
            for object_id in unique[:200]:
                try:
                    data[label][str(object_id)] = plain(getter(object_id))
                except Exception:
                    data[label][str(object_id)] = None
            if len(unique) > 200:
                data[label + "_truncated"] = True
    if name in ("set_deck_options", "assign_deck_preset", "update_deck") and args.get("deck_id"):
        try:
            data["deck_options"] = plain(s.col.decks.get_deck_configs_for_update(args["deck_id"]))
        except Exception:
            data["deck_options"] = None
        data["preset_assignments"] = {str(d["id"]): d.get("conf") for d in s.col.decks.get_all_legacy()}
    if args.get("notetype_id"):
        try:
            data["notetype"] = s.model(args["notetype_id"])
        except ToolError:
            data["notetype"] = None
    if args.get("filenames"):
        data["media"] = {}
        for filename in args["filenames"][:200]:
            path = s.file(filename, media=True)
            data["media"][filename] = {"exists": path.is_file(), "size": path.stat().st_size if path.is_file() else None}
    if args.get("source_id"):
        try:
            data["source"] = s.store.get("source", args["source_id"])
        except ToolError:
            data["source"] = None
    if name == "create_source" and isinstance(result, dict) and result.get("id"):
        data["source"] = result
    return data
