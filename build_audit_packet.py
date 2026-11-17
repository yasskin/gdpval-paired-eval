"""Build the local hand-audit packet for the 30-item failure ledger.

Writes audit/failure_audit.html (worksheet with prompt, criterion, judge reasons and links to
both models' files) and audit/failure_audit.csv (verdicts to fill in). Existing verdicts in the
CSV are preserved. Run build_site_plan.py afterwards to publish the audit results.
"""
import csv
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNS = ROOT / "gdpval-data" / "full_runs" / "2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d" / "runs"
TASKS = ROOT / "gdpval-data" / "full_grades" / "primary-v1" / "tasks"
LEDGER = HERE / "site" / "data" / "failure_ledger_draft.csv"
OUT = HERE / "audit"
AUDIT_CSV = OUT / "failure_audit.csv"
FIELDS = ["id", "model", "occupation", "criterion", "draft_class", "draft_severity",
          "verdict", "class", "severity", "notes"]
E = html.escape

runs = {}
for rj in RUNS.glob("*/run.json"):
    r = json.loads(rj.read_text(encoding="utf-8"))
    runs[(r["task_id"], r["provider"])] = (rj.parent, [a["path"] for a in r.get("artifacts") or []])

ledger = list(csv.DictReader(LEDGER.open(encoding="utf-8")))
OUT.mkdir(exist_ok=True)
previous = {}
if AUDIT_CSV.exists():
    previous = {r["id"]: r for r in csv.DictReader(AUDIT_CSV.open(encoding="utf-8"))}

rows, cards = [], []
for x in ledger:
    prev = previous.get(x["id"], {})
    rows.append({"id": x["id"], "model": x["model"], "occupation": x["occupation"], "criterion": x["criterion"],
                 "draft_class": x["class"], "draft_severity": x["severity"],
                 **{k: prev.get(k, "") for k in ("verdict", "class", "severity", "notes")}})
    prompt = (TASKS / x["task_id"] / "prompt.txt").read_text(encoding="utf-8").strip()
    links = []
    for prov, label in (("openai", "GPT"), ("anthropic", "Claude")):
        run_dir, files = runs.get((x["task_id"], prov), (None, []))
        items = "".join(f'<li><a href="{(run_dir / f).as_uri()}">{E(f)}</a></li>' for f in files) or "<li>No file</li>"
        answer = f' · <a href="{(run_dir / "answer.md").as_uri()}">final reply</a>' if run_dir and (run_dir / "answer.md").exists() else ""
        links.append(f"<div><b>{label}</b>{answer}<ul>{items}</ul></div>")
    done = f' <span class="done">{E(prev["verdict"])}</span>' if prev.get("verdict") else ""
    cards.append(f"""<section id="{x['id']}">
<h2>{x['id']} · {E(x['model'])} · {E(x['occupation'])}{done}</h2>
<p><b>Draft:</b> {E(x['class'])} · {E(x['severity'])}{' · ' + E(x['note']) if x['note'] else ''}</p>
<p><b>Required:</b> {E(x['required'])}<br><b>What went wrong:</b> {E(x['wrong'])}</p>
<p><b>Checklist item</b> (weight {E(x['weight'])}): {E(x['criterion'])}</p>
<details><summary>GPT judge's reason</summary><p>{E(x['gpt_judge_rationale'])}</p></details>
<details><summary>Claude judge's reason</summary><p>{E(x['claude_judge_rationale'])}</p></details>
<details><summary>Task prompt</summary><pre>{E(prompt)}</pre></details>
<div class="files">{''.join(links)}</div>
</section>""")

with AUDIT_CSV.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

checked = sum(bool(r["verdict"]) for r in rows)
(OUT / "failure_audit.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>Failure ledger hand audit</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:960px;margin:24px auto;padding:0 16px}}
section{{border:1px solid #ddd;border-radius:8px;padding:12px 16px;margin:16px 0}}h2{{font-size:1.05rem;margin:0 0 6px}}
pre{{white-space:pre-wrap;background:#f6f6f6;padding:8px}}.files{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.done{{background:#e6f4ea;color:#1a7f37;border-radius:999px;padding:1px 8px;font-size:.8rem}}</style>
<h1>Failure ledger hand audit ({checked} of {len(rows)} checked)</h1>
<p>For each item, open the failing model's file and check whether the judges were right. Record the result in
<code>{E(str(AUDIT_CSV))}</code>:</p>
<ul><li><b>verdict</b>: <code>confirmed</code> (the failure is real as drafted), <code>reclassified</code> (real, but a different
class or severity: fill in <b>class</b> and/or <b>severity</b>) or <code>rejected</code> (the file actually meets the item, or
the item is not a fair requirement).</li>
<li><b>notes</b>: one line of evidence, such as the page or cell you checked.</li></ul>
<p>Classes: Reference grounding, Quantitative reasoning, Domain judgment &amp; risk, Completeness, Format &amp; constraints,
Tool or modality limit, Grader / rubric defect. Severities: High, Medium, Low, Not a model failure.</p>
<p>Then run <code>uv run --no-project python build_site_plan.py</code> to update the site.</p>
{''.join(cards)}
""", encoding="utf-8")
print(f"wrote {OUT / 'failure_audit.html'} and {AUDIT_CSV}; {checked}/{len(rows)} already checked")
