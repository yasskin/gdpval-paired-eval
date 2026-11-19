"""Build (and optionally serve) the hand-audit worksheet for the 30-item failure ledger.

    uv run --no-project python build_audit_packet.py           # write audit/failure_audit.html + .csv
    uv run --no-project python build_audit_packet.py --serve   # interactive worksheet that saves to the CSV

In --serve mode the worksheet runs on http://127.0.0.1 only. A card shows "Audit recorded"
after its verdict is saved to audit/failure_audit.csv. Notes save when you leave the field.
Saved cards move to the collapsed "Recorded audits" section when you leave the card.
Model files open through the local server and "Update the site" reruns build_site_plan.py.
Existing verdicts in the CSV are always preserved.
"""
import argparse
import csv
import html
import json
import mimetypes
import os
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNS = ROOT / "gdpval-data" / "full_runs" / "2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d" / "runs"
TASKS = ROOT / "gdpval-data" / "full_grades" / "primary-v1" / "tasks"
LEDGER = HERE / "site" / "data" / "failure_ledger.csv"
OUT = HERE / "audit"
AUDIT_CSV = OUT / "failure_audit.csv"
FIELDS = ["id", "model", "occupation", "criterion", "draft_class", "draft_severity",
          "verdict", "class", "severity", "notes"]
VERDICTS = ["confirmed", "reclassified", "rejected"]
CLASSES = ["Reference grounding", "Research & citations", "Quantitative reasoning", "Domain judgment & risk",
           "Completeness", "Format & constraints", "Tool or modality limit", "Grader / rubric defect"]
SEVERITIES = ["High", "Medium", "Low", "Not a model failure"]
TYPE_HELP = {
    "Reference grounding": "Misreads, contradicts, or fails to use information in a supplied source.",
    "Research & citations": "Uses weak or missing outside sources, or does not show where a claim came from.",
    "Quantitative reasoning": "Gets a number, calculation, or comparison wrong.",
    "Domain judgment & risk": "Makes a poor professional decision or misses an important risk.",
    "Completeness": "Leaves out something the task asked for.",
    "Format & constraints": "Does not follow the requested format or an explicit rule.",
    "Tool or modality limit": "Could not produce or inspect the requested kind of work because of a tool limitation.",
    "Grader / rubric defect": "The judge misread the evidence or the scoring rule does not fairly reflect the task.",
}
SEVERITY_HELP = {
    "High": "Could materially mislead a decision.",
    "Medium": "Needs correction before someone should use the deliverable.",
    "Low": "A minor or debatable issue that does not materially change how the work is used.",
    "Not a model failure": "Do not count this against the model.",
}
E = html.escape


def load():
    runs = {}
    for rj in RUNS.glob("*/run.json"):
        r = json.loads(rj.read_text(encoding="utf-8"))
        runs[(r["task_id"], r["provider"])] = (rj.parent, [a["path"] for a in r.get("artifacts") or []])
    ledger = list(csv.DictReader(LEDGER.open(encoding="utf-8")))
    previous = {r["id"]: r for r in csv.DictReader(AUDIT_CSV.open(encoding="utf-8"))} if AUDIT_CSV.exists() else {}
    rows = {}
    for x in ledger:
        prev = previous.get(x["id"], {})
        rows[x["id"]] = {"id": x["id"], "model": x["model"], "occupation": x["occupation"], "criterion": x["criterion"],
                         "draft_class": x["draft_class"], "draft_severity": x["draft_severity"],
                         **{k: prev.get(k, "") for k in ("verdict", "class", "severity", "notes")}}
    return ledger, runs, rows


def write_csv(rows):
    OUT.mkdir(exist_ok=True)
    tmp = AUDIT_CSV.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows.values())
    os.replace(tmp, AUDIT_CSV)


def options(values, selected, blank):
    opts = [f'<option value="">{E(blank)}</option>']
    opts += [f'<option{" selected" if v == selected else ""}>{E(v)}</option>' for v in values]
    return "".join(opts)


def render(ledger, runs, rows, served):
    def href(run_dir, name):
        if served:
            return f"/files/{quote(run_dir.name)}/{quote(name)}"
        return (run_dir / name).as_uri()

    pending_cards, recorded_cards = [], []
    for x in ledger:
        r = rows[x["id"]]
        draft_type, draft_severity = x["draft_class"], x["draft_severity"]
        model = x["model"]
        file_hint = ("Open both models' deliverables and check this same requirement in each. "
                     "If the two outcomes differ, leave the shared verdict blank and note what each file shows."
                     if model == "Both" else
                     f"Start with the {model} deliverable. Use the other model's file only as a comparison, not as the answer key.")
        prompt = (TASKS / x["task_id"] / "prompt.txt").read_text(encoding="utf-8").strip()
        links = []
        for prov, label in (("openai", "GPT"), ("anthropic", "Claude")):
            run_dir, files = runs.get((x["task_id"], prov), (None, []))
            items = "".join(f'<li><a target="_blank" href="{href(run_dir, f)}">{E(f)}</a></li>' for f in files) or "<li>No file</li>"
            answer = (f' · <a target="_blank" href="{href(run_dir, "answer.md")}">final reply</a>'
                      if run_dir and (run_dir / "answer.md").exists() else "")
            links.append(f"<div><b>{label}</b>{answer}<ul>{items}</ul></div>")
        radios = "".join(
            f'<label class="v-{v}"><input type="radio" name="verdict" value="{v}"{" checked" if r["verdict"] == v else ""}> {v.capitalize()}</label>'
            for v in VERDICTS)
        recl = r["verdict"] == "reclassified"
        recorded = r["verdict"].strip().lower() in VERDICTS
        state = "saved" if recorded else "waiting"
        badge = ("✓ Audit recorded" if recorded else
                 "Note saved · no verdict" if r["notes"] else "Not recorded yet")
        cards = recorded_cards if recorded else pending_cards
        cards.append(f"""<section id="{x['id']}" class="{'done' if recorded else ''}">
<div class="card-heading">
<h2>{x['id']} · {E(x['model'])} · {E(x['occupation'])}</h2>
<span class="audit-badge {state}">{badge}</span>
</div>
<p><b>1. What to check:</b> {E(x['required'])}<br>
<b>Exact scoring rule:</b> {E(x['criterion'])}</p>
<p><b>2. Where to look:</b> {E(file_hint)} Compare the file to the rule above; open the original task instructions below if the rule seems unclear or unfair.</p>
<div class="files">{''.join(links)}</div>
<details><summary>Original task instructions</summary><pre>{E(prompt)}</pre></details>
<details class="draft"><summary>Draft finding and AI judge explanations (not verified)</summary>
<p><b>Issue flagged in the ledger:</b> {E(x['wrong'])}{' · ' + E(x['note']) if x['note'] else ''}</p>
<details><summary>GPT judge's reason</summary><p>{E(x['gpt_judge_rationale'])}</p></details>
<details><summary>Claude judge's reason</summary><p>{E(x['claude_judge_rationale'])}</p></details>
</details>
<p class="draft"><b>Proposed issue type: {E(draft_type)}.</b> {E(TYPE_HELP[draft_type])}<br>
<b>Proposed severity: {E(draft_severity)}.</b> {E(SEVERITY_HELP[draft_severity])}</p>
<form class="verdict" data-id="{x['id']}" data-recorded="{str(recorded).lower()}" onsubmit="return false">
  <b>3. Record what you found</b>
  <div class="radios">{radios}<button type="button" class="clear">Clear</button></div>
  <div class="recl">
    <select aria-label="Issue type" name="class"{"" if recl else " disabled"}>{options(CLASSES, r['class'], 'Type: keep draft')}</select>
    <select aria-label="Severity" name="severity"{"" if recl else " disabled"}>{options(SEVERITIES, r['severity'], 'Severity: keep draft')}</select>
  </div>
  <input name="notes" placeholder="Evidence, e.g. 'p.2 table omits dosage column'" value="{E(r['notes'])}">
  <span class="status" role="status">{badge}</span>
  <button type="button" class="retry" hidden>Retry save</button>
</form>
</section>""")

    checked = sum(r["verdict"].strip().lower() in VERDICTS for r in rows.values())
    glossary = "".join(f"<dt><b>{E(label)}</b></dt><dd>{E(help_text)}</dd>"
                       for label, help_text in (*TYPE_HELP.items(), *SEVERITY_HELP.items()))
    mode = ('<p class="banner ok">Look for <b>✓ Audit recorded</b> on each card. It appears once the verdict is saved to '
            '<code>audit/failure_audit.csv</code>. Notes save when you leave the notes box. '
            'Saved cards move to <b>Recorded audits</b> at the bottom when you leave the card.</p>'
            if served else
            '<p class="banner warn">Read-only snapshot. Badges show what was saved when this copy was generated. To record new verdicts, run '
            '<code>uv run --no-project python build_audit_packet.py --serve</code> and use the page it opens.</p>')
    return f"""<!doctype html><meta charset="utf-8"><title>Failure ledger hand audit</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:980px;margin:0 auto;padding:0 16px 80px}}
header{{position:sticky;top:0;background:#fff;border-bottom:1px solid #ddd;padding:10px 0;z-index:2}}
header h1{{font-size:1.2rem;margin:0}}.bar{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:6px}}
.prog{{flex:1;min-width:160px;height:8px;background:#eee;border-radius:4px;overflow:hidden}}.prog span{{display:block;height:100%;background:#1a7f37}}
section{{border:1px solid #ddd;border-radius:8px;padding:12px 16px;margin:16px 0}}section.done{{border-left:6px solid #1a7f37}}
h2{{font-size:1.05rem;margin:0 0 6px}}pre{{white-space:pre-wrap;background:#f6f6f6;padding:8px}}
.files{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
form.verdict{{background:#f7f9fc;border-radius:6px;padding:10px;display:grid;gap:8px}}
.radios{{display:flex;gap:8px;flex-wrap:wrap}}.radios label{{border:1px solid #ccc;border-radius:999px;padding:3px 12px;cursor:pointer;background:#fff}}
.radios label:has(input:checked).v-confirmed{{background:#e6f4ea;border-color:#1a7f37}}
.radios label:has(input:checked).v-reclassified{{background:#fff4e5;border-color:#b26a00}}
.radios label:has(input:checked).v-rejected{{background:#fde8e8;border-color:#c62828}}
.recl{{display:flex;gap:8px;flex-wrap:wrap}}select:disabled{{opacity:.45}}input[name=notes]{{padding:6px;border:1px solid #ccc;border-radius:4px}}
.status{{font-size:.85rem;color:#555}}.status.err{{color:#c62828}}
.card-heading{{display:flex;align-items:baseline;justify-content:space-between;gap:8px;flex-wrap:wrap}}
.audit-badge{{font-size:.85rem;font-weight:650;border-radius:999px;padding:3px 10px;background:#eee;color:#333}}
.audit-badge.saved{{background:#e6f4ea;color:#14642e}}.audit-badge.pending{{background:#fff4e5;color:#774000}}
.audit-badge.err{{background:#fde8e8;color:#a21c1c}}
.banner{{padding:8px 12px;border-radius:6px}}.ok{{background:#e6f4ea}}.warn{{background:#fff4e5}}
.guide,.draft{{background:#f7f9fc;padding:10px 14px;border-radius:6px}}summary{{cursor:pointer}}
.guide li + li{{margin-top:5px}}section{{scroll-margin-top:100px}}
#recorded-audits{{margin-top:24px;padding:12px 14px;border:1px solid #ddd;border-radius:8px}}
#recorded-audits > summary{{font-weight:650}}
button{{cursor:pointer}}#rebuild-out{{white-space:pre-wrap;font-size:.85rem}}</style>
<header><h1>Failure ledger hand audit</h1>
<div class="bar"><b id="count">{checked} of {len(rows)} verdicts recorded</b><div class="prog"><span id="prog" style="width:{checked / len(rows) * 100:.0f}%"></span></div>
<button id="next" type="button">Next unrecorded ↓</button>{'<button id="rebuild" type="button">Update the site</button>' if served else ''}</div>
<div id="rebuild-out"></div></header>
{mode}
<aside class="guide">
<h2>Start here: check one requirement, not the whole task</h2>
<p>Each card asks you to verify one issue the AI judges flagged. The <b>draft</b> labels are suggestions made before a person checked the file. The issue type describes <em>what</em> went wrong; severity describes <em>how much it would matter</em> to someone using the work.</p>
<p><b>Example: G1, checking GPT's monthly costs.</b> The rule asks for a one-month cost estimate without insurance for each medication. Open GPT's deliverable, find the medication list, then look for an estimate next to each entry or in a separate cost table. You are checking whether estimates are present, not whether the prices are accurate. <b>Completeness</b> means something required may be missing; <b>Medium</b> means the draft reviewer thought it would need fixing before use. Neither label tells you what you will find.</p>
<h2>Which button should I choose?</h2>
<ul>
<li><b>Confirmed:</b> You found the problem, and the proposed type and severity fit.</li>
<li><b>Reclassified:</b> You found the problem, but would change its type or severity. If the scoring rule conflicts with the original instructions, choose <i>Grader / rubric defect</i> and <i>Not a model failure</i>.</li>
<li><b>Rejected:</b> The deliverable meets the requirement, despite the AI judges' fail call.</li>
<li><b>Not sure?</b> Leave the verdict blank (or click <b>Clear</b>). Note what blocked the check, then move on. An unreadable file or missing source is not proof of failure.</li>
</ul>
<p><b>Leave a breadcrumb:</b> Write one sentence with a page, section, or cell and what you saw. Example format: <i>“Page [X], cost table: [what is present or missing].”</i> Notes can appear in the report, so leave out private details.</p>
<details><summary>Guide to all issue types and severity levels</summary><dl>{glossary}</dl></details>
</aside>
<h2>To check</h2>
<p id="all-recorded"{' hidden' if pending_cards else ''}>All verdicts are recorded. Open <b>Recorded audits</b> below to revisit them.</p>
<div id="pending-cards">{''.join(pending_cards)}</div>
<details id="recorded-audits">
<summary>Recorded audits (<span id="recorded-count">{len(recorded_cards)}</span>)</summary>
<div id="recorded-cards">{''.join(recorded_cards)}</div>
</details>
<script>
const served = location.protocol.startsWith('http');
const forms = [...document.querySelectorAll('form.verdict')];
const saves = new Map();
const recorded = f => f.dataset.recorded === 'true';
const pendingCards = document.getElementById('pending-cards');
const recordedCards = document.getElementById('recorded-cards');
const next = document.getElementById('next');
function placeCard(f) {{
  const card = f.closest('section');
  const target = recorded(f) ? recordedCards : pendingCards;
  // Keep the current card visible while the reviewer is still working in it.
  if (card.parentElement !== target && !card.contains(document.activeElement)) target.append(card);
  document.getElementById('recorded-count').textContent = recordedCards.childElementCount;
  document.getElementById('all-recorded').hidden = pendingCards.childElementCount > 0;
}}
function refresh() {{
  const n = forms.filter(recorded).length;
  document.getElementById('count').textContent = n + ' of ' + forms.length + ' verdicts recorded';
  document.getElementById('prog').style.width = (n / forms.length * 100) + '%';
  next.disabled = n === forms.length;
}}
function show(f, state, badge, message = badge) {{
  const section = f.closest('section');
  const pill = section.querySelector('.audit-badge');
  pill.className = 'audit-badge ' + state;
  pill.textContent = badge;
  section.classList.toggle('done', state === 'saved');
  const status = f.querySelector('.status');
  status.className = state === 'err' ? 'status err' : 'status';
  status.textContent = message;
  f.querySelector('.retry').hidden = state !== 'err';
}}
function verdict(f) {{
  return f.querySelector('input[name=verdict]:checked')?.value || '';
}}
function sync(f) {{
  const v = verdict(f);
  f.querySelectorAll('select').forEach(s => {{ s.disabled = v !== 'reclassified'; if (s.disabled) s.value = ''; }});
}}
function save(f) {{
  const state = saves.get(f);
  const revision = ++state.revision;
  sync(f);
  const body = {{id: f.dataset.id, verdict: verdict(f),
    class: f.elements['class'].value, severity: f.elements['severity'].value, notes: f.elements['notes'].value}};
  if (body.verdict === 'reclassified' && !body.class && !body.severity) {{
    show(f, 'pending', 'Not saved yet', 'Pick a new type or severity to record this verdict.');
    return;
  }}
  show(f, 'pending', 'Saving…');
  state.queue = state.queue.then(async () => {{
    if (revision !== state.revision) return;
    try {{
      const r = await fetch('/save', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(body)}});
      if (!r.ok) throw new Error(await r.text());
      f.dataset.recorded = String(Boolean(body.verdict));
      refresh();
      if (revision !== state.revision) return;
      if (body.verdict) show(f, 'saved', '✓ Audit recorded', '✓ Audit recorded in the CSV.');
      else if (body.notes.trim()) show(f, 'waiting', 'Note saved · no verdict');
      else show(f, 'waiting', 'Not recorded yet', 'Saved without a verdict. This item is not counted as reviewed.');
      placeCard(f);
    }} catch (e) {{
      if (revision === state.revision) show(f, 'err', 'Save failed', 'Changes not confirmed: ' + e.message);
    }}
  }});
}}
forms.forEach(f => {{
  if (!served) {{
    for (const control of f.elements) control.disabled = true;
    return;
  }}
  const state = {{revision: 0, queue: Promise.resolve()}};
  saves.set(f, state);
  sync(f);
  const card = f.closest('section');
  card.addEventListener('focusout', () => {{
    setTimeout(() => {{
      if (['saved', 'waiting'].some(s => card.querySelector('.audit-badge').classList.contains(s))) placeCard(f);
    }}, 0);
  }});
  f.elements['notes'].addEventListener('input', () => {{
    ++state.revision;
    show(f, 'pending', 'Unsaved edits', 'Leave the notes box to save.');
  }});
  f.elements['notes'].addEventListener('blur', () => {{
    if (f.closest('section').querySelector('.audit-badge').textContent === 'Unsaved edits') save(f);
  }});
  f.addEventListener('change', () => save(f));
  f.querySelector('.retry').addEventListener('click', () => save(f));
  f.querySelector('.clear').addEventListener('click', () => {{
    f.querySelectorAll('input[name=verdict]').forEach(i => i.checked = false); save(f); }});
}});
next.addEventListener('click', () => {{
  const f = [...pendingCards.querySelectorAll('form.verdict')].find(f => !recorded(f));
  if (f) f.closest('section').scrollIntoView({{behavior: 'smooth'}});
}});
const rb = document.getElementById('rebuild');
if (rb) rb.addEventListener('click', async () => {{
  const out = document.getElementById('rebuild-out'); out.textContent = 'Rebuilding site…';
  const r = await fetch('/rebuild', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: '{{}}'}});
  out.textContent = (r.ok ? 'Site updated: ' : 'Rebuild failed: ') + await r.text();
}});
refresh();
</script>
"""


def build():
    ledger, runs, rows = load()
    write_csv(rows)
    OUT.mkdir(exist_ok=True)
    (OUT / "failure_audit.html").write_text(render(ledger, runs, rows, served=False), encoding="utf-8")
    checked = sum(bool(r["verdict"]) for r in rows.values())
    print(f"wrote {OUT / 'failure_audit.html'} and {AUDIT_CSV}; {checked}/{len(rows)} already checked")
    return ledger, runs, rows


def serve(port):
    ledger, runs, rows = build()
    host = f"127.0.0.1:{port}"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def reply(self, code, body, ctype="text/plain; charset=utf-8"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            if path in ("/", "/index.html"):
                return self.reply(200, render(ledger, runs, rows, served=True), "text/html; charset=utf-8")
            if path.startswith("/files/"):
                target = (RUNS / path[len("/files/"):]).resolve()
                if target.is_relative_to(RUNS.resolve()) and target.is_file():
                    ctype = "text/plain; charset=utf-8" if target.suffix == ".md" else (
                        mimetypes.guess_type(target.name)[0] or "application/octet-stream")
                    return self.reply(200, target.read_bytes(), ctype)
            self.reply(404, "not found")

        def do_POST(self):
            # Local-only guard: reject other hosts (DNS rebinding) and non-JSON cross-site form posts.
            if self.headers.get("Host") != host or self.headers.get("Content-Type") != "application/json":
                return self.reply(403, "forbidden")
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            path = urlparse(self.path).path
            if path == "/save":
                row = rows.get(body.get("id"))
                v, c, s = body.get("verdict", ""), body.get("class", ""), body.get("severity", "")
                if not row or v not in ("", *VERDICTS) or c not in ("", *CLASSES) or s not in ("", *SEVERITIES):
                    return self.reply(400, "invalid value")
                updated = dict(row, verdict=v, notes=str(body.get("notes", "")).strip(),
                               **({"class": c, "severity": s} if v == "reclassified" else {"class": "", "severity": ""}))
                try:
                    write_csv({**rows, row["id"]: updated})
                except OSError as exc:
                    self.log_error("Could not save audit CSV: %s", exc)
                    return self.reply(500, "Could not write the audit CSV. Close it in Excel if open and retry.")
                rows[row["id"]] = updated
                return self.reply(200, "ok")
            if path == "/rebuild":
                p = subprocess.run([sys.executable, str(HERE / "build_site_plan.py")], cwd=HERE,
                                   capture_output=True, text=True, encoding="utf-8")
                return self.reply(200 if p.returncode == 0 else 500, (p.stdout + p.stderr).strip())
            self.reply(404, "not found")

    server = HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://{host}/"
    print(f"Hand-audit worksheet: {url}  (Ctrl+C to stop; verdicts save to {AUDIT_CSV})")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        build()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true", help="serve an interactive worksheet that saves to the CSV")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    serve(args.port) if args.serve else build()
