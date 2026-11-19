"""Build site/sectors.html and its two SVG charts from site/sector_results.json.

Run analyze_sectors.py first.
"""

import json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
DATA = json.loads((SITE / "sector_results.json").read_text(encoding="utf-8"))
ROWS = DATA["sectors"]
HET = DATA["heterogeneity"]
OVR = DATA["overall"]

GPT, CLAUDE, INK, MUTED, LINE = "#10a37f", "#c96442", "#1b1f24", "#5b6470", "#d9dee4"
FONT = "font-family='-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif'"

assert len(ROWS) == 9 and sum(r["n"] for r in ROWS) == 220
assert sum(r["gpt_delivered"] for r in ROWS) == 211 and sum(r["claude_delivered"] for r in ROWS) == 144
assert sum(r["claude_incomplete"] for r in ROWS) == 62
for key, w, l in (("gpt_judge", 38, 31), ("claude_judge", 26, 50)):
    assert sum(r[key]["gpt_better"] for r in ROWS) == w and sum(r[key]["claude_better"] for r in ROWS) == l


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}" if p < 0.1 else f"{p:.2f}"


def p_eq(p):
    s = fmt_p(p)
    return f"p{s}" if s.startswith("<") else f"p={s}"


def verdict(p_raw, p_holm):
    if p_holm < 0.05:
        return "significant", "Significant"
    if p_raw < 0.05:
        return "suggestive", "Suggestive only"
    return "none", "No clear difference"


def delivery_svg():
    w, top, row_h = 780, 58, 30
    x0, x1 = 250, 600
    h = top + row_h * len(ROWS) + 46
    sx = lambda pct: x0 + (x1 - x0) * pct / 100
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}' {FONT} font-size='13' role='img' "
        "aria-labelledby='dtitle'><title id='dtitle'>Share of tasks where each model handed in a file, by sector</title>",
        f"<rect width='{w}' height='{h}' fill='#fff'/>",
        f"<text x='12' y='22' font-size='15' font-weight='600' fill='{INK}'>Did each model hand in a file? Share of tasks, by sector</text>",
        f"<circle cx='262' cy='42' r='6' fill='{GPT}'/><text x='274' y='46' fill='{INK}'>GPT</text>",
        f"<circle cx='322' cy='42' r='6' fill='{CLAUDE}'/><text x='334' y='46' fill='{INK}'>Claude</text>",
        f"<text x='{w - 12}' y='46' text-anchor='end' fill='{MUTED}'>Gap · paired test (Holm-adjusted p)</text>",
    ]
    for pct in range(0, 101, 25):
        x = sx(pct)
        out.append(f"<line x1='{x}' y1='{top - 6}' x2='{x}' y2='{top + row_h * len(ROWS)}' stroke='{LINE}'/>")
        out.append(f"<text x='{x}' y='{top + row_h * len(ROWS) + 16}' text-anchor='middle' fill='{MUTED}' font-size='12'>{pct}%</text>")
    for i, r in enumerate(ROWS):
        y = top + row_h * i + row_h / 2
        g, c = 100 * r["gpt_delivered"] / r["n"], 100 * r["claude_delivered"] / r["n"]
        kind, _ = verdict(r["delivery_p"], r["delivery_p_holm"])
        weight = "700" if kind == "significant" else "400"
        out.append(f"<text x='12' y='{y + 4}' fill='{INK}' font-weight='{weight}'>{escape(r['label'])} <tspan fill='{MUTED}' font-weight='400'>({r['n']})</tspan></text>")
        out.append(f"<line x1='{sx(c)}' y1='{y}' x2='{sx(g)}' y2='{y}' stroke='#9aa3ad' stroke-width='3'/>")
        out.append(f"<circle cx='{sx(c)}' cy='{y}' r='7' fill='{CLAUDE}'><title>Claude {r['claude_delivered']}/{r['n']}</title></circle>")
        out.append(f"<circle cx='{sx(g)}' cy='{y}' r='7' fill='{GPT}'><title>GPT {r['gpt_delivered']}/{r['n']}</title></circle>")
        star = " ★" if kind == "significant" else ""
        color = INK if kind == "significant" else MUTED
        out.append(
            f"<text x='{w - 12}' y='{y + 4}' text-anchor='end' fill='{color}' font-weight='{weight}'>"
            f"+{g - c:.0f} pts · {escape(p_eq(r['delivery_p_holm']))}{star}</text>"
        )
    out.append(
        f"<text x='12' y='{h - 8}' fill='{MUTED}' font-size='12'>★ significant after correcting for 9 sectors. "
        f"Does the gap differ between sectors? Yes (permutation test p={fmt_p(HET['delivery']['p'])}).</text>"
    )
    out.append("</svg>")
    return "\n".join(out)


def quality_svg():
    w, top, block = 780, 62, 44
    mid, scale = 500, 14
    h = top + block * len(ROWS) + 40
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}' {FONT} font-size='13' role='img' "
        "aria-labelledby='qtitle'><title id='qtitle'>Tasks where each judge picked a winner, by sector</title>",
        f"<rect width='{w}' height='{h}' fill='#fff'/>",
        f"<text x='12' y='22' font-size='15' font-weight='600' fill='{INK}'>Whose work was better? Tasks with a clear winner, by sector and judge</text>",
        f"<text x='{mid - 8}' y='46' text-anchor='end' fill='{CLAUDE}' font-weight='600'>◀ Claude better</text>",
        f"<text x='{mid + 8}' y='46' fill='{GPT}' font-weight='600'>GPT better ▶</text>",
        f"<text x='{w - 12}' y='46' text-anchor='end' fill='{MUTED}'>Can't tell · p (adj.)</text>",
        f"<line x1='{mid}' y1='{top - 6}' x2='{mid}' y2='{top + block * len(ROWS)}' stroke='{INK}'/>",
    ]
    for n in (5, 10):
        for x in (mid - n * scale, mid + n * scale):
            out.append(f"<line x1='{x}' y1='{top - 6}' x2='{x}' y2='{top + block * len(ROWS)}' stroke='{LINE}' stroke-dasharray='3 3'/>")
            out.append(f"<text x='{x}' y='{top + block * len(ROWS) + 16}' text-anchor='middle' fill='{MUTED}' font-size='12'>{n}</text>")
    for i, r in enumerate(ROWS):
        y0 = top + block * i
        if i:
            out.append(f"<line x1='12' y1='{y0}' x2='{w - 12}' y2='{y0}' stroke='#eef1f4'/>")
        out.append(f"<text x='12' y='{y0 + 26}' fill='{INK}'>{escape(r['label'])}</text>")
        for j, (key, name) in enumerate((("gpt_judge", "GPT as judge"), ("claude_judge", "Claude as judge"))):
            q = r[key]
            y = y0 + 6 + j * 17
            out.append(f"<text x='{mid - 9 * scale - 8}' y='{y + 11}' text-anchor='end' fill='{MUTED}' font-size='11.5'>{name}</text>")
            cw, gw = q["claude_better"] * scale, q["gpt_better"] * scale
            out.append(f"<rect x='{mid - cw}' y='{y}' width='{cw}' height='14' fill='{CLAUDE}'><title>{name}: Claude better on {q['claude_better']}</title></rect>")
            out.append(f"<rect x='{mid}' y='{y}' width='{gw}' height='14' fill='{GPT}'><title>{name}: GPT better on {q['gpt_better']}</title></rect>")
            if q["claude_better"]:
                out.append(f"<text x='{mid - cw - 4}' y='{y + 11}' text-anchor='end' fill='{INK}' font-size='11.5'>{q['claude_better']}</text>")
            if q["gpt_better"]:
                out.append(f"<text x='{mid + gw + 4}' y='{y + 11}' fill='{INK}' font-size='11.5'>{q['gpt_better']}</text>")
            out.append(
                f"<text x='{w - 12}' y='{y + 11}' text-anchor='end' fill='{MUTED}' font-size='11.5'>"
                f"{q['unresolved'] + q['tie']} · p={escape(fmt_p(q['p_holm']))}</text>"
            )
    out.append(
        f"<text x='12' y='{h - 8}' fill='{MUTED}' font-size='12'>No sector is significant for either judge. "
        f"Does the pattern differ between sectors? No (p={fmt_p(HET['gpt_judge']['p'])} GPT judge; "
        f"p={fmt_p(HET['claude_judge']['p'])} Claude judge).</text>"
    )
    out.append("</svg>")
    return "\n".join(out)


def _bar(k, n, who):
    return (f"<td class='n'>{k}/{n}<div class='mini'><span class='{who}' "
            f"style='width:{100 * k / n:.0f}%'></span></div></td>")


def _delivery_badge(r):
    if r["delivery_p_holm"] < 0.05:
        return "<span class='badge gpt'>GPT ahead &middot; significant</span>"
    if r["delivery_p"] < 0.05:
        return "<span class='badge weak'>GPT ahead &middot; suggestive</span>"
    return "<span class='badge even'>No clear difference</span>"


def delivery_rows():
    out = []
    for r in ROWS:
        n, g, c = r["n"], r["gpt_delivered"], r["claude_delivered"]
        out.append(
            f"<tr><td>{escape(r['label'])}</td>{_bar(g, n, 'gpt')}{_bar(c, n, 'claude')}"
            f"<td class='n'><strong>+{100 * (g - c) / n:.0f}</strong></td>"
            f"<td class='n'>{r['claude_incomplete']}</td>"
            f"<td class='n'>{r['gpt_only']} / {r['claude_only']}</td>"
            f"<td>{_delivery_badge(r)}<div class='pnote'>{escape(p_eq(r['delivery_p']))} &middot; "
            f"adj. {escape(fmt_p(r['delivery_p_holm']))}</div></td></tr>"
        )
    return "\n".join(out)


def _wins(q):
    return (f"<td class='n'><span class='wg'>{q['gpt_better']}</span> &ndash; "
            f"<span class='wc'>{q['claude_better']}</span><div class='pnote'>adj. p={fmt_p(q['p_holm'])}</div></td>")


def quality_rows():
    out = []
    for r in ROWS:
        g, c = r["gpt_judge"], r["claude_judge"]
        out.append(
            f"<tr><td>{escape(r['label'])}</td>{_wins(g)}{_wins(c)}"
            f"<td><span class='badge even'>No significant difference</span></td></tr>"
        )
    return "\n".join(out)


def nav():
    items = [
        ("index.html", "Overview", ""),
        ("tasks.html", "GDPval gold tasks", ""),
        ("sectors.html", "By sector", ""),
        ("gpt.html", "For OpenAI (GPT)", "gpt"),
        ("claude.html", "For Anthropic (Claude)", "claude"),
        ("failures.html", "Failures", ""),
        ("audit.html", "Audit progress", ""),
        ("example.html", "Worked example", ""),
        ("methods.html", "Methods &amp; limits", ""),
        ("data.html", "Data &amp; code", ""),
        ("glossary.html", "Glossary", ""),
    ]
    links = []
    for href, text, cls in items:
        c = f' class="{cls}"' if cls else ""
        cur = ' aria-current="page"' if href == "sectors.html" else ""
        links.append(f'      <a{c} href="{href}"{cur}>{text}</a>')
    return "\n".join(links)


def main():
    (SITE / "sector_delivery.svg").write_text(delivery_svg(), encoding="utf-8")
    (SITE / "sector_quality.svg").write_text(quality_svg(), encoding="utf-8")

    fin = next(r for r in ROWS if r["sector"] == "Finance and Insurance")
    whl = next(r for r in ROWS if r["sector"] == "Wholesale Trade")
    n_sig = sum(r["delivery_p_holm"] < 0.05 for r in ROWS)
    sugg = [100 * (r["gpt_delivered"] - r["claude_delivered"]) / r["n"] for r in ROWS if r["delivery_p"] < 0.05 <= r["delivery_p_holm"]]
    n_sugg, sugg_lo, sugg_hi = len(sugg), min(sugg), max(sugg)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>By sector · GDPval Paired Evaluation</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <div class="brand">GDPval Paired Evaluation<small>How GPT and Claude compare across the nine industries</small></div>
    <nav class="tabs" aria-label="Sections">
{nav()}
    </nav>
  </div>
</header>

<main class="wrap">
  <h1>Results by sector: the industry view</h1>
  <p class="lede">Does the GPT-vs-Claude picture change from one industry to another? This page compares both models side by side,
  before the per-company pages go deeper on each model.</p>

  <div class="plain">
    <p><strong>In plain English:</strong> GDPval groups its 220 tasks into nine <a class="term" href="glossary.html#sector">sectors</a>
    (industries), 20–25 tasks each. GPT handed in a file more often than Claude in every sector, but the size of that lead
    varies a lot: it is largest in Finance &amp; insurance ({fin['gpt_delivered']} vs {fin['claude_delivered']} of {fin['n']}) and almost zero in
    Wholesale trade ({whl['gpt_delivered']} vs {whl['claude_delivered']}). On the quality of the work, no sector shows a
    <a class="term" href="glossary.html#significant">statistically significant</a> difference, and the quality pattern does not change by sector.</p>
  </div>

  <h2>1. Handing in a file</h2>
  <figure class="card">
    <img src="sector_delivery.svg" alt="Dot chart of delivery rate by sector. GPT is at or above 88% in every sector. Claude ranges from {fin['claude_delivered']} of {fin['n']} in Finance and insurance to {whl['claude_delivered']} of {whl['n']} in Wholesale trade." style="width:100%;height:auto">
  </figure>
  <p class="howto">Each row is one sector. The green dot is the share of that sector's tasks where GPT finished and handed in a file;
  the orange dot is Claude. A longer grey line means a bigger gap. The number on the right is the gap in percentage points
  and the corrected p-value (smaller means less likely to be luck).</p>
  <ul>
    <li><strong>Significant in {n_sig} sector:</strong> Finance &amp; insurance. Claude did not finish {fin['claude_incomplete']} of its {fin['n']}
    conversations within the <a class="term" href="glossary.html#budget">budget</a>, so it often ran out before saving a file.</li>
    <li><strong>Suggestive in {n_sugg} more sectors:</strong> GPT's lead is {sugg_lo:.0f}–{sugg_hi:.0f} points and each would pass a single test on its own,
    but not after correcting for testing nine sectors at once. With only 25 tasks per sector, gaps this size are hard to confirm.</li>
    <li><strong>No gap in Wholesale trade:</strong> {whl['gpt_delivered']} vs {whl['claude_delivered']}.</li>
    <li><strong>Does the gap really differ between sectors?</strong> Yes. A test that shuffles tasks between sectors at random
    produced variation this large only about {HET['delivery']['p'] * 1000:.0f} times in 1,000 (p={fmt_p(HET['delivery']['p'])}).
    The variation comes from Claude: GPT delivers at a similar rate everywhere.</li>
  </ul>

  <h2>2. Whose work was better</h2>
  <figure class="card">
    <img src="sector_quality.svg" alt="Diverging bar chart of tasks where each judge favored GPT or Claude, per sector. Bars are short, mostly under 8 tasks, and no sector is significant." style="width:100%;height:auto">
  </figure>
  <p class="howto">For each sector there are two bars, one per <a class="term" href="glossary.html#judge">judge</a>. Orange bars to the left count
  tasks where that judge's scores put Claude clearly ahead; green bars to the right count GPT clearly ahead. The grey number on
  the right counts tasks with no clear winner (<a class="term" href="glossary.html#bounds">score ranges</a> overlap, an exact tie,
  or a missing grade). Most tasks fall in that last group, so the bars are built on small numbers.</p>
  <ul>
    <li><strong>No sector is significant for either judge.</strong> The smallest corrected p-value is
    {fmt_p(min(min(r['gpt_judge']['p_holm'], r['claude_judge']['p_holm']) for r in ROWS))}.</li>
    <li><strong>The judges lean opposite ways.</strong> Across all sectors, GPT as judge picks GPT {OVR['gpt_judge']['gpt_better']}–{OVR['gpt_judge']['claude_better']}
    (p={fmt_p(OVR['gpt_judge']['p'])}, not significant); Claude as judge picks Claude {OVR['claude_judge']['claude_better']}–{OVR['claude_judge']['gpt_better']}
    (p={fmt_p(OVR['claude_judge']['p'])}). Each judge appears to favor its own model, so neither result is a reliable quality verdict.</li>
    <li><strong>No sector stands out.</strong> The quality pattern is consistent across sectors
    (p={fmt_p(HET['gpt_judge']['p'])} with GPT as judge, p={fmt_p(HET['claude_judge']['p'])} with Claude as judge).</li>
  </ul>

  <h2>All the numbers</h2>
  <p class="howto">The detail behind the two charts, one table each. Sectors are listed from the largest delivery gap to the smallest.</p>

  <h3>Handing in a file</h3>
  <div class="table-wrap">
  <table class="matrix numbers">
    <thead>
      <tr><th>Sector</th><th class="n">GPT</th><th class="n">Claude</th><th class="n">Gap<br><small>points</small></th>
      <th class="n">Claude<br><small>ran out</small></th><th class="n">Only one<br><small>GPT / Claude</small></th><th>Result</th></tr>
    </thead>
    <tbody>
{delivery_rows()}
    </tbody>
  </table>
  </div>
  <p class="note">"Claude ran out" counts tasks where Claude hit a limit before finishing. "Only one" counts tasks where just one model delivered; these are the tasks the significance test uses.
  "adj." is the p-value after correcting for nine sectors.</p>

  <h3>Whose work was better</h3>
  <div class="table-wrap">
  <table class="matrix numbers">
    <thead>
      <tr><th>Sector</th><th class="n">GPT's judge<br><small><span class="wg">GPT</span> &ndash; <span class="wc">Claude</span> wins</small></th>
      <th class="n">Claude's judge<br><small><span class="wg">GPT</span> &ndash; <span class="wc">Claude</span> wins</small></th><th>Result</th></tr>
    </thead>
    <tbody>
{quality_rows()}
    </tbody>
  </table>
  </div>
  <p class="note">Wins count only tasks where a judge picked a clear winner; every other task had no clear winner and is left out.</p>

  <h2>How significance was tested</h2>
  <ul>
    <li><strong>Matched pairs.</strong> Both models attempted the same tasks, so each test compares them task by task rather than as two separate groups.</li>
    <li><strong>Handing in a file:</strong> an exact McNemar test. Only tasks where one model delivered and the other did not
    (the “Only one” column) carry information about which is better.</li>
    <li><strong>Quality:</strong> an exact sign test on tasks with a clear winner, run separately for each judge. Ties and unclear
    tasks are left out of the test, never counted as wins for either side, and the two judges are never averaged.</li>
    <li><strong>Correcting for nine sectors.</strong> Testing nine sectors gives nine chances of a fluke, so p-values are
    Holm-adjusted (“adj.”). A result is called significant when the adjusted p is below 0.05.</li>
    <li><strong>Does the gap differ between sectors?</strong> A permutation test: tasks are shuffled between sectors 100,000 times to see
    how often the sector-to-sector differences are as large as the real ones.</li>
  </ul>

  <div class="callout">
    <strong>Read with care.</strong> This breakdown was not planned before the runs, so treat it as exploratory. Each sector has only
    20–25 tasks and one attempt per model. Grades are <a class="term" href="glossary.html#provisional">provisional</a> and automated,
    and most quality comparisons are unresolved. Sectors also differ in the kinds of files and inputs their tasks involve, so a sector gap does
    not prove that the industry itself is the cause.
  </div>

  <h2>Next: what each company could improve</h2>
  <p>The company pages turn these patterns into specific weaknesses and suggested training data for each model's team.</p>
  <div class="grid">
    <div class="card gpt"><h3>For OpenAI (GPT)</h3><p>GPT delivered almost everywhere; the open question is whether its files meet every requirement.</p><a href="gpt.html">See GPT findings →</a></div>
    <div class="card claude"><h3>For Anthropic (Claude)</h3><p>Claude's delivery gap is largest in Finance &amp; insurance, where it often ran out of room before saving a file.</p><a href="claude.html">See Claude findings →</a></div>
  </div>
</main>

<footer class="site"><div class="wrap">Provisional results from a take-home evaluation. <a href="index.html">Back to overview</a>.</div></footer>
</body>
</html>
"""
    (SITE / "sectors.html").write_text(html, encoding="utf-8")
    print("wrote sectors.html, sector_delivery.svg, sector_quality.svg")


if __name__ == "__main__":
    main()
