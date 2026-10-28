from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mcp.server.mcpserver import MCPServer

from .config import MAX_VEC_DISTANCE
from .search import search
from .store import connect

if TYPE_CHECKING:
    from .embed import Embedder

TOOL_DESCRIPTION = (
    "Search the company knowledge base. Returns verbatim passages with file:line citations. "
    "If the list is empty, tell the user the knowledge base has no answer; do not guess."
)


def build_server(db_path: Path, embedder: Embedder | None,
                 max_distance: float = MAX_VEC_DISTANCE) -> MCPServer:
    server = MCPServer("company-brain")

    @server.tool(name="search_company_knowledge", description=TOOL_DESCRIPTION)
    def search_company_knowledge(query: str, top: int = 5) -> list[dict]:
        # One connection per call: the server may run sync tools off the main thread.
        con = connect(db_path)
        try:
            hits = search(con, query, embedder, top=top, max_distance=max_distance)
        finally:
            con.close()
        return [{"path": h.path, "lines": f"{h.line_start}-{h.line_end}", "text": h.text}
                for h in hits]

    return server
