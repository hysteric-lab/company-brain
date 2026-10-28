import asyncio

from company_brain.ingest import ingest
from company_brain.mcp_server import build_server
from company_brain.store import connect


def make_server(tmp_path, kb):
    db = tmp_path / "mcp.db"
    con = connect(db)
    ingest(con, kb, None)
    con.close()
    return build_server(db, None, max_distance=1.2)


def test_mcp_tool_listed(tmp_path, kb):
    tools = asyncio.run(make_server(tmp_path, kb).list_tools())
    assert [t.name for t in tools] == ["search_company_knowledge"]


def test_mcp_tool_call(tmp_path, kb):
    server = make_server(tmp_path, kb)
    res = asyncio.run(server.call_tool("search_company_knowledge", {"query": "sick leave"}))
    assert not res.is_error
    assert res.structured_content["result"][0]["path"] == "leave.md"
