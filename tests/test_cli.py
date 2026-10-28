from company_brain.cli import main


def test_cli_ingest_then_ask(tmp_path, kb, monkeypatch, capsys):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    db = str(tmp_path / "cli.db")
    assert main(["--db", db, "ingest", str(kb)]) == 0
    assert main(["--db", db, "ask", "sick leave"]) == 0
    out, err = capsys.readouterr()
    assert "leave.md:L" in out
    assert "VOYAGE_API_KEY not set" in err


def test_cli_no_match_exit_1(tmp_path, kb, monkeypatch, capsys):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    db = str(tmp_path / "cli.db")
    main(["--db", db, "ingest", str(kb)])
    assert main(["--db", db, "ask", "zzqqxx"]) == 1
    assert "No matching passages" in capsys.readouterr().out


def test_cli_ingest_bad_path_exit_2(tmp_path, capsys):
    assert main(["--db", str(tmp_path / "x.db"), "ingest", str(tmp_path / "typo")]) == 2
    assert "not a directory" in capsys.readouterr().err


def test_cli_ask_missing_db_exit_2(tmp_path, capsys):
    db = tmp_path / "missing.db"
    assert main(["--db", str(db), "ask", "anything"]) == 2
    assert "no index" in capsys.readouterr().err
    assert not db.exists()


def test_cli_mcp_missing_db_exit_2(tmp_path, capsys):
    assert main(["--db", str(tmp_path / "missing.db"), "mcp"]) == 2
    assert "no index" in capsys.readouterr().err


def test_cli_rejected_key_is_one_line(tmp_path, kb, monkeypatch, capsys):
    import urllib.error

    from company_brain import cli

    class RejectingEmbedder:
        def embed(self, texts, input_type):
            raise urllib.error.HTTPError("https://api.voyageai.com", 401, "Unauthorized", {}, None)

    monkeypatch.setattr(cli, "default_embedder", lambda: RejectingEmbedder())
    assert main(["--db", str(tmp_path / "k.db"), "ingest", str(kb)]) == 2
    err = capsys.readouterr().err
    assert "Voyage API rejected the request (HTTP 401)" in err
    assert "Traceback" not in err
