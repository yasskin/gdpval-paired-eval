import argparse
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from pilot import MODELS, PROJECT, digest, now, save, tasks
from pilot_grade import validate_grade


def agreement_bounds(submissions, rubric):
    if len(submissions) != 2:
        return None
    decisions = [{item["rubric_item_id"]: item["verdict"] for item in submission["criteria"]} for submission in submissions]
    lower = upper = 0.0
    disagreements = []
    agreed = 0
    denominator = sum(float(item["score"]) for item in rubric if float(item["score"]) > 0)
    for item in rubric:
        identity = item["rubric_item_id"]
        weight = float(item["score"])
        first, second = decisions[0][identity], decisions[1][identity]
        if first == second and first != "unverified":
            agreed += 1
            if first == "pass":
                lower += weight
                upper += weight
        else:
            lower += min(0, weight)
            upper += max(0, weight)
            if first != second:
                disagreements.append(identity)
    return {"lower_percent": 100 * lower / denominator, "upper_percent": 100 * upper / denominator, "agreed_verified_criteria": agreed, "criterion_count": len(rubric), "disagreement_criterion_ids": disagreements}


def usage_totals(records):
    totals = defaultdict(lambda: {"requests_with_usage": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
    for provider, usage in records:
        totals[provider]["requests_with_usage"] += 1
        totals[provider]["input_tokens"] += usage.get("input_tokens", usage.get("prompt_tokens", 0))
        totals[provider]["output_tokens"] += usage.get("output_tokens", usage.get("completion_tokens", 0))
        totals[provider]["total_tokens"] += usage.get("total_tokens", 0)
    return dict(totals)


def build(root):
    manifest = json.loads((root / "experiment.json").read_text())
    collection = tasks()
    assert len(manifest["runs"]) == 12
    assert len({run["run_id"] for run in manifest["runs"]}) == 12
    assert len({run["task_id"] for run in manifest["runs"]}) == 6
    assert len(manifest["judgments"]) == 24
    assert all(run["status"] not in {"running", "not_run"} for run in manifest["runs"])
    assert all(assessment["status"] not in {"running", "not_run"} for assessment in manifest["judgments"])
    report = {
        "experiment_id": manifest["experiment_id"],
        "generated_at": now(),
        "models": MODELS,
        "generation_status": dict(Counter(run["status"] for run in manifest["runs"])),
        "judgment_status": dict(Counter(assessment["status"] for assessment in manifest["judgments"])),
        "generation_usage": usage_totals((run["provider"], usage) for run in manifest["runs"] for usage in run.get("usage", [])),
        "grading_usage": usage_totals((assessment["judge_provider"], usage) for assessment in manifest["judgments"] for usage in assessment.get("usage", [])),
        "usd_cost": None,
        "cost_note": "Metered usage only; dollar charges not reconciled. Three original CLI-timeout request outcomes/usages are unknown. Earlier smoke tests and integration probes are separate costs.",
        "protocol_amendments": manifest.get("protocol_amendments", []),
        "limitations": [
            "Development pilot with protocol repairs, not a frozen confirmatory benchmark",
            "23/24 valid uncalibrated, unofficial assessments; one judge turn-limited",
            "Local execution is not a hardened sandbox",
            "Default Claude reasoning versus low GPT reasoning: unequal compute allocation possible",
            "Three Claude transport continuations after CLI inactivity timeouts; original failed requests may have been billed",
            "No native audio listening; perceptual audio grades require a listener",
            "Judge disagreements remain unresolved; no consensus winner is manufactured",
            "Image conversions lose detail; public search/retrieval can be weak or unavailable",
            "Human artifact review is partial and non-expert; no professional electrical/financial/audio validation",
        ],
        "tasks": [],
        "artifact_hashes_verified": 0,
    }
    for selection in manifest["selection"]:
        task = collection[selection["task_id"]]
        rubric = json.loads(task["rubric_json"])
        paired = {"task_id": task["task_id"], "occupation": task["occupation"], "selection_reason": selection["reason"], "runs": []}
        for run in [run for run in manifest["runs"] if run["task_id"] == task["task_id"]]:
            directory = root / "runs" / run["run_id"]
            record = {**run, "assessments": []}
            for artifact in run["artifacts"]:
                assert digest(directory / artifact["path"]) == artifact["sha256"], "Original artifact hash changed"
                report["artifact_hashes_verified"] += 1
            inspection = json.loads((directory / "evidence.json").read_text())
            record["inspection"] = inspection
            submissions = []
            for assessment in [assessment for assessment in manifest["judgments"] if assessment["run_id"] == run["run_id"]]:
                record["assessments"].append(assessment)
                if assessment["status"] == "completed":
                    submission = json.loads((root / "judgments" / assessment["assessment_id"] / "grade-submission.json").read_text())
                    assert validate_grade(submission, rubric) == assessment["score"], "Saved grading arithmetic mismatch"
                    submissions.append(submission)
            record["agreement_bounds"] = agreement_bounds(submissions, rubric)
            paired["runs"].append(record)
        report["tasks"].append(paired)
    return report


def score_text(assessment):
    if "score" not in assessment:
        return assessment["status"]
    score = assessment["score"]
    lower, upper = score["lower_percent"], score["upper_percent"]
    return f"{lower:.1f}%" if lower == upper else f"{lower:.1f} to {upper:.1f}%"


def write_report(root, output):
    report = build(root)
    save(output.with_suffix(".json"), report)
    raw_link = "../../gdpval-data/pilots/" + report["experiment_id"]
    lines = [
        "# Six-Task Paired Pilot Results",
        "",
        f"Experiment UUID: `{report['experiment_id']}`",
        "",
        "**Development pilot only. Do not launch the full run from these results.**",
        "",
        "Twelve generation attempts and 24 judge attempts are retained. Nine generation conversations completed and three reached limits; ten artifacts were produced. Twenty-three assessments passed schema/criterion/arithmetic checks; one Claude judge reached its turn limit. Artifact existence is not a professional-quality verdict.",
        "",
        "Models: `gpt-6-astra` (low reasoning) and `databricks-claude-opus-5-5` (endpoint default). Both used the same local Python, web and image tools. Judges used the same two models separately, with generator identity hidden.",
        "",
        "## Paired Scores",
        "",
        "Scores are weighted original-rubric percentages. A range is unresolved evidence, not a confidence interval. Each generator has two separate judge columns; disagreements are deliberately not averaged away. Negative bounds retain rubric penalties.",
        "",
        "| Coverage | Generator | Generation | OpenAI Judge | Claude Judge | Artifact |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for task in report["tasks"]:
        for run in sorted(task["runs"], key=lambda item: item["provider"]):
            assessments = {assessment["judge_provider"]: assessment for assessment in run["assessments"]}
            artifacts = []
            for artifact in run["artifacts"]:
                target = raw_link + "/runs/" + run["run_id"] + "/" + artifact["path"]
                artifacts.append("[" + Path(artifact["path"]).suffix[1:].upper() + "](" + target.replace(" ", "%20") + ")")
            coverage = {"Administrative Services Managers": "Research", "Property, Real Estate, and Community Association Managers": "PDF / Word", "Financial Managers": "Finance / XLSX", "Sales Managers": "Sales / Slides", "Industrial Engineers": "Image / Schematic", "Audio and Video Technicians": "Audio / WAV"}[task["occupation"]]
            lines.append(f"| {coverage} | {'GPT' if run['provider'] == 'openai' else 'Claude'} | {run['status']} | {score_text(assessments['openai'])} | {score_text(assessments['anthropic'])} | {', '.join(artifacts) or 'Missing'} |")
    lines.extend(
        [
            "",
            "## Findings",
            "",
            "- Research: both judges favored Claude. Its Word output actually renders to one page; GPT's renders to two, violating the one-page requirement. Source validity still needs independent auditing.",
            "- Financial modeling: both produced recalculable workbooks and received high provisional scores, with a small GPT lead from each judge. Formula/error and scenario validation remain necessary before a professional-quality claim.",
            "- Sales: GPT produced 13 PDF pages; Claude's turn-limited output has 17. The judges disagree sharply on Claude (59.4% versus 98.0%). This is a grading-calibration issue to resolve, not grounds to select whichever score supports a story.",
            "- Engineering: GPT produced a one-page schematic; Claude exhausted its response without producing the requested file. High judge scores do NOT certify safe wiring or IEC compliance; professional review is required.",
            "- Audio: GPT produced stereo PCM-24 at 48 kHz, measured at approximately -16.00 integrated LUFS and -0.45 dBFS sample peak. Claude produced no final WAV within 14 turns. Neither result establishes perceptual mix quality, true-peak compliance, or correct musical editing; one GPT-artifact judge remains incomplete.",
            "- Operational lesson: the Databricks CLI terminated three requests after one minute of inactivity. OAuth-authenticated REST with a longer explicit timeout allowed logged continuations. Two structured final-message serialization failures were recovered from saved responses with no new inference.",
            "",
            "## Usage and Coverage",
            "",
            "| Stage / Provider | Requests With Usage | Input Tokens | Output Tokens | Total Tokens |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for stage in ("generation", "grading"):
        for provider, usage in report[stage + "_usage"].items():
            lines.append(f"| {stage} / {provider} | {usage['requests_with_usage']} | {usage['input_tokens']} | {usage['output_tokens']} | {usage['total_tokens']} |")
    lines.extend(
        [
            "",
            report["cost_note"],
            "",
            "## Before Scaling",
            "",
            "Resolve the sales/property-manager grading disagreements, inspect formula/scenario errors, add native audio/listener coverage or formally declare it unsupported, choose comparable reasoning budgets, and rerun the pilot under one frozen transport/tool protocol. Use a real isolated runtime and the separate full-run approval gates. Do not treat this six-task selection or its mixed development protocol as a provider-wide ranking.",
            "",
            "The preserved original artifacts passed SHA-256 checks. Criterion UUID coverage and grading arithmetic were revalidated locally. This report is reproducible from saved responses without further model calls.",
            "",
            "## Evidence",
            "",
            f"[Experiment manifest]({raw_link}/experiment.json) contains UUID-linked attempts, hashes, versions, usage, selection and repair history. Raw artifacts and judge traces remain in the ignored dataset directory. The shareable JSON report contains the paired status/score data and inspection records, but no API credentials.",
            "",
        ]
    )
    output.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"experiment_id": report["experiment_id"], "generation_status": report["generation_status"], "judgment_status": report["judgment_status"], "artifact_hashes_verified": report["artifact_hashes_verified"], "report": str(output.with_suffix(".md"))}))


class ReportTests(unittest.TestCase):
    def test_disagreement_is_not_consensus(self):
        rubric = [{"rubric_item_id": "criterion", "score": 2}]
        submissions = [{"criteria": [{"rubric_item_id": "criterion", "verdict": verdict}]} for verdict in ("pass", "fail")]
        bounds = agreement_bounds(submissions, rubric)
        self.assertEqual((bounds["lower_percent"], bounds["upper_percent"]), (0, 100))
        self.assertEqual(bounds["disagreement_criterion_ids"], ["criterion"])

    def test_missing_judge_stays_missing(self):
        self.assertIsNone(agreement_bounds([], [{"rubric_item_id": "criterion", "score": 2}]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=Path)
    parser.add_argument("--output", type=Path, default=PROJECT / "PILOT_RESULTS")
    args = parser.parse_args()
    write_report(args.experiment.resolve(), args.output)
