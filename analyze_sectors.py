"""Per-sector GPT vs. Claude comparison with paired significance tests.

Delivery: exact McNemar test on discordant tasks (one model delivered, the other did not).
Quality: exact two-sided sign test on decided pairs (GPT favored vs. Claude favored), per judge;
ties and unresolved pairs carry no direction and are excluded from the test.
Per-sector p-values are Holm-adjusted across the nine sectors. Heterogeneity asks whether the
per-task GPT-minus-Claude margin differs across sectors (permutation test of sector labels).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PARQUET = REPO / "gdpval-data" / "data" / "train-00000-of-00001.parquet"
GRADES = REPO / "gdpval-data" / "full_grades" / "primary-v1"
OUT = HERE / "site" / "sector_results.json"

SHORT = {
    "Professional, Scientific, and Technical Services": "Professional & technical services",
    "Real Estate and Rental and Leasing": "Real estate & leasing",
    "Health Care and Social Assistance": "Health care & social assistance",
    "Finance and Insurance": "Finance & insurance",
    "Wholesale Trade": "Wholesale trade",
    "Retail Trade": "Retail trade",
}


def holm(pvals):
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj.tolist()


def heterogeneity(values, sectors, iters=100_000, seed=7):
    """Permutation test: does the per-task GPT-minus-Claude margin differ across sectors?

    values: per-task +1 (GPT ahead), -1 (Claude ahead) or 0; statistic is the between-sector
    sum of squares of sector means, compared against random reassignment of tasks to sectors.
    """
    x = np.asarray(values, dtype=float)
    codes, _ = pd.factorize(np.asarray(sectors))
    k = codes.max() + 1
    counts = np.bincount(codes, minlength=k)

    def ss(v):
        means = np.bincount(codes, weights=v, minlength=k) / counts
        return float((counts * (means - v.mean()) ** 2).sum())

    obs = ss(x)
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(iters // 2000):
        perms = rng.permuted(np.tile(x, (2000, 1)), axis=1)
        sums = np.stack([perms[:, codes == j].sum(axis=1) for j in range(k)], axis=1)
        s = (counts * (sums / counts - x.mean()) ** 2).sum(axis=1)
        hits += int((s >= obs - 1e-9).sum())
    return obs, (hits + 1) / (iters + 1)


def main():
    tasks = pd.read_parquet(PARQUET, columns=["task_id", "sector"])
    grading = json.loads((GRADES / "grading.json").read_text(encoding="utf-8"))
    runs = pd.DataFrame(
        {
            "task_id": r["task_id"],
            "provider": r["provider"],
            "delivered": r["status"] == "completed" and len(r["artifacts"]) > 0,
            "incomplete": r["status"] == "incomplete",
        }
        for r in grading["runs"]
    )
    incomplete = runs.pivot(index="task_id", columns="provider", values="incomplete")
    deliv = runs.pivot(index="task_id", columns="provider", values="delivered").reset_index()
    deliv = deliv.merge(tasks, on="task_id", validate="one_to_one")
    assert len(deliv) == 220 and deliv.openai.sum() == 211 and deliv.anthropic.sum() == 144

    pairs = pd.read_csv(GRADES / "reports" / "pairs.csv").merge(tasks, on="task_id", validate="many_to_one")
    assert len(pairs) == 440

    sectors = sorted(tasks.sector.unique(), key=lambda s: -deliv[deliv.sector == s].pipe(lambda g: g.openai.mean() - g.anthropic.mean()))
    rows = []
    for s in sectors:
        d = deliv[deliv.sector == s]
        gpt_only = int((d.openai & ~d.anthropic).sum())
        claude_only = int((~d.openai & d.anthropic).sum())
        disc = gpt_only + claude_only
        row = {
            "sector": s,
            "label": SHORT.get(s, s),
            "n": len(d),
            "gpt_delivered": int(d.openai.sum()),
            "claude_delivered": int(d.anthropic.sum()),
            "gpt_only": gpt_only,
            "claude_only": claude_only,
            "claude_incomplete": int(incomplete.loc[d.task_id, "anthropic"].sum()),
            "gpt_incomplete": int(incomplete.loc[d.task_id, "openai"].sum()),
            "delivery_p": binomtest(gpt_only, disc, 0.5).pvalue if disc else 1.0,
        }
        for judge, key in (("openai", "gpt_judge"), ("anthropic", "claude_judge")):
            p = pairs[(pairs.sector == s) & (pairs.judge_provider == judge)]
            c = p.outcome.value_counts()
            w, l = int(c.get("win", 0)), int(c.get("loss", 0))
            row[key] = {
                "gpt_better": w,
                "claude_better": l,
                "tie": int(c.get("tie", 0)),
                "unresolved": int(c.get("unresolved", 0)),
                "p": binomtest(w, w + l, 0.5).pvalue if w + l else 1.0,
            }
        rows.append(row)

    for adj, r in zip(holm([r["delivery_p"] for r in rows]), rows):
        r["delivery_p_holm"] = adj
    for key in ("gpt_judge", "claude_judge"):
        for adj, r in zip(holm([r[key]["p"] for r in rows]), rows):
            r[key]["p_holm"] = adj

    het = {}
    margin = deliv.openai.astype(int) - deliv.anthropic.astype(int)
    stat, p = heterogeneity(margin, deliv.sector)
    het["delivery"] = {"stat": stat, "p": p}
    claude_rate = deliv.anthropic.astype(int)
    stat, p = heterogeneity(claude_rate, deliv.sector)
    het["claude_delivery_rate"] = {"stat": stat, "p": p}
    sign = {"win": 1, "loss": -1, "tie": 0, "unresolved": 0}
    for judge, key in (("openai", "gpt_judge"), ("anthropic", "claude_judge")):
        p_ = pairs[pairs.judge_provider == judge]
        stat, p = heterogeneity(p_.outcome.map(sign), p_.sector)
        het[key] = {"stat": stat, "p": p}

    overall = {
        "delivery_p": binomtest(int(sum(r["gpt_only"] for r in rows)), int(sum(r["gpt_only"] + r["claude_only"] for r in rows)), 0.5).pvalue,
    }
    for key in ("gpt_judge", "claude_judge"):
        w = sum(r[key]["gpt_better"] for r in rows)
        l = sum(r[key]["claude_better"] for r in rows)
        overall[key] = {"gpt_better": w, "claude_better": l, "p": binomtest(w, w + l, 0.5).pvalue}

    OUT.write_text(json.dumps({"sectors": rows, "heterogeneity": het, "overall": overall}, indent=2), encoding="utf-8")

    print(f"{'sector':36} n  GPT Cla  g/c  p_holm | GPTjudge g-c p_holm | CLjudge g-c p_holm")
    for r in rows:
        g, c = r["gpt_judge"], r["claude_judge"]
        print(
            f"{r['label'][:36]:36} {r['n']} {r['gpt_delivered']:3} {r['claude_delivered']:3} {r['gpt_only']:2}/{r['claude_only']:<2} {r['delivery_p_holm']:.4f}"
            f" | {g['gpt_better']:2}-{g['claude_better']:<2} t{g['tie']} u{g['unresolved']:2} {g['p_holm']:.3f}"
            f" | {c['gpt_better']:2}-{c['claude_better']:<2} t{c['tie']} u{c['unresolved']:2} {c['p_holm']:.3f}"
        )
    print("heterogeneity", json.dumps(het))
    print("overall", json.dumps(overall))


if __name__ == "__main__":
    main()
