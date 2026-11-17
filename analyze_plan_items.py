"""Offline analyses backing the site's plan-coverage pages. No inference is run.

Produces plan_items.json (cost by stage, frozen-rule slice ranking, judge reliability,
quality-failure candidates) and site/data/status_matrix.csv (the 220 x 2 status matrix).
"""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from scipy.stats import binomtest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA = REPO / "gdpval-data"
PRIMARY = DATA / "full_runs" / "2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d"
GRADES = DATA / "full_grades" / "primary-v1"
RETRY = DATA / "retry_runs"
PARQUET = DATA / "data" / "train-00000-of-00001.parquet"
OUT = HERE / "plan_items.json"
MATRIX = HERE / "site" / "data" / "status_matrix.csv"

# List prices per 1M tokens, checked 2026-11-17 (OpenAI API pricing page; Anthropic list price).
PRICES = {
    "openai": {"input": 10.00, "cached": 1.00, "cache_write": 12.50, "output": 50.00},
    "anthropic": {"input": 4.00, "cached": 0.20, "cache_write": 5.00, "output": 20.00},
}
LONG_PROMPT = 272_000  # OpenAI: 2x input/cache and 1.5x output for the whole request above this


def norm_usage(u):
    """Return (provider, uncached_input, cached, cache_write, output) for one request's usage."""
    if "input_tokens" in u:
        det = u.get("input_tokens_details") or {}
        cached, write = det.get("cached_tokens", 0) or 0, det.get("cache_write_tokens", 0) or 0
        total_in = u["input_tokens"]
        return "openai", total_in - cached - write, cached, write, u["output_tokens"], total_in
    return ("anthropic", u.get("prompt_tokens", 0), u.get("cache_read_input_tokens", 0) or 0,
            u.get("cache_creation_input_tokens", 0) or 0, u.get("completion_tokens", 0), u.get("prompt_tokens", 0))


def usd(provider, unc, cached, write, out, total_in):
    p = PRICES[provider]
    mi = mo = 1.0
    if provider == "openai" and total_in > LONG_PROMPT:
        mi, mo = 2.0, 1.5
    return (unc * p["input"] * mi + cached * p["cached"] * mi + write * p["cache_write"] * mi + out * p["output"] * mo) / 1e6


def ledger_usage(root):
    """Sum request-ledger usage under root; requests without usage are counted by status."""
    acc = defaultdict(Counter)
    for f in root.glob("**/requests/**/*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        u = d.get("usage")
        if not u:
            acc["no_usage"]["requests"] += 1
            acc["no_usage"][d.get("status") or "unknown"] += 1
            continue
        prov, unc, cached, write, out, tin = norm_usage(u)
        a = acc[prov]
        a["requests"] += 1
        a["input"] += unc
        a["cached"] += cached
        a["cache_write"] += write
        a["output"] += out
        a["long_prompt_requests"] += tin > LONG_PROMPT and prov == "openai"
        a["usd_micro"] += round(usd(prov, unc, cached, write, out, tin) * 1e6)
    return {k: dict(v) for k, v in acc.items()}


def cost():
    stages = {
        "primary_generation": ledger_usage(PRIMARY),
        "primary_grading": ledger_usage(GRADES),
        "claude_retries": ledger_usage(RETRY),
    }
    # Pilot ledgers predate per-request cache fields; use the pilot report's totals, priced as uncached input.
    pilot = {
        "openai": {"requests": 52 + 65, "input": 457514 + 880132, "output": 29026 + 44526},
        "anthropic": {"requests": 57 + 75, "input": 897171 + 1224231, "output": 106117 + 72059},
    }
    for prov, a in pilot.items():
        a["usd_micro"] = round(usd(prov, a["input"], 0, 0, a["output"], 0) * 1e6)
    stages["pilot_six_tasks"] = pilot
    return stages


def main():
    tasks = pd.read_parquet(PARQUET, columns=["task_id", "sector", "occupation"])
    sector = dict(zip(tasks.task_id, tasks.sector))
    runs = {}
    for f in (PRIMARY / "runs").glob("*/run.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        runs[(r["task_id"], r["provider"])] = r
    pairs = pd.read_csv(GRADES / "reports" / "pairs.csv")
    assess = pd.read_csv(GRADES / "reports" / "assessments.csv")

    # ---------- 220 x 2 status matrix ----------
    label = {"win": "GPT better", "loss": "Claude better", "tie": "Exact tie", "unresolved": "Can't tell"}
    pv = pairs.pivot(index="task_id", columns="judge_provider", values="outcome")
    rows = []
    for t in tasks.itertuples():
        g, c = runs[(t.task_id, "openai")], runs[(t.task_id, "anthropic")]
        rows.append({
            "task_id": t.task_id, "sector": t.sector, "occupation": t.occupation,
            "gpt_status": g["status"], "gpt_files": len(g["artifacts"]),
            "claude_status": c["status"], "claude_files": len(c["artifacts"]),
            "gpt_judge": label[pv.loc[t.task_id, "openai"]],
            "claude_judge": label[pv.loc[t.task_id, "anthropic"]],
        })
    MATRIX.parent.mkdir(parents=True, exist_ok=True)
    with MATRIX.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["sector"], r["occupation"], r["task_id"])))

    # ---------- frozen slice-selection rule ----------
    ok = assess[assess.status == "completed"].groupby("task_id").size()
    pj = {j: pairs[pairs.judge_provider == j].set_index("task_id") for j in ("openai", "anthropic")}

    def conservative(row):
        if row["outcome"] == "win":
            return row["difference_lower"]
        if row["outcome"] == "loss":
            return row["difference_upper"]
        return 0.0

    per_task = []
    for t in tasks.itertuples():
        a, b = pj["openai"].loc[t.task_id], pj["anthropic"].loc[t.task_id]
        same = a["outcome"] == b["outcome"] and a["outcome"] in ("win", "loss")
        da, db = conservative(a), conservative(b)
        backed = (min(abs(da), abs(db)) * (1 if a["outcome"] == "win" else -1)) if same else 0.0
        inspectable = (len(runs[(t.task_id, "openai")]["artifacts"]) > 0
                       and len(runs[(t.task_id, "anthropic")]["artifacts"]) > 0
                       and ok.get(t.task_id, 0) == 4)
        per_task.append({"task_id": t.task_id, "occupation": t.occupation, "sector": t.sector,
                         "backed": backed, "inspectable": inspectable,
                         "direction": ("GPT" if backed > 0 else "Claude") if same else None})
    pt = pd.DataFrame(per_task)
    occ = (pt.groupby("occupation")
             .agg(sector=("sector", "first"), mean_abs=("backed", lambda s: s.abs().mean()),
                  coverage=("inspectable", "sum"), gpt=("direction", lambda s: (s == "GPT").sum()),
                  claude=("direction", lambda s: (s == "Claude").sum()))
             .reset_index())
    occ["eligible"] = occ.coverage >= 4
    occ = occ.sort_values(["mean_abs", "coverage", "occupation"], ascending=[False, False, True])
    occ["rank"] = range(1, len(occ) + 1)
    selected = occ[occ.eligible].head(6).occupation.tolist()

    # ---------- judge reliability ----------
    both = pairs.pivot(index="task_id", columns="judge_provider", values="outcome")
    agree = Counter()
    for o, a in zip(both.openai, both.anthropic):
        if o == a:
            agree[{"win": "both_gpt", "loss": "both_claude", "tie": "both_tie", "unresolved": "both_unresolved"}[o]] += 1
        elif {o, a} == {"win", "loss"}:
            agree["opposite"] += 1
        else:
            agree["mixed"] += 1
    selfpref = {}
    for j, own_win in (("openai", "win"), ("anthropic", "loss")):
        s = pairs[pairs.judge_provider == j].outcome.value_counts()
        own, other = int(s.get(own_win, 0)), int(s.get("loss" if own_win == "win" else "win", 0))
        selfpref[j] = {"own": own, "other": other, "p": binomtest(own, own + other).pvalue}

    crit = pd.read_csv(GRADES / "reports" / "criteria.csv",
                       usecols=["assessment_id", "task_id", "run_id", "judge_provider", "assessment_status",
                                "rubric_item_id", "weight", "verdict", "evidence", "rationale"])
    crit = crit[crit.assessment_status == "completed"]
    gen = {r["run_id"]: p for (t, p), r in runs.items()}
    crit["generator"] = crit.run_id.map(gen)

    def fmt(run_id):
        exts = sorted({Path(a["path"]).suffix.lower().lstrip(".") for a in runs_by_id[run_id]["artifacts"]})
        if not exts:
            return "no file"
        if len(exts) > 1:
            return "multiple formats"
        e = exts[0]
        return {"doc": "docx", "xls": "xlsx", "ppt": "pptx", "markdown": "md"}.get(e, e)

    runs_by_id = {r["run_id"]: r for r in runs.values()}
    crit["format"] = crit.run_id.map(fmt)
    unv = crit.assign(u=crit.verdict == "unverified")
    by_jg = unv.groupby(["judge_provider", "generator"]).u.agg(["mean", "size"]).reset_index()
    by_fmt = unv.groupby("format").u.agg(["mean", "size"]).reset_index().sort_values("size", ascending=False)
    piv = crit.pivot_table(index=["run_id", "rubric_item_id"], columns="judge_provider",
                           values="verdict", aggfunc="first").dropna()
    same_verdict = float((piv.openai == piv.anthropic).mean())
    pf = piv[piv.openai.isin(["pass", "fail"]) & piv.anthropic.isin(["pass", "fail"])]
    po = float((pf.openai == pf.anthropic).mean())
    pe = sum(float((pf.openai == v).mean()) * float((pf.anthropic == v).mean()) for v in ("pass", "fail"))
    kappa = (po - pe) / (1 - pe)

    # ---------- quality-failure candidates ----------
    rubric_text, total_pos = {}, {}
    for d in (GRADES / "tasks").iterdir():
        items = json.loads((d / "rubric.json").read_text(encoding="utf-8"))
        total_pos[d.name] = sum(i["score"] for i in items if i["score"] > 0)
        for i in items:
            rubric_text[i["rubric_item_id"]] = i["criterion"]
    delivered = {k for k, r in runs.items() if r["status"] == "completed" and r["artifacts"]}
    cpos = crit[crit.weight > 0]
    v = cpos.pivot_table(index=["task_id", "rubric_item_id"], columns=["generator", "judge_provider"],
                         values="verdict", aggfunc="first")
    rat = {(r.run_id, r.rubric_item_id, r.judge_provider): (r.rationale, r.evidence) for r in cpos.itertuples()}
    weight = dict(zip(cpos.rubric_item_id, cpos.weight))
    cands = []
    for (task, item), row in v.iterrows():
        if (task, "openai") not in delivered or (task, "anthropic") not in delivered:
            continue
        try:
            g = (row[("openai", "openai")], row[("openai", "anthropic")])
            c = (row[("anthropic", "openai")], row[("anthropic", "anthropic")])
        except KeyError:
            continue
        for loser, lv, wv in (("openai", g, c), ("anthropic", c, g)):
            shared = lv == ("fail", "fail") and wv == ("fail", "fail")
            if lv == ("fail", "fail") and (wv == ("pass", "pass") or shared):
                run = runs[(task, loser)]
                cands.append({
                    "task_id": task, "occupation": tasks.set_index("task_id").occupation[task],
                    "sector": sector[task], "model": "shared" if shared else loser,
                    "rubric_item_id": item, "criterion": rubric_text[item],
                    "weight": weight[item], "share": weight[item] / total_pos[task],
                    "run_id": run["run_id"], "files": [Path(a["path"]).name for a in run["artifacts"]],
                    "gpt_judge": rat.get((run["run_id"], item, "openai")),
                    "claude_judge": rat.get((run["run_id"], item, "anthropic")),
                })
                if shared:
                    break
    cdf = pd.DataFrame(cands).sort_values("share", ascending=False)
    cdf = cdf.drop_duplicates(["task_id", "model"])  # one item per task and model

    OUT.write_text(json.dumps({
        "cost": cost(),
        "prices": PRICES,
        "slice": {"ranking": occ.to_dict("records"), "selected": selected,
                  "selected_tasks": pt[pt.occupation.isin(selected)].to_dict("records"),
                  "eligible": int(occ.eligible.sum())},
        "judges": {"agreement": dict(agree), "self_preference": selfpref,
                   "unverified_by_judge_generator": by_jg.to_dict("records"),
                   "unverified_by_format": by_fmt.to_dict("records"),
                   "criterion_same_verdict": same_verdict, "pass_fail_agreement": po, "kappa": kappa,
                   "criterion_pairs": int(len(piv)), "pass_fail_pairs": int(len(pf))},
        "candidates": {m: cdf[cdf.model == m].head(40).to_dict("records") for m in ("openai", "anthropic", "shared")},
        "candidate_pool": cdf.model.value_counts().to_dict(),
    }, indent=1, default=str), encoding="utf-8")
    print("wrote", OUT, "and", MATRIX)


if __name__ == "__main__":
    main()
