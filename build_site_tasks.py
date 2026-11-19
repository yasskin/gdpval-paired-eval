"""Generate site/tasks.html: what the public GDPval gold tasks are and how they are scored.

Run: uv run --no-project --with pandas --with pyarrow python build_site_tasks.py
"""

import collections
import html
import json
import os
import statistics
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PARQUET = REPO / "gdpval-data" / "data" / "train-00000-of-00001.parquet"
OUT = HERE / "site" / "tasks.html"

EXAMPLES = [
    ("83d10b06", "Audit sample testing on anti-financial-crime metrics"),
    ("3f625cb2", "Children's privacy legal memo for a lay client"),
    ("c7d83f01", "American option pricing framework in a notebook"),
    ("4d61a19a", "Store promotion form plus a training deck"),
    ("38889c3b", "Instrumental track built on a supplied drum stem"),
    ("a4a9195c", "Electrostatic discharge (ESD) standard operating procedure"),
]

# Real rubric criteria, quoted verbatim, chosen to illustrate the kinds of checks.
CRITERION_KINDS = [
    ("File format and naming", "83d10b06",
     "The submitted deliverable is an Excel workbook file whose basename is 'Sample'"),
    ("Required structure", "83d10b06",
     "The workbook contains a worksheet named exactly 'Sample Size Calculation'"),
    ("Correct numbers and data", "83d10b06",
     "shows the population size N used and N equals the number of data rows"),
    ("Professional constraints", "3f625cb2",
     "The memorandum’s body text does not exceed three pages"),
    ("Domain substance", "3f625cb2",
     "Applies CCPA/CPRA to the facts"),
    ("Works when run", "c7d83f01",
     "The notebook runs end-to-end in a fresh kernel"),
    ("Technical quality of media", "38889c3b",
     "Bass stem bit depth/format is professional quality"),
    ("Penalty for a professional error", "61f546a8",
     "Schedules paint work in M17 on the same day"),
]

e = html.escape


def ext(path):
    return os.path.splitext(path)[1].lower().lstrip(".") or "(none)"


def find_criterion(rubric, needle):
    hits = [c for c in rubric if needle in c["criterion"]]
    assert len(hits) >= 1, needle
    return hits[0]


def main():
    df = pd.read_parquet(PARQUET)
    df["short"] = df.task_id.str[:8]
    df["rubric"] = df.rubric_json.map(json.loads)
    by_short = df.set_index("short")

    n_tasks = len(df)
    sectors = df.groupby("sector").occupation.agg(["nunique", "size"])
    occs = df.groupby(["sector", "occupation"]).size()
    crit_counts = df.rubric.map(len)
    n_crit = int(crit_counts.sum())
    pos_pts = df.rubric.map(lambda r: sum(c["score"] for c in r if c["score"] > 0))
    weights = collections.Counter(c["score"] for r in df.rubric for c in r)
    neg = [c for r in df.rubric for c in r if c["score"] < 0]
    neg_tasks = int(df.rubric.map(lambda r: any(c["score"] < 0 for c in r)).sum())
    words = df.prompt.map(lambda p: len(p.split()))
    has_ref = int(df.reference_files.map(len).gt(0).sum())
    n_ref_files = int(df.reference_files.map(len).sum())
    ref_types = collections.Counter(ext(f) for fs in df.reference_files for f in fs)
    gold_types = collections.Counter(ext(f) for fs in df.deliverable_files for f in fs)
    no_gold = int(df.deliverable_files.map(len).eq(0).sum())

    assert n_tasks == 220 and len(sectors) == 9 and len(occs) == 44
    assert n_crit == 10453 and has_ref == 125 and int(crit_counts.median()) == 47
    assert {c.get("author_type") for r in df.rubric for c in r} == {"human"}

    def type_rows(counter, top=10):
        items = counter.most_common()
        shown, rest = items[:top], items[top:]
        rows = "".join(f'<tr><td>.{e(k)}</td><td class="n">{v}</td></tr>' for k, v in shown)
        if rest:
            other = ", ".join(f".{k}" for k, _ in rest)
            rows += f'<tr><td class="muted">Other ({e(other)})</td><td class="n">{sum(v for _, v in rest)}</td></tr>'
        return rows

    sector_rows = []
    for sector, g in occs.groupby(level=0):
        names = "; ".join(e(o) for o in g.index.get_level_values(1))
        sector_rows.append(
            f'<tr><td>{e(sector)}</td><td class="n">{int(g.sum())}</td><td>{names}</td></tr>')

    weight_rows = "".join(
        f'<tr><td class="n">{w:+d}</td><td class="n">{c:,}</td></tr>'
        for w, c in sorted(weights.items(), key=lambda x: -x[1])[:6])

    kind_rows = []
    for kind, tid, needle in CRITERION_KINDS:
        r = by_short.loc[tid]
        c = find_criterion(r.rubric, needle)
        kind_rows.append(
            f'<tr><td>{e(kind)}</td><td>{e(r.occupation)}</td>'
            f'<td>“{e(c["criterion"])}”</td><td class="n">{c["score"]:+d}</td></tr>')

    cards = []
    for tid, title in EXAMPLES:
        r = by_short.loc[tid]
        refs = ", ".join(e(Path(f).name) for f in r.reference_files) or "None"
        gold = ", ".join(e(Path(f).name) for f in r.deliverable_files) or "None"
        first = r.prompt.strip().split("\n")[0]
        excerpt = first if len(first) <= 320 else first[:317].rsplit(" ", 1)[0] + "…"
        rub = r.rubric
        crit_sample = "".join(f'<li>{e(c["criterion"])} <span class="muted">({c["score"]:+d})</span></li>'
                              for c in rub[:3])
        link = (' <a href="example.html">See both models’ artifacts for this task →</a>'
                if tid == "a4a9195c" else "")
        cards.append(f"""
    <div class="card">
      <h3>{e(title)}</h3>
      <p class="muted">{e(r.sector)} · {e(r.occupation)} · task <code>{tid}</code></p>
      <blockquote>{e(excerpt)}</blockquote>
      <ul class="tight">
        <li><strong>Inputs provided:</strong> {refs}</li>
        <li><strong>Expert gold deliverable:</strong> {gold}</li>
        <li><strong>Rubric:</strong> {len(rub)} criteria, {sum(c['score'] for c in rub if c['score'] > 0)} positive points</li>
      </ul>
      <details><summary>First three rubric criteria</summary><ul class="tight">{crit_sample}</ul></details>{link}
    </div>""")

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GDPval gold tasks · GDPval Paired Evaluation</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <div class="brand">GDPval Paired Evaluation<small>What the gold tasks are and how they are scored</small></div>
    <nav class="tabs" aria-label="Sections">
      <a href="index.html">Overview</a>
      <a href="tasks.html" aria-current="page">GDPval gold tasks</a>
      <a href="sectors.html">By sector</a>
      <a class="gpt" href="gpt.html">For OpenAI (GPT)</a>
      <a class="claude" href="claude.html">For Anthropic (Claude)</a>
      <a href="failures.html">Failures</a>
      <a href="audit.html">Audit progress</a>
      <a href="example.html">Worked example</a>
      <a href="methods.html">Methods &amp; limits</a>
      <a href="data.html">Data &amp; code</a>
      <a href="glossary.html">Glossary</a>
    </nav>
  </div>
</header>

<main class="wrap">
  <h1>GDPval gold tasks</h1>
  <p>GDPval is a benchmark of realistic professional work. Each task asks a model to act as a named professional
  and produce a real work product, usually a file such as a spreadsheet, memo, slide deck, notebook or audio mix.
  The public <a href="https://huggingface.co/datasets/openai/gdpval">gold set</a> has {n_tasks} tasks. Every task in
  it was run once by each model in this study.</p>

  <div class="plain">
    <strong>In plain English</strong>
    <p>Think of each task as a realistic work assignment handed to a new employee: a description of the job, sometimes some files to work from, and a request for a finished file. Experts also wrote a detailed <a class="term" href="glossary.html#rubric">grading checklist</a> for each assignment, listing everything a good answer must include. The checklist, not the expert's own answer, is what the models are graded against.</p>
  </div>

  <div class="grid">
    <div class="stat"><div class="num">{n_tasks}</div><div class="label">tasks</div></div>
    <div class="stat"><div class="num">{len(sectors)}</div><div class="label">economic sectors</div></div>
    <div class="stat"><div class="num">{len(occs)}</div><div class="label">occupations, {int(occs.min())} tasks each</div></div>
    <div class="stat"><div class="num">{n_crit:,}</div><div class="label">human-written rubric criteria</div></div>
    <div class="stat"><div class="num">{has_ref}</div><div class="label">tasks supply input files ({n_ref_files} files)</div></div>
    <div class="stat"><div class="num">{int(crit_counts.median())}</div><div class="label">median criteria per task ({crit_counts.min()}–{crit_counts.max()})</div></div>
  </div>

  <h2>Anatomy of a task</h2>
  <div class="table-wrap"><table><tbody>
    <tr><th>Prompt</th><td>A role, a business situation and explicit deliverable requirements. Median {int(words.median())} words
      (range {words.min()}–{words.max():,}).</td></tr>
    <tr><th>Reference files</th><td>Inputs the professional would be handed: source spreadsheets, PDFs, contracts, audio stems.
      {has_ref} of {n_tasks} tasks have them, up to {int(df.reference_files.map(len).max())} per task.</td></tr>
    <tr><th>Gold deliverable</th><td>An expert-made answer. It shows what good looks like but is <em>not</em> what the
      model is scored against; {no_gold} tasks have no gold file in the public release.</td></tr>
    <tr><th>Rubric</th><td>A checklist of weighted criteria written by people. Each criterion is a concrete, checkable
      statement about the deliverable. This is what is scored.</td></tr>
  </tbody></table></div>

  <h2>Sectors and occupations</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Sector</th><th>Tasks</th><th>Occupations (5 tasks each)</th></tr></thead>
    <tbody>{''.join(sector_rows)}</tbody>
  </table></div>

  <h2>Inputs and outputs are files, not chat answers</h2>
  <p>The work is multimodal. Models must read spreadsheets and PDFs, and they often must produce Office files,
  notebooks or media. A text-only reply cannot satisfy criteria such as “submits exactly one PDF”.</p>
  <div class="pair">
    <div class="table-wrap"><table>
      <thead><tr><th>Reference file type</th><th>Files</th></tr></thead>
      <tbody>{type_rows(ref_types)}</tbody>
    </table></div>
    <div class="table-wrap"><table>
      <thead><tr><th>Gold deliverable type</th><th>Files</th></tr></thead>
      <tbody>{type_rows(gold_types)}</tbody>
    </table></div>
  </div>

  <h2>What is evaluated</h2>
  <p>Scoring uses the checklist. An <a class="term" href="glossary.html#judge">AI judge</a> reads the task, the checklist and the model's files, then marks each item. The task score is the share of checklist points earned. Items range from simple mechanical checks to calls that need expert judgement:</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Kind of check</th><th>Occupation</th><th>Real criterion (verbatim)</th><th>Weight</th></tr></thead>
    <tbody>{''.join(kind_rows)}</tbody>
  </table></div>

  <div class="pair">
    <div>
      <h3>Weights</h3>
      <p>Most criteria are worth 1 or 2 points. A task carries a mean of {pos_pts.mean():.0f} positive points
      (range {pos_pts.min()}–{pos_pts.max()}). {len(neg)} penalty criteria across {neg_tasks} tasks subtract points
      for professional errors, such as double-booking contractors or clipping an audio master.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Weight</th><th>Criteria</th></tr></thead>
        <tbody>{weight_rows}</tbody>
      </table></div>
    </div>
    <div>
      <h3>Verdicts</h3>
      <ul class="tight">
        <li><strong>pass</strong>: the delivered evidence satisfies the criterion.</li>
        <li><strong>fail</strong>: the evidence shows it is not satisfied.</li>
        <li><strong>unverified</strong>: the judge could not confirm it from what it could inspect, for example
          audio quality or whether a notebook runs.</li>
        <li><strong>unassessed</strong>: no verdict recorded because that grading attempt did not complete.</li>
      </ul>
      <p>Because unverified items are uncertain, scores are reported as lower and upper bounds rather than
      a single number. Two judges, GPT and Claude, grade independently and are never
      averaged. See <a href="methods.html">Methods &amp; limits</a>.</p>
    </div>
  </div>

  <h2>Six example tasks</h2>
  <p>Excerpts are the first line of the prompt; full prompts continue with detailed requirements.</p>
  {''.join(cards)}

  <div class="callout">
    <strong>Caveat.</strong> Rubrics were written by people, but grading in this study is automated and
    provisional. It has not been validated by occupational experts. Some criteria, especially audio, video and
    “runs end-to-end” checks, cannot be verified fully from a judge’s view of the files.
  </div>
</main>

<footer class="site"><div class="wrap">Data: <a href="https://huggingface.co/datasets/openai/gdpval">openai/gdpval</a>
public gold set. Statistics generated from the dataset by <code>build_site_tasks.py</code>.</div></footer>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} ({len(page):,} bytes); median prompt words {int(words.median())}; "
          f"penalties {len(neg)} in {neg_tasks} tasks")


if __name__ == "__main__":
    main()
