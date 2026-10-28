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
