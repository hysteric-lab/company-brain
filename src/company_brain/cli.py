from __future__ import annotations

import argparse
import sys
import textwrap
import urllib.error
from pathlib import Path

from .embed import default_embedder
from .ingest import ingest
from .search import search
from .store import connect

NO_MATCH = "No matching passages in the knowledge base."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="brain", description=__doc__ or
                                     "Hybrid-search knowledge base with file:line citations.")
    parser.add_argument("--db", default="brain.db", help="SQLite file (default: ./brain.db)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_ingest = sub.add_parser("ingest", help="index .md/.txt files under DIR")
    p_ingest.add_argument("dir", type=Path)
    p_ask = sub.add_parser("ask", help="search the knowledge base")
    p_ask.add_argument("question")
    p_ask.add_argument("--top", type=int, default=5)
    sub.add_parser("mcp", help="serve the search tool over MCP (stdio)")
    args = parser.parse_args(argv)
    db = Path(args.db)
    if args.cmd in ("ask", "mcp") and not db.exists():
        # Opening a missing path would create an empty index and answer "no match".
        print(f"brain: no index at {db}; run `brain --db {db} ingest DIR` first", file=sys.stderr)
        return 2

    if args.cmd == "mcp":
        # stdout is the JSON-RPC channel from here on; diagnostics go to stderr only.
        from .mcp_server import build_server
        build_server(db.resolve(), default_embedder()).run("stdio")
        return 0

    con = connect(db)
    try:
        if args.cmd == "ingest":
            try:
                r = ingest(con, args.dir, default_embedder())
            except NotADirectoryError as e:
                print(f"brain: {e}", file=sys.stderr)
                return 2
            except urllib.error.HTTPError as e:
                print(f"brain: Voyage API rejected the request (HTTP {e.code}); "
                      "check VOYAGE_API_KEY", file=sys.stderr)
                return 2
            print(f"added={r.added} updated={r.updated} unchanged={r.unchanged} "
                  f"removed={r.removed} skipped={len(r.skipped)} embedded={r.embedded}")
            return 0
        hits = search(con, args.question, default_embedder(), top=args.top)
        if not hits:
            print(NO_MATCH)
            return 1
        for h in hits:
            print(f"{h.path}:L{h.line_start}-{h.line_end}")
            print(textwrap.indent(h.text.strip(), "    "))
            print()
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
