"""Grade company-brain skill eval runs by script.

Usage: python3 grade.py OUT_DIR   (OUT_DIR as written by run_evals.sh)
Writes grading.json and outputs/answer.md into each run-1/ and prints a summary.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CORPUS = REPO / "demo" / "corpus"
NAMES = {e["id"]: e["name"] for e in json.load(open(Path(__file__).with_name("evals.json")))["evals"]}
norm = lambda s: re.sub(r"\s+", " ", s)
corpus = norm("\n".join(p.read_text(encoding="utf-8") for p in CORPUS.rglob("*.md")))


def parse(run_json):
    queries, answer = [], ""
    for m in json.load(open(run_json)):
        if m.get("type") == "assistant":
            for c in m["message"]["content"]:
                if c.get("type") == "tool_use" and c["name"].endswith("search_company_knowledge"):
                    queries.append(c["input"].get("query", ""))
        if m.get("type") == "result":
            answer = m.get("result") or ""
    return queries, answer


def verbatim_quotes(answer, queries):
    """English quotations (>= 25 chars, quoted or blockquoted) must all occur in the corpus.
    Echoes of Claude's own search queries are not quotations and are ignored."""
    spans = re.findall(r'["“]([A-Za-z][^"”]{25,}?)["”]', answer)
    spans += [l.lstrip("> ") for l in answer.splitlines()
              if l.startswith(">") and re.search(r"[A-Za-z]{4,}", l) and len(l) > 30]
    clean = lambda s: re.split(r'["”]\s*[—-]|\s+[—-]\s+`', s)[0].strip(' "“”.…*')
    words = lambda s: set(re.findall(r"\w+", s.lower()))
    echoes_query = lambda s: any(words(s) <= words(q) for q in queries)
    spans = [c for c in (clean(s) for s in spans) if len(c) >= 25 and not echoes_query(c)]
    if not spans:
        return False, "no English quotation found"
    missing = [s for s in spans if norm(s.split("…")[0].strip())[:60] not in corpus]
    return not missing, f"{len(spans)} quoted spans, {len(missing)} not found in corpus: {missing[:2]}"


def grade(name, run_dir):
    queries, answer = parse(run_dir / "outputs" / "run.json")
    checks = []
    add = lambda text, ok, ev: checks.append({"text": text, "passed": bool(ok), "evidence": ev})
    english_query = any(re.search(r"[A-Za-z]{3,}", q) for q in queries)
    add("Called search_company_knowledge at least once", queries, f"queries={queries}")
    if name == "airport-taxi-zh":
        cites = re.findall(r"expenses\.md:L?\d+-\d+", answer)
        add("Cites finance/expenses.md with path:lines", cites, f"citations={cites}")
        add("Quotes the policy text verbatim (quote found in corpus)", *verbatim_quotes(answer, queries))
        add("Ran an English-language query for a Chinese question", english_query, f"queries={queries}")
    elif name == "bereavement-en":
        cites = re.findall(r"time-off-types\.md:L?\d+-\d+", answer)
        add("Cites time-off-types.md with path:lines", cites, f"citations={cites}")
        add("Quotes the policy text verbatim (quote found in corpus)", *verbatim_quotes(answer, queries))
    elif name == "office-dog-zh":
        no = re.search(r"(沒有|找不到|查不到|未提及|沒提到|no (relevant|answer|mention))", answer)
        add("States the knowledge base has no answer", no, answer[:200])
        add("Searched at least twice before giving up", len(queries) >= 2, f"{len(queries)} queries")
        add("Ran an English-language query for a Chinese question", english_query, f"queries={queries}")
    passed = sum(c["passed"] for c in checks)
    result = {"expectations": checks,
              "summary": {"passed": passed, "failed": len(checks) - passed, "total": len(checks),
                          "pass_rate": round(passed / len(checks), 3)}}
    json.dump(result, open(run_dir / "grading.json", "w"), ensure_ascii=False, indent=1)
    (run_dir / "outputs" / "answer.md").write_text(answer, encoding="utf-8")
    return result


if __name__ == "__main__":
    out = Path(sys.argv[1])
    totals = {}
    for ev in sorted(out.glob("eval-*")):
        name = NAMES[int(ev.name.split("-")[1])]
        for cfg in ("with_skill", "without_skill"):
            run = ev / cfg / "run-1"
            if (run / "outputs" / "run.json").exists():
                s = grade(name, run)["summary"]
                totals.setdefault(cfg, [0, 0])
                totals[cfg][0] += s["passed"]
                totals[cfg][1] += s["total"]
                print(f"{name:16} {cfg:14} {s['passed']}/{s['total']}")
    for cfg, (p, t) in totals.items():
        print(f"TOTAL {cfg:14} {p}/{t}")
