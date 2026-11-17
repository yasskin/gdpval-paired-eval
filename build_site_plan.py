"""Build failures.html and data.html from plan_items.json and the frozen run records. No inference."""

import csv
import html
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
D = json.loads((HERE / "plan_items.json").read_text(encoding="utf-8"))
E = html.escape

NAV = [
    ("index.html", "Overview", ""),
    ("tasks.html", "GDPval gold tasks", ""),
    ("sectors.html", "By sector", ""),
    ("gpt.html", "For OpenAI (GPT)", "gpt"),
    ("claude.html", "For Anthropic (Claude)", "claude"),
    ("failures.html", "Failures", ""),
    ("example.html", "Worked example", ""),
    ("methods.html", "Methods &amp; limits", ""),
    ("data.html", "Data &amp; code", ""),
    ("glossary.html", "Glossary", ""),
]


def page(fname, title, subtitle, body):
    links = []
    for href, text, cls in NAV:
        c = f' class="{cls}"' if cls else ""
        cur = ' aria-current="page"' if href == fname else ""
        links.append(f'      <a{c} href="{href}"{cur}>{text}</a>')
    nav = "\n".join(links)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · GDPval Paired Evaluation</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <div class="brand">GDPval Paired Evaluation<small>{subtitle}</small></div>
    <nav class="tabs" aria-label="Sections">
{nav}
    </nav>
  </div>
</header>

<main class="wrap">
{body}
</main>

<footer class="site"><div class="wrap">Provisional results. <a href="methods.html">Methods and limitations</a>.</div></footer>
</body>
</html>
"""


# ---------------------------------------------------------------- failure ledger (draft)
# Keyed by candidate list and index in plan_items.json; the criterion prefix guards against reordering.
# (class, severity, required, what went wrong, note)
GR, CI, QR, CA, DJ, CO, TM, GH = (
    "Reference grounding", "Research & citations", "Quantitative reasoning", "Format & constraints",
    "Domain judgment & risk", "Completeness", "Tool or modality limit", "Grader / rubric defect")
REVIEW = {
    "openai": [
        (0, "An estimated one-month cost", CO, "Medium", "A one-month uninsured cost for every medication in a formulary", "Costs missing for almost every medication", ""),
        (1, "The Word document contains all items", GR, "Medium", "Carry every column of a source checklist PDF into a Word version", "Items copied, but the per-item details from the PDF were dropped", ""),
        (6, "All survey questions are answerable", CA, "Low", "A Yes/No-only survey with no free-text fields", "Added a fill-in blank on both pages", "Cosmetic; easy to fix"),
        (8, "The itinerary includes all destinations", CO, "Medium", "A yacht itinerary covering six named islands", "Three of the six destinations are not stops", ""),
        (12, "Includes a brief interpretation of the 20", DJ, "High", "Interpret a heat map, including whether any hotspot is within 10 °C of a 150 °C limit", "No interpretation of the safety margin", "Safety-relevant engineering conclusion left out"),
        (13, "Confirms in the report that the provided photographs", DJ, "Medium", "Confirm that surveillance photos match the logged events", "The report declines to confirm the match", "Debatable: caution can be professionally defensible"),
        (15, "The memorandum concludes that Marcus", DJ, "High", "Conclude that a shareholder veto right is facially enforceable under Delaware law", "Treats the charter clause as an obstacle, the opposite conclusion", "Wrong legal bottom line"),
        (18, "States that the additional deposit becomes nonrefundable", DJ, "High", "Letter of intent states when the extra deposit becomes nonrefundable", "Key deal term deferred instead of stated", "Money-at-risk term missing from a deal document"),
        (19, "The Monthly section includes reviewing staff schedule", DJ, "Medium", "Monthly check of the pharmacist-to-technician ratio under California rules", "Cites the regulation but never schedules the check", ""),
        (20, "Dr. Jane Joe", CO, "Medium", "Travel plan that gets the doctor back to Chicago by 3 pm, with arrival time shown", "No arrival time documented", ""),
        (23, "For each project, the report states whether the IRR", QR, "High", "Say only whether each project's return is above or below 9%, without inventing numbers", "Reports precise returns calculated from invented cash flows", "Fabricated precision a board could act on"),
        (26, "Difference vs. Juvoxa Optics", QR, "Medium", "Report one supplier's cost difference versus another (₹769.56 million)", "The required comparison figure is missing", ""),
    ],
    "anthropic": [
        (0, "Overall formatting and style", CA, "Low", "A polished, client-ready luxury itinerary", "Missing images and large empty areas", "Presentation only"),
        (3, "The memorandum concludes that there is a substantial risk", DJ, "High", "Conclude that the board likely breached its duty of loyalty", "Lists risks but never reaches the required conclusion", "Hedged legal advice"),
        (5, "For each conversion year", QR, "Medium", "Calculate conversion tax at a flat 35% marginal rate", "Used a bracket-filling method instead", "Debatable: the alternative method may be more realistic"),
        (6, "Schedules carpet cleaning in M2", GR, "Medium", "Schedule carpet cleaning before staff work in unit M2", "Scheduled it after staff work", "Ignores an ordering constraint in the inputs"),
        (8, "For every list item, the original statement", GR, "High", "Quote real agent statements from the support case file", "Quoted a customer line and claimed an agent message was missing when it exists", "Misstates the record being reviewed"),
        (9, "Provides PMP", CO, "Medium", "Phase 1 covers local assembly of vehicles, battery packs and motor controllers", "Vehicles and motor controllers left out", ""),
        (10, "Sum of quarterly shipments", QR, "Low", "Year-1 shipments total $225,000", "Totals $255,000; Claude flagged the brief as inconsistent", "Possibly a rubric problem, not a model error"),
        (12, "In Omni (Last Year)", CA, "Low", "Totals computed with formulas that sum the channel cells", "Numerically correct, but not built the required way", "Noise: same numbers"),
        (15, "Total Investment Difference vs. Juvoxa", QR, "Medium", "Report one supplier's investment difference (₹294.39 million)", "The required figure is never stated", ""),
        (21, "For the infection", DJ, "Medium", "Nursing care plan includes ordering lab tests for infection risk", "That intervention is missing", ""),
        (27, "States in the Court Documentation subsection", GR, "High", "Court case number PT-2025-1782", "Wrote DV-2025-1782, the wrong case number", "Wrong legal identifier in a case file"),
        (29, "The comparative table includes a column", QR, "Medium", "Revenue difference defined as 100-day minus 90-day", "Defined the other way round, so signs are flipped", ""),
    ],
    "shared": [
        (3, "The total available inventory", QR, "High", "Inventory coverage = total supply ÷ expected sales", "Both models subtracted demand from supply", "Same error in both: the prompt may be ambiguous"),
        (9, "Excel workbook includes tab", CO, "Medium", "Workbook includes an 'Exercise of Rights' tab", "Neither model created it", ""),
        (6, "Includes a map of the area", TM, "Medium", "A map for each property listing", "Neither model included maps", "Needs map tools, not just data"),
        (10, "Each day section includes at least one photo", TM, "Low", "One photo per itinerary day", "Neither model included photos", "Needs image tools"),
        (5, "Submission is provided as a single PDF", GH, "Not a model failure", "Checklist demands a PDF", "The task itself asked for a Word file", "The checklist contradicts the task"),
        (8, "Includes the firm's phone number", GH, "Not a model failure", "Checklist demands a specific phone number", "Both used the number the task gave", "The checklist contradicts the task"),
    ],
}
WHO = {"openai": "GPT", "anthropic": "Claude", "shared": "Both"}
SEV_CLS = {"High": "sev-high", "Medium": "sev-med", "Low": "sev-low", "Not a model failure": "sev-na"}

ledger = []
for model, items in REVIEW.items():
    pool = D["candidates"][model]
    for idx, prefix, cls, sev, req, wrong, note in items:
        c = pool[idx]
        assert c["criterion"].startswith(prefix), (model, idx, c["criterion"][:60])
        ledger.append({"model": WHO[model], "occupation": c["occupation"], "sector": c["sector"],
                       "task_id": c["task_id"], "run_id": c["run_id"], "rubric_item_id": c["rubric_item_id"],
                       "weight": c["weight"], "criterion": c["criterion"], "required": req, "wrong": wrong,
                       "class": cls, "severity": sev, "note": note,
                       "gpt_judge_rationale": (c["gpt_judge"] or [""])[0],
                       "claude_judge_rationale": (c["claude_judge"] or [""])[0],
                       "review_status": "draft: classified from both judges' evidence; artifact re-check pending"})
assert len(ledger) == 30

(SITE / "data").mkdir(exist_ok=True)
with (SITE / "data" / "failure_ledger_draft.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ledger[0]))
    w.writeheader()
    w.writerows(ledger)

pool = D["candidate_pool"]
matrix = list(csv.DictReader((SITE / "data" / "status_matrix.csv").open(encoding="utf-8")))
both_delivered = sum(r["gpt_status"] == "completed" and int(r["gpt_files"]) > 0
                     and r["claude_status"] == "completed" and int(r["claude_files"]) > 0 for r in matrix)
sev_counts = Counter(x["severity"] for x in ledger)


def ledger_table(model):
    rows = []
    for x in [x for x in ledger if x["model"] == model]:
        note = f'<div class="pnote" style="white-space:normal">{E(x["note"])}</div>' if x["note"] else ""
        rows.append(f"""        <tr><td>{E(x['occupation'])}<div class="pnote"><code>{x['task_id'][:8]}</code></div></td>
          <td>{E(x['required'])}</td><td>{E(x['wrong'])}{note}</td>
          <td>{E(x['class'])}</td><td><span class="sev {SEV_CLS[x['severity']]}">{E(x['severity'])}</span></td></tr>""")
    return "\n".join(rows)


cls_order = [GR, QR, DJ, CO, CA, TM, GH]
cls_counts = {k: Counter(x["model"] for x in ledger if x["class"] == k) for k in cls_order}
cls_rows = "\n".join(
    f'        <tr><td>{E(k)}</td><td class="n">{v["GPT"] or "–"}</td><td class="n">{v["Claude"] or "–"}</td><td class="n">{v["Both"] or "–"}</td></tr>'
    for k, v in cls_counts.items())

DELIVERY = [
    ("Ran out of its 50,000-token writing budget mid-task", 0, 33, "Model + limits", "yes", "Claude spent its budget exploring before writing the file."),
    ("Final reply cut off before it finished", 0, 14, "Model + limits", "yes", "The answer was too long for one reply."),
    ("Used all 14 turns while still working", 3, 15, "Model + limits", "yes", "Still working when the turn limit hit."),
    ("Used all 24 tool calls, then wrote the content as chat text instead of a file", 0, 13, "Model", "yes", "The most actionable: the work existed but the save step never ran."),
    ("Web-search request cut off; our software could not read it", 3, 0, "Model + harness", "partly", "Shorter requests or better error recovery would fix it."),
    ("Requested video not produced", 1, 0, "Tool limit", "partly", "GPT said it could not export video; not independently checked."),
    ("OpenAI server timed out", 2, 0, "Provider", "no", "Network noise; says nothing about the model."),
    ("Content filter returned an empty answer", 0, 1, "Provider / serving", "no", "An operations issue, not a training-data gap."),
]
MATTERS = {"yes": '<span class="badge gpt">Yes</span>', "partly": '<span class="badge weak">Partly</span>',
           "no": '<span class="badge even">No, noise</span>'}
deliv_rows = "\n".join(
    f'        <tr><td>{E(a)}<div class="pnote" style="white-space:normal">{E(note)}</div></td><td class="n">{g or "–"}</td><td class="n">{c or "–"}</td><td>{E(who)}</td><td>{MATTERS[m]}</td></tr>'
    for a, g, c, who, m, note in DELIVERY)

failures = f"""  <h1>What went wrong, and which failures matter</h1>
  <p class="lede">A failure taxonomy sorts mistakes into types so a researcher can see which are worth fixing with data and which are noise. We split failures into two kinds: tasks where no usable file was produced, and errors inside files that were handed in.</p>

  <div class="plain">
    <strong>In plain English</strong>
    <p>Not every failure says something about the model. A server timeout is noise. A checklist that contradicts its own task is a grading problem. A model that runs out of room before saving its work, or confidently writes the wrong case number, is a real gap a dataset could target. Each failure below is labeled with who or what was responsible and whether it matters to a researcher.</p>
  </div>

  <div class="grid">
    <div class="stat claude"><div class="num">85</div><div class="label">tasks with no usable file (9 GPT, 76 Claude), all classified</div></div>
    <div class="stat"><div class="num">30</div><div class="label">errors inside delivered files, classified in a draft ledger</div></div>
    <div class="stat"><div class="num">{sev_counts['High']}</div><div class="label">of the 30 rated high severity (could mislead a decision)</div></div>
    <div class="stat"><div class="num">{sev_counts['Not a model failure'] + sum(1 for x in ledger if 'Noise' in x['note'] or 'rubric problem' in x['note'])}</div><div class="label">of the 30 are grading problems or noise, not model weaknesses</div></div>
  </div>

  <h2>Part A: tasks that produced no usable file (85 of 440 attempts)</h2>
  <p class="howto">each row is one cause. "Matters?" asks whether the failure tells a researcher something about the model that better data could fix. Every one of the 85 attempts was checked against its saved run records.</p>
  <div class="table-wrap">
    <table class="numbers">
      <thead><tr><th>What happened</th><th class="n">GPT</th><th class="n">Claude</th><th>Responsible</th><th>Matters?</th></tr></thead>
      <tbody>
{deliv_rows}
        <tr><td><strong>Total</strong></td><td class="n"><strong>9</strong></td><td class="n"><strong>76</strong></td><td></td><td></td></tr>
      </tbody>
    </table>
  </div>
  <p class="note">Nine of these attempts left partial files (1 GPT, 8 Claude). Limits were identical for both models: 14 turns, 24 tool calls and 50,000 written tokens per task. In a separate follow-up with larger limits, 53 of 62 cut-off Claude tasks produced a file (<a href="claude.html">details</a>).</p>

  <h2>Part B: errors inside delivered files (draft ledger of 30)</h2>
  <div class="callout"><strong>Status: draft.</strong> Each item was classified from both AI judges' cited evidence. A human re-check of each item against the original file is still pending, so treat severities as provisional. <a href="data/failure_ledger_draft.csv">Download the full ledger (CSV)</a> with task, run and checklist-item IDs and both judges' reasoning.</div>
  <h3>How the 30 were chosen</h3>
  <ol class="steps">
    <li><strong>Start from agreement</strong>Only checklist items that <em>both</em> judges failed. One judge alone is not enough.</li>
    <li><strong>Find contrasts</strong>On the {both_delivered} tasks where both models delivered a file: {pool.get('openai', 0)} tasks where both judges failed an item for GPT and passed it for Claude, {pool.get('anthropic', 0)} the reverse, and {pool.get('shared', 0)} where both failed.</li>
    <li><strong>Prioritize weight</strong>Highest-weight item per task, so the errors that cost the most points come first.</li>
    <li><strong>Spread and label</strong>Picked 12 GPT, 12 Claude and 6 shared items across occupations, then labeled each one's type and severity.</li>
  </ol>
  <p class="note">Those counts compare the two models on the same tasks, but they do not include judge self-preference or unverifiable items, so read them as a direction, not a rate.</p>

  <h3>Types of error, by model</h3>
  <div class="table-wrap">
    <table class="numbers" style="max-width:620px">
      <thead><tr><th>Error type</th><th class="n">GPT</th><th class="n">Claude</th><th class="n">Both</th></tr></thead>
      <tbody>
{cls_rows}
      </tbody>
    </table>
  </div>
  <p class="legend"><span><span class="sev sev-high">High</span> could mislead a decision</span><span><span class="sev sev-med">Medium</span> needs rework before use</span><span><span class="sev sev-low">Low</span> cosmetic or debatable</span><span><span class="sev sev-na">Not a model failure</span> grading problem</span></p>

  <h3>GPT-6 Astra: 12 errors</h3>
  <div class="table-wrap"><table class="numbers ledger">
      <thead><tr><th>Occupation</th><th>The checklist required</th><th>What went wrong</th><th>Type</th><th>Severity</th></tr></thead>
      <tbody>
{ledger_table('GPT')}
      </tbody></table></div>

  <h3>Claude Opus 5.5: 12 errors</h3>
  <div class="table-wrap"><table class="numbers ledger">
      <thead><tr><th>Occupation</th><th>The checklist required</th><th>What went wrong</th><th>Type</th><th>Severity</th></tr></thead>
      <tbody>
{ledger_table('Claude')}
      </tbody></table></div>

  <h3>Both models: 6 shared failures</h3>
  <div class="table-wrap"><table class="numbers ledger">
      <thead><tr><th>Occupation</th><th>The checklist required</th><th>What went wrong</th><th>Type</th><th>Severity</th></tr></thead>
      <tbody>
{ledger_table('Both')}
      </tbody></table></div>

  <h2>Three patterns worth building data for</h2>
  <div class="pair">
    <div class="card claude">
      <h3>1. Claude runs out of room before saving the file</h3>
      <p><strong>Evidence:</strong> 76 of 220 tasks without a usable file; 13 used every tool call and then pasted the content as chat text. With larger limits, 53 of 62 cut-off tasks delivered.</p>
      <p><strong>Other explanation:</strong> the limits may simply be tight for Claude's default reasoning. The retry shows budget sensitivity, not a single cause.</p>
      <p><strong>Data that could help:</strong> worked examples that save a first draft early and then improve it, under explicit budgets.</p>
      <p style="margin-bottom:0"><strong>Follow-up test:</strong> rerun the 76 tasks at the same limits; count files and grade them.</p>
    </div>
    <div class="card gpt">
      <h3>2. GPT's files look finished but miss specific requirements</h3>
      <p><strong>Evidence:</strong> on {both_delivered} tasks where both delivered, both judges failed a GPT checklist item that they passed for Claude on {pool.get('openai', 0)} tasks, versus {pool.get('anthropic', 0)} the other way. Examples above include a wrong legal conclusion, invented return figures and a missing safety margin.</p>
      <p><strong>Other explanation:</strong> GPT ran with a low reasoning setting, and judges may prefer their own model's style.</p>
      <p><strong>Data that could help:</strong> requirement-dense tasks with item-by-item expert checklists and near-miss files paired with corrections.</p>
      <p style="margin-bottom:0"><strong>Follow-up test:</strong> new held-out tasks scored by experts on critical omissions.</p>
    </div>
  </div>
  <div class="card">
    <h3>3. Both: the grading itself is a gap, so evaluation data has value too</h3>
    <p><strong>Evidence:</strong> judges could not verify 24.3% of checklist items, including 98% of items on PowerPoint files. Two of the 30 ledger items are checklists that contradict their own task. Both models also failed the same items on {pool.get('shared', 0)} tasks, often ones needing maps, photos or careful formulas.</p>
    <p style="margin-bottom:0"><strong>Data that could help:</strong> rendered gold-standard files, machine-checkable acceptance tests and audited checklists. These make an evaluation trustworthy for <em>both</em> labs before any training claim. See <a href="methods.html#judges">Can we trust the judges?</a></p>
  </div>
  <p class="note">These patterns come from one try per task and AI grading. They suggest where data might help; they do not show that training on such data would improve either model.</p>
"""

# ---------------------------------------------------------------- data & code page
status_label = {"completed": "Finished", "incomplete": "Cut off", "provider_error": "Server error", "harness_error": "Harness error"}


def st(status, files):
    files = int(files)
    s = status_label.get(status, status)
    cls = "v-pass" if status == "completed" and files else "v-fail"
    return f'<td class="{cls}">{s} · {files} file{"s" if files != 1 else ""}</td>'


JUDGE_CLS = {"GPT better": "wg", "Claude better": "wc"}
mrows = "\n".join(
    f'        <tr><td>{E(r["occupation"])}<div class="pnote"><code>{r["task_id"][:8]}</code></div></td>{st(r["gpt_status"], r["gpt_files"])}{st(r["claude_status"], r["claude_files"])}'
    f'<td class="{JUDGE_CLS.get(r["gpt_judge"], "")}">{r["gpt_judge"]}</td><td class="{JUDGE_CLS.get(r["claude_judge"], "")}">{r["claude_judge"]}</td></tr>'
    for r in matrix)

data_page = f"""  <h1>Data and code: how to check our work</h1>
  <p class="lede">Every number on this site comes from saved run records. This page lists what was frozen before running, the checks that passed, the code that produced the results and the status of all 440 attempts.</p>

  <div class="plain">
    <strong>In plain English</strong>
    <p>A trustworthy evaluation is one someone else can re-check. We fixed the settings before running, recorded a fingerprint (a <a class="term" href="glossary.html#hash">hash</a>) of every input, saved every request and reply, and never dropped a failed task from the totals.</p>
  </div>

  <h2>The pipeline</h2>
  <ol class="steps">
    <li><strong>1. Preflight</strong>Checked all 220 tasks, 10,453 checklist items and 261 input files (1.66 GB) before any paid run.</li>
    <li><strong>2. Generate</strong>One resumable job ran all 220 tasks with GPT, then all 220 with Claude.</li>
    <li><strong>3. Inspect</strong>Extracted text and page images from every saved file for the judges.</li>
    <li><strong>4. Calibrate</strong>Graded 6 tasks (24 assessments), reviewed a report on the results, then approved full grading.</li>
    <li><strong>5. Grade</strong>880 blinded assessments, checkpointed one by one.</li>
    <li><strong>6. Analyze</strong>Offline scripts built every table and chart; no new model calls.</li>
  </ol>

  <h2 id="agent">How the coding agent was used</h2>
  <p>The whole project was built with a coding agent, with a human approving every paid step and every claim.</p>
  <ul class="tight">
    <li><strong>Planned:</strong> drafted the evaluation plan and kept a written run log, updated at each stage (<a href="https://github.com/yasskin/gdpval-paired-eval/blob/main/PROJECT_PLAN.md">PROJECT_PLAN.md</a>).</li>
    <li><strong>Built:</strong> wrote the harness, grader, tests, analysis scripts and this site.</li>
    <li><strong>Operated:</strong> ran preflight checks, monitored the unattended jobs and diagnosed failures from saved records, such as the expired login that paused grading.</li>
    <li><strong>Checked:</strong> re-derived every number on this site from saved records and corrected claims that went beyond the evidence.</li>
    <li><strong>Human control:</strong> paid stages, budgets and published claims needed explicit approval; the agent never launched paid work on its own.</li>
  </ul>
  <h2>Settings frozen before the run</h2>
  <div class="table-wrap"><table class="numbers">
    <tbody>
      <tr><th>Models</th><td><code>gpt-6-astra</code> (low reasoning, OpenAI API) and <code>databricks-claude-opus-5-5</code> (default settings, Databricks)</td></tr>
      <tr><th>Per-task limits (both models)</th><td>14 turns · 24 tool calls · 10,000 tokens per reply · 50,000 tokens written per task · 30-minute schedule · 150 s per code run</td></tr>
      <tr><th>Tools (both models)</th><td>Python, web search and image viewing, with identical input files and instructions</td></tr>
      <tr><th>Retries</th><td>At most 3 requests per reply on network errors; no task regenerated after a poor answer</td></tr>
      <tr><th>Judge limits</th><td>16 turns · 32 tool calls · 12,000 tokens per reply · 60,000 per assessment; order randomized with a fixed seed</td></tr>
      <tr><th>Experiment IDs</th><td>Generation <code>c6d44b16-80ed-4955-bba6-a34c1a10110d</code> · grading <code>51cfbb2b-90ca-42e6-8c61-1c28346844ee</code></td></tr>
    </tbody>
  </table></div>

  <h2>Fingerprints and checks</h2>
  <div class="table-wrap"><table class="numbers">
    <thead><tr><th>Item</th><th>Value</th></tr></thead>
    <tbody>
      <tr><td>Dataset file (SHA-256)</td><td><code class="hash">f8422fab9b21d90c0ee5f0659842ab666d418cb8940842918f9f4b0df7ae0202</code></td></tr>
      <tr><td>Reference-file manifest (SHA-256)</td><td><code class="hash">0bc42b02a40607ecd8255c5d485e3684fd3abd771ef3f45be2462baa3d0d0157</code><br>over 261 files, 1,656,670,179 bytes</td></tr>
      <tr><td>Grading policy (SHA-256)</td><td><code class="hash">c47ea4141aecd94e332adcf58ebc36ccdb1ed80af1d023bd87c538624849e19f</code></td></tr>
      <tr><td>Calibration results approved (SHA-256)</td><td><code class="hash">428c3ee4fd404088e34b070d217af4945bc2673940e0281ebe6a61b9752cfd20</code></td></tr>
      <tr><td>Saved output files</td><td>550 files, each re-checked against its size and SHA-256</td></tr>
      <tr><td>Automated tests</td><td>16 harness tests (preflight) · 21 run-orchestration tests · 15 grading tests, all passing</td></tr>
    </tbody>
  </table></div>

  <h2>The code</h2>
  <p>All the code is public at <a href="https://github.com/yasskin/gdpval-paired-eval"><b>github.com/yasskin/gdpval-paired-eval</b></a>. Its README lists every script in run order. Raw model outputs and judge grades are not in the repository because they are large and contain copies of the GDPval reference files. Main pieces:</p>
  <div class="table-wrap"><table class="numbers">
    <thead><tr><th>File</th><th>What it does</th></tr></thead>
    <tbody>
      <tr><td><a href="https://github.com/yasskin/gdpval-paired-eval/blob/main/full_run.py"><code>full_run.py</code></a></td><td>Resumable generation job: preflight hashes, both providers, limits, checkpoints, status matrix</td></tr>
      <tr><td><a href="https://github.com/yasskin/gdpval-paired-eval/blob/main/full_grade.py"><code>full_grade.py</code></a></td><td>Separate grading workspace: inspect files, blinded judges, approval gates, aggregate reports</td></tr>
      <tr><td><a href="https://github.com/yasskin/gdpval-paired-eval/blob/main/retry_claude.py"><code>retry_claude.py</code></a></td><td>The separately labeled larger-limit Claude follow-up</td></tr>
      <tr><td><a href="https://github.com/yasskin/gdpval-paired-eval/blob/main/analyze_sectors.py"><code>analyze_sectors.py</code></a>, <a href="https://github.com/yasskin/gdpval-paired-eval/blob/main/analyze_plan_items.py"><code>analyze_plan_items.py</code></a></td><td>Offline statistics: sectors, costs, judge agreement, slice ranking, failure candidates</td></tr>
      <tr><td><code>build_site_*.py</code></td><td>Generate this site's data-driven pages</td></tr>
      <tr><td><a href="https://github.com/yasskin/gdpval-paired-eval/blob/main/test_full_grade.py"><code>test_full_grade.py</code></a> and run tests</td><td>Offline tests for coverage, resume, locking, retries and grading validation</td></tr>
    </tbody>
  </table></div>
  <p class="note">Re-running the job resumes from checkpoints and skips finished work: <code>uv run python full_run.py run --experiment &lt;dir&gt;</code>, then <code>full_grade.py inspect | grade | aggregate --workspace &lt;dir&gt;</code>. Every paid stage needed a recorded human approval.</p>



  <h2>Status of every task (220 × 2)</h2>
  <p class="howto">one row per task. "Finished · 1 file" means the model said it was done and saved a file. The last two columns show each judge's verdict. <a href="data/status_matrix.csv">Download as CSV</a>.</p>
  <details class="explain">
    <summary>Show all 220 tasks</summary>
    <p><input id="q" type="search" placeholder="Filter by occupation or status…" style="width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px"></p>
    <div class="table-wrap"><table class="matrix" id="m">
      <thead><tr><th>Occupation · task</th><th class="gpt-h">GPT</th><th class="claude-h">Claude</th><th>GPT's judge</th><th>Claude's judge</th></tr></thead>
      <tbody>
{mrows}
      </tbody></table></div>
  </details>
  <script>
    document.getElementById('q').addEventListener('input', e => {{
      const q = e.target.value.toLowerCase();
      for (const tr of document.querySelectorAll('#m tbody tr')) tr.hidden = !tr.textContent.toLowerCase().includes(q);
    }});
  </script>
"""

for name, title, sub, body in (
        ("failures.html", "Failures", "Which failures matter, and which are noise", failures),
        ("data.html", "Data &amp; code", "Reproducibility, frozen settings and the full status matrix", data_page)):
    (SITE / name).write_text(page(name, title, sub, body), encoding="utf-8")


# ---------------------------------------------------------------- methods.html generated sections
def money(x):
    return f"${x:,.2f}" if x < 100 else f"${x:,.0f}"


def mtok(n):
    return f"{n / 1e6:,.1f}M"


C = D["cost"]
STAGES = [("primary_generation", "Main run: writing the 440 answers"),
          ("primary_grading", "Grading: 880 assessments (model = judge)"),
          ("claude_retries", "Follow-up: 62 Claude retries with larger limits"),
          ("pilot_six_tasks", "Development pilot: 6 tasks, both stages")]


def cell(stage, prov):
    a = C[stage].get(prov)
    if not a:
        return '<td class="n">–</td>'
    tin = a["input"] + a.get("cached", 0) + a.get("cache_write", 0)
    return f'<td class="n"><b>{money(a["usd_micro"] / 1e6)}</b><div class="pnote">{mtok(tin)} in · {mtok(a["output"])} out</div></td>'


tot = {p: sum(C[s].get(p, {}).get("usd_micro", 0) for s, _ in STAGES) / 1e6 for p in ("openai", "anthropic")}
cost_rows = "\n".join(
    f'        <tr><td>{label}</td>{cell(s, "openai")}{cell(s, "anthropic")}<td class="n">{money(sum(C[s].get(p, {}).get("usd_micro", 0) for p in ("openai", "anthropic")) / 1e6)}</td></tr>'
    for s, label in STAGES)
no_usage = sum(C[s].get("no_usage", {}).get("requests", 0) for s in C)
gen_g = C["primary_generation"]["openai"]["usd_micro"] / 1e6
gen_c = C["primary_generation"]["anthropic"]["usd_micro"] / 1e6
P = D["prices"]

J = D["judges"]
A = J["agreement"]
SP = J["self_preference"]
ujg = {(r["judge_provider"], r["generator"]): r["mean"] for r in J["unverified_by_judge_generator"]}
FMT_NAME = {"pdf": "PDF", "docx": "Word", "xlsx": "Excel", "pptx": "PowerPoint", "multiple formats": "Several formats",
            "no file": "No file handed in", "zip": "ZIP archive", "txt": "Plain text", "wav": "Audio (WAV)",
            "png": "Image (PNG)", "mp4": "Video (MP4)"}
fmt_rows = "\n".join(
    f'        <tr><td>{FMT_NAME.get(r["format"], r["format"])}</td><td class="n">{r["size"]:,}</td>'
    f'<td class="n">{r["mean"] * 100:.1f}%</td><td><div class="mini"><span class="{"claude" if r["mean"] > .5 else "gpt"}" style="width:{r["mean"] * 100:.0f}%"></span></div></td></tr>'
    for r in sorted(J["unverified_by_format"], key=lambda r: r["mean"]) if r["size"] >= 50)

S = D["slice"]
selected = set(S["selected"])


def rank_row(r):
    mark = ('<span class="badge gpt">Selected</span>' if r["occupation"] in selected
            else ('<span class="badge even">Eligible</span>' if r["eligible"] else '<span class="muted">Too few files</span>'))
    return (f'        <tr><td class="n">{r["rank"]}</td><td>{E(r["occupation"])}</td><td class="n">{r["mean_abs"]:.1f}</td>'
            f'<td class="n">{r["coverage"]}/5</td><td class="n"><span class="wg">{r["gpt"]}</span> · <span class="wc">{r["claude"]}</span></td><td>{mark}</td></tr>')


top_rows = "\n".join(rank_row(r) for r in S["ranking"] if r["eligible"])
other_rows = "\n".join(rank_row(r) for r in S["ranking"] if not r["eligible"])
sel_dirs = Counter(t["direction"] for t in S["selected_tasks"])

methods_block = f"""<!-- plan:start (generated by build_site_plan.py) -->
  <h2 id="slice">How we chose what to inspect closely</h2>
  <p>The brief suggests a 20–40 task slice. We ran <strong>all 220 tasks</strong> instead, because a single unattended job made it affordable and a full run avoids hand-picking. That gives a less biased overall picture. We then chose a 30-task slice for close inspection using a rule written down <em>before</em> the results came in:</p>
  <ol class="steps">
    <li><strong>Agreement only</strong>A task counts only if <em>both</em> judges clearly favor the same model; otherwise it scores 0.</li>
    <li><strong>Size of gap</strong>Use the smaller of the two judges' guaranteed score gaps, so neither judge can inflate it.</li>
    <li><strong>Rank occupations</strong>Average that gap over the occupation's five tasks.</li>
    <li><strong>Need evidence</strong>At least 4 of 5 tasks must have files from both models and four valid grades.</li>
    <li><strong>Top six, all tasks</strong>Take the top six eligible occupations and keep all five tasks each: 30 tasks, no cherry-picking within an occupation.</li>
  </ol>
  <p>Only {S['eligible']} of 44 occupations had enough evidence, mostly because Claude often handed in no file. The six selected occupations are {', '.join(S['selected'][:-1])} and {S['selected'][-1]}. Across these 30 tasks both judges agree on a direction for {sel_dirs.get('GPT', 0) + sel_dirs.get('Claude', 0)}: <span class="wg">{sel_dirs.get('GPT', 0)} favor GPT</span>, <span class="wc">{sel_dirs.get('Claude', 0)} favor Claude</span>.</p>
  <div class="table-wrap"><table class="numbers">
    <thead><tr><th class="n">Rank (of 44)</th><th>Occupation</th><th class="n">Avg. agreed gap (points)</th><th class="n">Tasks with both files + grades</th><th class="n">Both judges favor <span class="wg">GPT</span> · <span class="wc">Claude</span></th><th>Status</th></tr></thead>
    <tbody>
{top_rows}
    </tbody></table></div>
  <details class="explain"><summary>The other {44 - S['eligible']} occupations (not eligible)</summary>
    <div class="table-wrap"><table class="numbers"><tbody>
{other_rows}
    </tbody></table></div></details>
  <p class="note">A slice chosen for big gaps exaggerates differences by design; it shows where to look, not how the models compare overall. The full-220 results remain the headline. Hand-checking these 30 tasks against the original files is the next step and is not yet done.</p>

  <h2 id="cost">What it cost</h2>
  <p>We did not set a dollar cap, but every request's token usage was recorded. Multiplying by each provider's published list price gives an <strong>estimated total of about {money(tot['openai'] + tot['anthropic'])}</strong> for everything shown on this site, including the pilot.</p>
  <div class="table-wrap"><table class="numbers cost">
    <thead><tr><th>Stage</th><th class="n">OpenAI (GPT)</th><th class="n">Anthropic (Claude)</th><th class="n">Stage total</th></tr></thead>
    <tbody>
{cost_rows}
      <tr><td><strong>Total</strong></td><td class="n"><b>{money(tot['openai'])}</b></td><td class="n"><b>{money(tot['anthropic'])}</b></td><td class="n"><b>{money(tot['openai'] + tot['anthropic'])}</b></td></tr>
    </tbody></table></div>
  <div class="grid">
    <div class="stat gpt"><div class="num">{money(gen_g / 211)}</div><div class="label">GPT: answer cost per delivered file (211 files)</div></div>
    <div class="stat claude"><div class="num">{money(gen_c / 144)}</div><div class="label">Claude: answer cost per delivered file (144 files)</div></div>
  </div>
  <ul class="tight note">
    <li><strong>Prices used</strong> (per million tokens, checked Nov 17, 2026): GPT-6 Astra ${P['openai']['input']:.2f} input, ${P['openai']['cached']:.2f} cached input, ${P['openai']['cache_write']:.2f} cache write and ${P['openai']['output']:.2f} output. Claude Opus 5.5 ${P['anthropic']['input']:.2f} input and ${P['anthropic']['output']:.2f} output. These are estimates, not invoices.</li>
    <li>GPT reused a large share of its input through caching, which lowers its cost. Databricks reported no caching for Claude, so all of Claude's input is priced at the full rate.</li>
    <li>Not included: web-search tool fees, Databricks platform charges, early smoke tests and {no_usage} failed requests that returned no usage (one with an unknown outcome).</li>
    <li>The pilot recorded only total input and output tokens, so its input is priced at the full rate as an upper bound.</li>
  </ul>

  <h2 id="judges">Can we trust the judges?</h2>
  <p>AI judges can be wrong, can favor their own model and can miss things they cannot open. We checked each risk.</p>
  <div class="grid">
    <div class="stat"><div class="num">{J['pass_fail_agreement'] * 100:.1f}%</div><div class="label">agreement on pass/fail when both judges could check an item ({J['pass_fail_pairs']:,} items; <a class="term" href="glossary.html#kappa">kappa</a> {J['kappa']:.2f}, strong)</div></div>
    <div class="stat"><div class="num">{A['both_gpt'] + A['both_claude'] + A['both_tie']}</div><div class="label">tasks where both judges reach the same verdict (<span class="wg">{A['both_gpt']} GPT</span>, <span class="wc">{A['both_claude']} Claude</span>, {A['both_tie']} tie)</div></div>
    <div class="stat"><div class="num">{A['opposite']}</div><div class="label">tasks where the judges pick opposite winners</div></div>
    <div class="stat"><div class="num">24.3%</div><div class="label">of checklist items the judges could not verify</div></div>
  </div>
  <h3>1. Calibration before scaling up</h3>
  <p>Before grading all 880 jobs, both judges graded 6 tasks (24 assessments, 964 checklist decisions). We reviewed a report on those grades, including the 26.3% marked unverified and the tasks where the judges disagreed. We then approved the full run with the judges and instructions unchanged. This approval let automated grading proceed; it did not confirm that the grades are professionally correct.</p>
  <h3>2. Do the judges favor their own model?</h3>
  <p>The Claude judge favored Claude {SP['anthropic']['own']} to {SP['anthropic']['other']} on tasks it could decide, which is <strong>unlikely to be chance</strong> (p={SP['anthropic']['p']:.3f}). The GPT judge favored GPT {SP['openai']['own']} to {SP['openai']['other']}, which is within chance (p={SP['openai']['p']:.2f}). That is why the site leads with tasks where <em>both</em> judges agree, and never averages the two.</p>
  <h3>3. What the judges could not check</h3>
  <p>The judges read extracted text and page images; they could not open slides natively, play audio or video, or recalculate spreadsheets. The unverified rate shows this clearly. Both judges also found Claude's work harder to verify, mostly because of missing files: the GPT judge left {ujg[('openai', 'openai')] * 100:.0f}% of GPT's items unverified versus {ujg[('openai', 'anthropic')] * 100:.0f}% of Claude's, and the Claude judge {ujg[('anthropic', 'openai')] * 100:.0f}% versus {ujg[('anthropic', 'anthropic')] * 100:.0f}%.</p>
  <div class="table-wrap"><table class="numbers" style="max-width:640px">
    <thead><tr><th>Format of the handed-in file</th><th class="n">Checklist items</th><th class="n">Unverified</th><th></th></tr></thead>
    <tbody>
{fmt_rows}
    </tbody></table></div>
  <p class="note">PowerPoint, video and ZIP files were almost entirely unverifiable, so results on tasks that need them say little about quality. A human audit of the judges' pass/fail calls against the original files has not been done; until then, all quality results are provisional.</p>

  <h2 id="pilot">Development pilot (kept separate)</h2>
  <p>Before the full run, a 6-task pilot tested the harness and grading end to end. Its fixes, such as better file inspection and recovery from errors, went into the frozen settings above. Pilot results are not counted anywhere on this site except in the cost table.</p>
<!-- plan:end -->
"""
mp = SITE / "methods.html"
mt = mp.read_text(encoding="utf-8")
start, end = mt.find("<!-- plan:start"), mt.find("<!-- plan:end -->")
if start == -1:
    anchor = "  <h2>Average scores (as ranges)</h2>"
    assert anchor in mt
    mt = mt.replace(anchor, methods_block + "\n" + anchor)
else:
    mt = mt[:start] + methods_block.rstrip("\n").lstrip() + mt[end + len("<!-- plan:end -->"):]
mp.write_text(mt, encoding="utf-8")
print("wrote failures.html, data.html; ledger", len(ledger), "both delivered", both_delivered, dict(sev_counts))
