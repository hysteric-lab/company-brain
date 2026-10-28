# company-brain

Point it at a folder of company documents and ask questions in any language. It returns the matching passages verbatim, each with `file:line` citations, from the command line or to Claude over MCP.

## 30-second start

```bash
git clone https://github.com/hysteric-lab/company-brain && cd company-brain
python3 -m venv .venv && .venv/bin/pip install -e .
bash scripts/fetch_demo_corpus.sh                 # 4 pages of GitLab's public handbook
export VOYAGE_API_KEY=...                         # optional, see below
.venv/bin/brain --db demo.db ingest demo/corpus
.venv/bin/brain --db demo.db ask "員工請病假的規定是什麼？"
```

Needs Python 3.11+ whose `sqlite3` can load extensions (sqlite-vec is one). Homebrew's and uv's Pythons can; the python.org macOS installer cannot, and `brain` says so and names the fix. With uv: `uv venv --python-preference only-managed --python 3.12`.

`ask` prints each passage under a header like `people-group/time-off-and-absence/time-off-types.md:L129-148`. When nothing relevant is found, it prints `No matching passages in the knowledge base.` and exits with status 1.

## How it works

```
 .md / .txt files ──► ingest ──► SQLite file
                        │          ├─ documents  (path, sha256, text)
                        │          ├─ chunks     (1200 chars, 200 overlap, line_start/line_end)
                        │          ├─ chunks_fts (FTS5, trigram tokenizer: works for CJK too)
                        │          └─ vec_chunks (sqlite-vec, voyage-3.5-lite, 1024-d)
 question ──► FTS5 bm25 ─┐
          └─► vector KNN ─┴─► reciprocal-rank fusion (k=60) ─► top N passages + file:line
```

- **Re-ingest is incremental.** Files are compared by sha256. Changed files are re-chunked, deleted files lose their chunks and vectors, and unchanged files are skipped.
- **Missing vectors are backfilled.** Ingest first without a key, then run it again with one, and the chunks that have no vectors get embedded.
- **No key means FTS only.** Without `VOYAGE_API_KEY`, everything still works on full-text search alone, and stderr prints one line saying so.
- **"No answer" is a distance cut-off.** Vector hits farther than `MAX_VEC_DISTANCE` are dropped. The value in `src/company_brain/config.py` was calibrated on the demo corpus, and the measurements are recorded in that file. The gap between relevant and irrelevant questions was narrow, so recalibrate on your own documents.
- Non-UTF-8 files are skipped with a warning instead of aborting the run.

## Use it from Claude (MCP)

`brain mcp` serves one tool over stdio, `search_company_knowledge(query, top=5)`. It returns `[{path, lines, text}]`, and its description tells Claude to say "no answer" when the list is empty. The server does retrieval only: Claude writes the answer from the returned passages, so no Anthropic key is needed here.

```bash
claude mcp add company-brain -- "$PWD/.venv/bin/brain" --db "$PWD/demo.db" mcp
```

### Run record (2026-10-28, Claude Code, demo corpus)

Question asked: `GitLab 員工請病假要通知誰？用 company-brain 工具查，回答時引用檔案與行號。` ("Who must a GitLab employee notify when taking sick leave? Use the company-brain tool and cite file and line numbers.")

Claude called `search_company_knowledge` twice (`"sick leave who to notify"`, `"unable to work due to illness notify manager"`) and answered as follows. The answer is verbatim; a local status table that the author's own Claude Code configuration appends to every reply has been cut from the end.

> GitLab 員工請病假要先通知誰，看病假連續幾天：
>
> **連續 1–5 天：通知你的直屬主管。**
> `people-group/time-off-and-absence/time-off-types.md:129-148` 原文：
>
> > 1. Notify your manager of your absence. Please note that you do not need to disclose any medical information …
> > 1. Enter the time away in Workday by selecting the label "Out Sick"
>
> 通知主管之後，在 Workday 用「Out Sick」標籤登記這段時間，Time Off by Deel 會自動同步。少於 6 天不用交病假單，除非你所在國家的法規另有要求。
>
> **連續 6 天以上：算「留職停薪（leave of absence）」，通知對象看你在哪個國家。**
> `time-off-types.md:142-155`：
>
> - **美國**：透過 Okta 進入 Tilt 提交請假申請，大約 2–5 個工作天會排好你的個人請假計畫。
> - **其他國家**：在 Compass 開單通知 Absence Management Team（請假管理組），一樣要在 Workday 登記「Out Sick」，並依當地規定附上醫療證明，例如醫師證明或 fit note。
>
> **病情細節要不要講：** `time-off-types.md:161-179` 寫明，病情要跟主管和 People Business Partner（人資夥伴）講多少由你自己決定。如果你不想講，Absence Management Team 只會告訴主管請假日期，主管也不得把任何病情細節告訴其他同事。
>
> 另外有兩點：
>
> - 請假是為了照顧生病的家人時，適用 Caregiver Sick Time（照顧者病假）規定（`time-off-types.md:196-229`）。通知對象一樣，1–5 天找主管，6 天以上開 Compass 單。差別在 Workday 標籤要選「Caregiver Sick Time」。
> - 文件開頭註明：所在國家法定的通報規定永遠優先於上面這些流程（`time-off-types.md:129`）。

Check: lines 135–136 of `time-off-types.md` read `1. Notify your manager of your absence. …` and `1. Enter the time away in Workday by selecting the label "Out Sick"`.

## Tests

```bash
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q -m "not integration"            # offline: no network, no key
BRAIN_INTEGRATION=1 VOYAGE_API_KEY=... .venv/bin/pytest -q -m integration
```

The offline suite uses a deterministic bag-of-words embedder. It covers incremental re-ingest, backfill, FTS query escaping, CJK queries, empty results, citations that map back to file lines, the CLI, and the MCP tool. The integration suite asks Chinese questions against the English handbook and checks the expected page is in the top 3. It also checks that held-out off-topic questions return nothing; those questions were not used for calibration.

## Demo corpus

`scripts/fetch_demo_corpus.sh` downloads four pages from [GitLab's public handbook](https://gitlab.com/gitlab-com/content-sites/handbook) when you run it. They are not committed here: the handbook repository's LICENSE grants MIT for "the GitLab Software" and does not spell out terms for the handbook text, so this repo links to the source instead of redistributing it. All handbook content belongs to GitLab B.V.

## Licence

Apache-2.0 (this code). The demo corpus is not covered, see above.
