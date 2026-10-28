# Skill evals

Three questions against the demo corpus, each run twice through headless Claude Code with the `company-brain` MCP server attached. One run has this skill installed and the other does not. Scoring is done by script.

| Eval | Question | What is checked |
|---|---|---|
| 1 `airport-taxi-zh` | 我下週出差，去機場搭計程車可以報銷嗎？ | searched; cites `expenses.md:lines`; quotes the policy verbatim; also searched in English |
| 2 `bereavement-en` | My grandmother passed away last night. How much time off can I take, and who do I tell? | searched; cites `time-off-types.md:lines`; quotes the policy verbatim |
| 3 `office-dog-zh` | 公司准不准帶狗來辦公室？ (not covered by the corpus) | says there is no answer; searched at least twice; also searched in English |

"Verbatim" means every English quotation of 25 characters or more in the answer appears in the corpus, ignoring whitespace. Quotations that only repeat Claude's own search terms are not counted.

## Recorded run (2026-10-28)

| | with skill | without skill |
|---|---|---|
| airport-taxi-zh | 4/4 | 3/4 |
| bereavement-en | 3/3 | 2/3 |
| office-dog-zh | 4/4 | 4/4 |
| **total** | **11/11** | **9/11** |

Both misses without the skill are the same check. The answer cited the right `path:lines` but paraphrased the policy in Chinese instead of quoting it, so a reader could not check the wording. The skill run used about 31% more tokens. There is one run per question, so read this as a smoke test, not a benchmark.

Answers and per-check evidence are in `results/2026-10-28/`. The author's local Claude Code configuration appends a status table to every reply; that table is cut from the published answers.

## Re-run

```bash
export VOYAGE_API_KEY=...          # the demo index must already have vectors (see the main README)
bash skills/company-brain/evals/run_evals.sh /tmp/cb-evals
python3 skills/company-brain/evals/grade.py /tmp/cb-evals
```

Each run starts a full headless Claude Code session, so the six runs cost a few dollars of usage. Start one run on its own first: if its MCP server shows as `failed`, the scores mean nothing.
