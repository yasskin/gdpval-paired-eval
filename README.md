# GDPval paired evaluation: GPT-6 Astra vs Claude Opus 5.5

This is the code behind a paired evaluation on all 220 public [GDPval](https://huggingface.co/datasets/openai/gdpval) gold tasks. Each task was given to GPT-6 Astra (low reasoning) and to Claude Opus 5.5. Each model's deliverable files were then graded against the task rubrics by two blind judges, one GPT and one Claude.

**Results site:** https://yasskin.github.io/evals-site/

**One-page summary:** [RESULTS_ONE_PAGE.md](RESULTS_ONE_PAGE.md). It gives the headline findings, organized by the four parts of the take-home brief.

The results site explains the findings for non-specialists. This repository holds the code that produced them, so the work can be checked or re-run.

## What is not included
- **Raw run data** (model outputs, judge grades, deliverable files). It is large and contains copies of the GDPval reference files. Every script reads it from `gdpval-data/` and writes back there.
- **Credentials.** OpenAI uses the standard `OPENAI_API_KEY` variable. Claude is served through Databricks model serving, authenticated with a Databricks CLI OAuth profile. Set `DATABRICKS_CONFIG_PROFILE` (and optionally `DATABRICKS_HOST` to pin the expected workspace) before any paid stage.

## Layout
The scripts expect to live two levels below the root of an [openai/evals](https://github.com/openai/evals) checkout, next to its data folder:

```
<evals checkout>/
  gdpval-data/                      # GDPval parquet + reference files; runs and grades are written here
  turing/field_engineer_take_home_project/   # <- this repository
```

## Pipeline, in run order
Run Python with [uv](https://docs.astral.sh/uv/). The paid stages need explicit opt-in flags, and grading also needs a signed approval file.

| Stage | Script | Purpose |
| --- | --- | --- |
| 1. Pilot | `pilot.py prepare / generate`, `pilot_tools.py`, `pilot_worker.py` | Six-task development pilot; models get sandboxed Python tools to write files |
| | `pilot_grade.py`, `pilot_render.py`, `pilot_report.py` | Grade and summarize the pilot (see `PILOT.md`) |
| 2. Generate | `full_run.py prepare / run / status` | Both models on all 220 tasks; `watch_progress.py` monitors |
| | `retry_claude.py prepare / run` | One retry for Claude runs cut off before saving a file |
| 3. Grade | `full_grade.py policy / prepare / inspect / grade / aggregate / report` | Evidence extraction, two blind judges per item, paired report |
| | `run_full_grading.ps1`, `full_grade_worker.py` | Batch driver with approval checks and checkpointing |
| | `test_full_grade.py` | Offline tests: `uv run python -m unittest test_full_grade` |
| 4. Analyze | `analyze_sectors.py`, `analyze_plan_items.py` | Sector comparison, judge agreement, cost, failure-ledger candidates |
| 5. Site | `build_site_tasks.py`, `build_site_example.py`, `build_site_sectors.py`, `build_site_plan.py` | Generate the results-site pages and CSVs |
| | `build_audit_packet.py` | Worksheet for the hand audit of the failure ledger |

Analysis and site scripts use only the standard library plus pandas, pyarrow and scipy, for example:

```
uv run --no-project --with pandas --with pyarrow --with scipy python turing/field_engineer_take_home_project/analyze_sectors.py
```

## Documents
- `PROJECT_PLAN.md`: plan, decisions and run log
- `PILOT.md`: pilot protocol
- `CALIBRATION_REPORT.md`: judge calibration sample that was reviewed before full grading
- `RESULTS_ONE_PAGE.md`: one-page summary of the findings
- `PROVISIONAL_FAILURE_FINDINGS.md`: detailed failure findings
- `plan_items.json`: analysis output used by the site generators

All findings are provisional. Judge scores are never averaged across the two judges.