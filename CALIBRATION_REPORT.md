# GDPval Calibration and Grading Report

**Date:** November 9, 2026  
**Status:** All 24 calibration assessments completed. The user approved provisional full grading after reviewing this report; the remaining 846-assessment queue was launched. Completion is not yet established.

## Coverage

| Stage                       | Saved Result                                                                              |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| Primary generation          | 220 tasks, two generators, 440 attempts                                                   |
| Offline artifact inspection | 440 candidate evidence records completed; this does not certify every file is inspectable |
| Calibration                 | Six task pairs, 12 candidate outputs, two judges, 24/24 completed assessments             |
| Full planned grading        | At full-stage launch: 880 assignments, 24 completed, 846 pending, 10 unavailable             |
| Human calibration approval  | Explicit approval to proceed with provisional automated grading; not expert adjudication  |

The 10 unavailable assignments correspond to five primary provider/harness errors, each assigned to both judges. They are not semantic zeros. Calibration is part of the 880 assignments, not an additional batch. Pilot judgments and higher-budget Claude retries are excluded.

## Calibration Scores

Generators and judges use GPT-6 Astra (`gpt-6-astra`, low reasoning) and Claude Opus 5.5 (`databricks-claude-opus-5-5`, endpoint defaults). Each judge independently assessed both generators using the original task rubric and blinded artifact contexts.

Scores are percentages of available positive rubric points, retaining penalties. Ranges reflect unverified rubric evidence, not confidence intervals. Judges are not averaged into a consensus score.

| Task / Occupation                                 | GPT: OpenAI Judge | Claude: OpenAI Judge | GPT: Claude Judge | Claude: Claude Judge |
| ------------------------------------------------- | ----------------: | -------------------: | ----------------: | -------------------: |
| Real Estate Sales Agents                          |        13.2-28.3% |           35.8-67.9% |          3.8-3.8% |           49.1-88.7% |
| First-Line Supervisors of Retail Sales Workers    |        97.8-97.8% |           93.5-93.5% |        97.8-97.8% |           93.5-93.5% |
| Project Management Specialists                    |        54.7-94.2% |            0.0-51.2% |        59.3-75.6% |            0.0-91.9% |
| Compliance Officers                               |        70.4-74.1% |           70.4-74.1% |        74.1-77.8% |           74.1-77.8% |
| Medical Secretaries and Administrative Assistants |        63.0-91.4% |           64.2-91.4% |        75.3-97.5% |           86.4-98.8% |
| Editors                                           |       67.3-100.0% |            0.0-96.2% |       71.2-100.0% |             0.0-5.8% |

## Interpretation

- **Real estate:** both judges' intervals favor Claude. This is a task-level provisional result, not an occupation-wide finding.
- **Retail supervision:** both judges report GPT 97.8% versus Claude 93.5%, with no unverified score range.
- **Project management:** the OpenAI judge favors GPT; the Claude judge's intervals overlap. No agreement-backed winner.
- **Editors:** the Claude judge favors GPT, but the OpenAI judge leaves substantial uncertainty about Claude. Inspect the missing or partial deliverable evidence before interpreting the gap.
- **Compliance and medical administration:** intervals overlap under both judges. Equal overlapping ranges are unresolved, not established ties.

Overall, two task pairs have a direction supported by both judges; four remain unresolved under at least one judge. These six calibration tasks do not establish an overall provider winner or select the final 30-task slice.

## Calibration Quality and Recovery

The completed assessments contain **964 criterion decisions**, including **254 unverified decisions (26.3%)**. These are repeated decisions across candidates and judges, not 964 unique criteria. Completed assessment status establishes a saved, validated grade, not professional correctness.

The first launch yielded five completed, 13 blocked and six failed assessments. The 13 blocked contexts were recovered offline after permission errors. Databricks SDK authentication then confirmed an invalid OAuth refresh token; browser reauthentication and a no-inference SDK check restored access. Resuming within original budgets completed the remaining 19 assessments without replacing the five completed grades.

Completed-assessment records report **3,832,640 metered tokens**. This is not reconciled dollar spend or a complete accounting of failed/ambiguous requests, generation, retries, pilots or smoke tests.

## Limits and Required Review

The user explicitly approved proceeding despite the 26.3% unverified criterion decisions and unresolved comparisons, with no dollar ceiling and unchanged judges and parser limits. This is permission to run provisional automated grading, not a finding that its decisions are professionally correct. Human audit of criterion evidence, false passes/fails and disagreements remains outstanding. Particular priorities are the project-management and editor uncertainty gaps and the real-estate score differences between judges.

No live citation verification, Office layout rendering/recalculation, native audio listening, or video/CAD/PSD execution is provided by this grading policy. Parser errors and truncated previews remain uncertainty. Local parsers are not a hardened sandbox. No expert adjudication or professional-quality certification has occurred.

**Full-stage authorization:** [Approval record](../../gdpval-data/full-grading-approval.json) binds the explicit approval to calibration-results SHA-256 `428c3ee4fd404088e34b070d217af4945bc2673940e0281ebe6a61b9752cfd20`. The [batch launcher](run_full_grading.ps1) retains the frozen 24-assessment limit per launch and individual request budgets, preserves completed grades, stops on failures and exports reports after the queue ends. Live counts are in [grading state](../../gdpval-data/full_grades/primary-v1/grading.json); the counts above are the launch baseline.

## Evidence and Identity

- Primary experiment: `c6d44b16-80ed-4955-bba6-a34c1a10110d`.
- Grading workspace UUID: `51cfbb2b-90ca-42e6-8c61-1c28346844ee`.
- [Live grading checkpoints](../../gdpval-data/full_grades/primary-v1/grading.json).
- [Generated findings](../../gdpval-data/full_grades/primary-v1/reports/FINDINGS.md), [assessment table](../../gdpval-data/full_grades/primary-v1/reports/assessments.csv) and [criterion evidence](../../gdpval-data/full_grades/primary-v1/reports/criteria.csv). The offline export refresh completed with 24 completed, 846 not-run and 10 unavailable assignments; none remain failed or blocked.

Stable calibration task IDs, in table order: `11593a50-734d-4449-b5b4-f8986a133fd8`, `45c6237b-f9c9-4526-9a8d-6a5c404624ec`, `02aa1805-c658-4069-8a6a-02dec146063a`, `36d567ba-e205-4313-9756-931c6e4691fe`, `6d2c8e55-fe20-45c6-bdaf-93e676868503`, `ec2fccc9-b7f6-4c73-bf51-896fdb433cec`.
