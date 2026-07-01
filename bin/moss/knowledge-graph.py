#!/usr/bin/env python3
"""
Moss Knowledge Graph (M1) — minimal Chroma wrapper.

Stores semantic memories for Moss: decisions, lessons, contacts, projects, code references.
Each entry is a chunk of text + structured metadata. Queryable by semantic similarity.

Usage:
  knowledge-graph.py add <type> <text> [--meta KEY=VAL ...]   # add a memory
  knowledge-graph.py search <query> [--type TYPE] [--k N]      # semantic search
  knowledge-graph.py list [--type TYPE] [--limit N]            # list all
  knowledge-graph.py stats                                    # count by type
  knowledge-graph.py forget <id>                               # delete by id

Storage: /root/.moss-private/knowledge/
Schema: id, type, text, metadata (json), ts

Types: decision, lesson, contact, project, code-ref, preference, fact
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

CHROMA_PATH = "/root/.moss-private/knowledge"
COLLECTION = "moss_memories"
STATE_FILE = "/root/.openclaw/workspace/moss-state.json"

VALID_TYPES = {"decision", "lesson", "contact", "project", "code-ref", "preference", "fact"}


def get_client():
    import chromadb
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection(client):
    return client.get_or_create_collection(
        name=COLLECTION,
        metadata={"description": "Moss long-term semantic memory"}
    )


def cmd_add(args):
    if args.type not in VALID_TYPES:
        print(f"ERROR: invalid type '{args.type}'. Valid: {sorted(VALID_TYPES)}", file=sys.stderr)
        sys.exit(1)
    meta = {"type": args.type, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for kv in args.meta or []:
        if "=" in kv:
            k, v = kv.split("=", 1)
            meta[k] = v
    client = get_client()
    coll = get_collection(client)
    rid = f"{args.type}-{int(time.time() * 1000)}"
    coll.add(ids=[rid], documents=[args.text], metadatas=[meta])
    # Also sync a brief note to moss-state.json
    try:
        state = json.loads(Path(STATE_FILE).read_text())
        if "knowledge_graph" not in state:
            state["knowledge_graph"] = {"last_entries": [], "stats": {}}
        state["knowledge_graph"]["last_entries"].append({
            "id": rid, "type": args.type, "ts": meta["ts"], "preview": args.text[:80]
        })
        state["knowledge_graph"]["last_entries"] = state["knowledge_graph"]["last_entries"][-50:]
        tmp = Path(STATE_FILE).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        tmp.replace(STATE_FILE)
    except Exception as e:
        print(f"warning: state sync failed: {e}", file=sys.stderr)
    print(f"added: {rid}  type={args.type}  text={args.text[:60]}{'...' if len(args.text) > 60 else ''}")


def cmd_search(args):
    client = get_client()
    coll = get_collection(client)
    where = {"type": args.type} if args.type else None
    res = coll.query(query_texts=[args.query], n_results=args.k, where=where)
    if not res or not res.get("ids"):
        print("(no matches)")
        return
    print(f"=== {len(res['ids'][0])} matches for: {args.query} ===")
    for i, (rid, doc, meta, dist) in enumerate(zip(
        res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
    ), 1):
        score = 1 - dist  # cosine distance → similarity
        print(f"\n{i}. [{meta.get('type', '?')}] {rid}  (sim={score:.2f})  {meta.get('ts', '')}")
        print(f"   {doc}")
        if "tags" in meta:
            print(f"   tags: {meta['tags']}")


def cmd_list(args):
    client = get_client()
    coll = get_collection(client)
    where = {"type": args.type} if args.type else None
    res = coll.get(where=where, limit=args.limit)
    if not res or not res.get("ids"):
        print("(empty)")
        return
    print(f"=== {len(res['ids'])} entries ===")
    for rid, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
        print(f"\n[{meta.get('type', '?')}] {rid}  {meta.get('ts', '')}")
        print(f"  {doc[:120]}{'...' if len(doc) > 120 else ''}")


def cmd_stats(args):
    client = get_client()
    coll = get_collection(client)
    total = coll.count()
    print(f"Total entries: {total}")
    if total == 0:
        return
    res = coll.get()
    counts = {}
    for meta in res["metadatas"]:
        t = meta.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    print("\nBy type:")
    for t, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {t:15s} {n}")


def cmd_forget(args):
    client = get_client()
    coll = get_collection(client)
    try:
        coll.delete(ids=[args.id])
        print(f"deleted: {args.id}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="Moss Knowledge Graph (M1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="add a memory")
    pa.add_argument("type", choices=sorted(VALID_TYPES))
    pa.add_argument("text", help="the memory text")
    pa.add_argument("--meta", nargs="*", help="KEY=VAL metadata")

    ps = sub.add_parser("search", help="semantic search")
    ps.add_argument("query")
    ps.add_argument("--type", choices=sorted(VALID_TYPES))
    ps.add_argument("--k", type=int, default=5)

    pl = sub.add_parser("list", help="list entries")
    pl.add_argument("--type", choices=sorted(VALID_TYPES))
    pl.add_argument("--limit", type=int, default=20)

    sub.add_parser("stats", help="show counts by type")

    pf = sub.add_parser("forget", help="delete by id")
    pf.add_argument("id")

    args = p.parse_args()
    {"add": cmd_add, "search": cmd_search, "list": cmd_list, "stats": cmd_stats, "forget": cmd_forget}[args.cmd](args)


if __name__ == "__main__":
    main()
