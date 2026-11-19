# GPT vs. Claude: Provisional Failure Findings

**Updated:** November 18, 2026; full grading export saved November 11.  
**Scope:** 220 GDPval tasks, one primary attempt per model; 440 attempts total.  
**Status:** Primary generation and the provisional automated grading queue have finished. Of 880 judge assignments, 857 have valid assessments, nine have invalid grades, four failed and 10 are unavailable. The 30-item failure ledger has been hand-checked against the original files: 21 items were confirmed as drafted, seven reclassified and two judge fail calls rejected. The resulting ledger classifies 20 items as model failures, eight as grading/rubric issues, and two as rejected judge fail calls. This is one reviewer's audit, not independent expert adjudication or validation of all AI-judge grades. See the [item-by-item published audit](https://yasskin.github.io/evals-site/audit.html).

**Bottom line:** GPT completed with at least one artifact on 211/220 tasks versus Claude on 144/220, a 30.5-percentage-point delivery-proxy gap. Quality comparisons remain uncertain and judge-sensitive, not evidence of an overall quality winner. The independent higher-budget Claude experiment finished with 54/62 completed conversations, 53 with listed artifacts; it does not alter primary outcomes.

## 1. Failure classification, grouped by model

A failure here means an attempt did **not both complete its conversation and produce at least one artifact**. This identifies 9 GPT attempts and 76 Claude attempts. It is not a rubric-based failure rate: completed artifacts may still be wrong, incomplete artifacts may contain useful work, and one file may not satisfy a multi-file assignment.

The classes below are mutually exclusive. Artifact presence is recorded separately so partial outputs are not silently discarded.

### GPT-6 Astra (`gpt-6-astra`, low reasoning)

| Failure class | Attempts | With any artifact | Without artifacts | Evidence and interpretation |
| --- | ---: | ---: | ---: | --- |
| Truncated tool arguments followed by parsing failure | 3 | 0 | 3 | All three final saved responses have `stop=incomplete` and malformed JSON arguments for `web`. Parsing raises `JSONDecodeError`; the harness records `harness_error`. This is a model-output/adapter-handling boundary failure, not evidence that the underlying professional task was beyond the model. |
| Provider request timeout | 2 | 0 | 2 | Saved conversation errors report `APITimeoutError`, with no HTTP status. Infrastructure/transport failure; task competence cannot be inferred. |
| Conversation turn budget exhausted | 3 | 1 | 2 | All reach 14 turns while still requesting tools. The cumulative output ceiling is not reached. One attempt leaves two files; their presence does not establish a complete or correct deliverable. |
| Completed response without requested file | 1 | 0 | 1 | Film/video task: the final answer explicitly says no MP4 was produced and describes perceived download/export limitations. Treat those explanations as model-reported limitations, not independently proven tool incapabilities. |
| **Total operational failures** | **9** | **1** | **8** | **211/220 attempts completed with at least one artifact.** |

**Main GPT finding:** The observed failures are concentrated in truncation/parsing robustness, transport reliability, and a small number of unfinished workflows. Do not pool the five parser/transport failures into a claim of professional reasoning failure.

#### GPT evidence inventory

| Class | Occupation | Task ID | Run ID |
| --- | --- | --- | --- |
| Truncated `web` arguments | Registered Nurses | `dd724c67-8118-4b99-ab50-4761af705c3b` | `4ade8e59-18ad-41b9-aaa1-9ba1c0574bcd` |
| Truncated `web` arguments | Software Developers | `0e386e32-df20-4d1f-b536-7159bc409ad5` | `c9355053-fc65-4dec-ad31-7e0ec0136dff` |
| Truncated `web` arguments | Software Developers | `854f3814-681c-4950-91ac-55b0db0e3781` | `7a9e799e-7eea-42f9-b5ac-cd2490f03781` |
| Provider timeout | Lawyers | `aad21e4c-1d43-45fc-899a-97754a1b1b63` | `e6a1ebc2-5935-4109-b82e-49484ed855cc` |
| Provider timeout | Securities, Commodities, and Financial Services Sales Agents | `bb499d9c-0263-4684-9238-75e8e86077b1` | `6e9006a6-86a8-4fdb-a82f-d620ebfb44c3` |
| Turn limit; no artifact | Audio and Video Technicians | `4b894ae3-1f23-4560-b13d-07ed1132074e` | `a948433c-d04d-46e3-81a3-6a9327304690` |
| Turn limit; no artifact | Compliance Officers | `2696757c-1f8a-4959-8f0d-f5597b9e70fc` | `52449610-103d-4580-b297-107135b84ac4` |
| Turn limit; two partial artifacts | Mechanical Engineers | `5e2b6aab-f9fb-4dd6-a1a5-874ef1743909` | `6b6c9ecc-8874-4560-8066-707a0b46166d` |
| Completed without MP4 | Film and Video Editors | `c94452e4-39cd-4846-b73a-ab75933d1ad7` | `7b7254d8-238b-4f93-8e97-fc6827b5dad1` |

File presence alone does not establish the quality of the mechanical-engineering attempt; inspect its saved rubric assessments and original artifacts separately.

### Claude Opus 5.5 (`databricks-claude-opus-5-5`, endpoint-default reasoning)

| Failure class | Attempts | With any artifact | Without artifacts | Evidence and interpretation |
| --- | ---: | ---: | ---: | --- |
| Cumulative output budget exhausted | 33 | 3 | 30 | Reached 50,000 cumulative generated tokens while still in a tool-using workflow, without an earlier terminal-response classification or turn-limit classification. |
| Truncated terminal response | 14 | 1 | 13 | Final response has no tool calls and reports `length` or `incomplete`. The harness exits on that response. Some also reach the cumulative ceiling; this row does not establish that only the per-response cap caused termination. |
| Conversation turn budget exhausted | 15 | 5 | 10 | Reached 14 turns while still requesting tools. Some also reached another limit. |
| Tool budget exhausted; final prose instead of file | 13 | 0 | 13 | All have 24 executed tool calls, empty deliverable inventories, and nonempty final answers reporting that file creation did not run before the tool budget was exhausted. Several supply content to paste into the requested file format. |
| Content-filter termination recorded as completed | 1 | 0 | 1 | Software task: one response, `stop=content_filter`, reasoning-only content, no tool calls, empty final answer, no artifacts. The harness nevertheless records `completed`. The trace does not identify the filter's policy reason or whether it originated in the endpoint, serving layer, or model. |
| **Total operational failures** | **76** | **9** | **67** | **144/220 attempts completed with at least one artifact.** |

**Main Claude finding:** Budget management and completing the file-production step are the strongest observed operational gaps. Thirteen nominally completed runs exhausted tools before creating files. The filtered empty response is a separate serving/outcome-classification issue, not another budget failure.

#### Claude evidence examples

| Class | Occupation | Task ID | Run ID | Saved evidence |
| --- | --- | --- | --- | --- |
| Cumulative output limit; partial artifacts | Computer and Information Systems Managers | `a45bc83b-22f9-4def-8d89-9c5661b2b86f` | `959e5a2d-ddc9-4768-baa9-4abea7b4dd17` | 13 turns, 50,000 generated tokens, two artifacts. |
| Cumulative output limit; no artifact | General and Operations Managers | `6436ff9e-c5f2-47ba-9aaa-49d89b0594ab` | `93ac1f6c-51ab-4efb-a1db-1b3f5199ef9c` | Six turns, 50,000 generated tokens, no artifact. |
| Truncated terminal response | Medical and Health Services Managers | `74d6e8b0-f334-4e7e-af55-c095d5d4d1a6` | `276731b5-bb79-479c-b0a2-8151df683110` | 12 turns, 50,000 generated tokens, `length`, no artifact. |
| Turn limit; partial artifact | Audio and Video Technicians | `4b894ae3-1f23-4560-b13d-07ed1132074e` | `a2796549-bd24-499e-be5b-1c6875ebd67f` | 14 turns, 18 executed tool calls, one artifact. |
| Turn limit; no artifact | Financial and Investment Analysts | `46b34f78-6c06-4416-87e2-77b6d8b20ce9` | `0c1474c7-74f2-4065-9b98-f6e3d1227d32` | 14 turns, 24 executed tool calls, 40,479 generated tokens. |
| Tool budget before file creation | Administrative Services Managers | `f84ea6ac-8f9f-428c-b96c-d0884e30f7c7` | `8971b257-1420-4879-b37f-11b9e3b38d2d` | 24 executed tool calls; final answer supplies a table instead of a Word file. |
| Tool execution/workflow issue | Concierges | `a10ec48c-168e-476c-8fe3-23b2a5f616ac` | `5f935fa4-e13e-468f-b526-29af77faa878` | 24 executed tool calls; final answer reports script attempts sent without code. That specific explanation remains model-reported. |
| Content-filter termination | Software Developers | `0e386e32-df20-4d1f-b536-7159bc409ad5` | `10cce60c-d028-4cc8-ada1-f417c21f5409` | `content_filter`, reasoning-only response, empty answer, no artifact. |

#### All 13 Claude completed-but-tool-exhausted attempts

Each row has 24 executed tool calls and zero artifacts. These attempts are outside the 62 runs labeled `incomplete`, despite failing to produce requested files.

| Occupation | Task ID |
| --- | --- |
| Administrative Services Managers | `f84ea6ac-8f9f-428c-b96c-d0884e30f7c7` |
| Real Estate Sales Agents | `94925f49-36bc-42da-b45b-61078d329300` |
| Producers and Directors | `e14e32ba-d310-4d45-9b8a-6d73d0ece1ae` |
| Pharmacists | `f2986c1f-2bbf-4b83-bc93-624a9d617f45` |
| Real Estate Brokers | `6074bba3-7e3a-4b1c-b8c6-a15bb6695c3b` |
| Securities, Commodities, and Financial Services Sales Agents | `1d4672c8-b0a7-488f-905f-9ab4e25a19f7` |
| Shipping, Receiving, and Inventory Clerks | `5349dd7b-bf0a-4544-9a17-75b7013767e6` |
| Editors | `ec2fccc9-b7f6-4c73-bf51-896fdb433cec` |
| Concierges | `0e4fe8cd-16d0-4f41-8247-6385b4762582` |
| Concierges | `a10ec48c-168e-476c-8fe3-23b2a5f616ac` |
| Medical and Health Services Managers | `81db15ff-ceea-4f63-a1cd-06dc88114709` |
| Recreation Workers | `1bff4551-1d54-4e37-b2e0-d5c3f2ea4a45` |
| Pharmacists | `8384083a-c31b-4194-80ba-4d335a444918` |

## 2. Classification rules and attribution limits

For attempts already recorded as `incomplete`, apply this precedence:

1. **Truncated terminal response:** last response has no tool calls and `stop` is `length` or `incomplete`.
2. **Turn exhaustion:** otherwise, conversation has reached the 14-turn limit.
3. **Cumulative output exhaustion:** otherwise, generated tokens have reached 50,000.

These rules partition GPT's three incomplete attempts and Claude's 62 incomplete attempts. They name the observed stopping mechanism, not a uniquely proven underlying cause.

Keep overlapping diagnostics separate: among Claude's 62 incomplete attempts, 52 have a last response labeled `length`, 38 reach the cumulative output ceiling, 15 reach the turn limit, and five reach the executed-tool-call ceiling. These numbers must not be added together. In particular, a `length` response can still contain tool calls, so 52 length stops are not 52 truncated terminal responses.

For other statuses, inspect the saved error, last response, artifact inventory, and final answer. A nominal `completed` status does not override an empty artifact inventory or a content-filter stop. No original run labels or artifacts were changed during this analysis.

## 3. Delivery and resource findings

| Primary-run metric | GPT-6 Astra | Claude Opus 5.5 |
| --- | ---: | ---: |
| Conversation completed | 212/220 (96.4%) | 158/220 (71.8%) |
| Completed with at least one artifact | 211/220 (95.9%) | 144/220 (65.5%) |
| Any artifact, including unfinished attempts | 212/220 (96.4%) | 153/220 (69.5%) |
| Incomplete conversations | 3 | 62 |
| Completed conversations without artifacts | 1 | 14 |
| Provider/harness error statuses | 5 | 0 |
| Total artifact files | 314 | 236 |
| Median elapsed time per attempt | 129 seconds | 245 seconds |
| Metered input tokens | 18,575,907 | 43,725,861 |
| Metered output tokens | 1,131,470 | 5,185,626 |
| Metered total tokens | 19,707,377 | 48,911,487 |

Both models completed their conversations on 156 tasks; GPT alone completed on 56, Claude alone on two, and neither on six. These are completion outcomes, not quality wins.

The gap is not confined to unsupported modalities. On the 205 tasks without capability-limit flags, GPT completed 200 conversations and Claude 150. On the 15 flagged tasks, the counts were 12 and eight.

Financial and Investment Analysts shows the largest descriptive occupation-level completion gap: GPT 5/5, Claude 0/5. Financial Managers and Personal Financial Advisors each show GPT 5/5 versus Claude 1/5. Each occupation has only five tasks; these are inspection priorities, not evidence of generalized financial competence differences.

## 4. Full-run automated quality findings

### Coverage and uncertainty

The same two model configurations independently assessed both generators using original task rubrics, with wrapper identities hidden. Candidate style, filenames or content can still reveal identity. Calibration assessments are included in the 880 assignments, not additional to them.

| Assignment status | Count | Interpretation |
| --- | ---: | --- |
| Completed valid assessment | 857 | Schema/criterion validation passed; professional correctness is not established. |
| Invalid grade | 9 | Schema or criterion validation failed: five GPT candidates, four Claude candidates. |
| Failed | 4 | Judge-stage errors, all on GPT candidates; not generation failures or semantic zeros. |
| Unavailable | 10 | Five GPT primary provider/harness errors, each assigned to both judges. |
| Not-run / blocked | 0 / 0 | Queue processing finished, but not every assignment yielded a usable grade. |

Across valid assessments, there are **40,318 repeated criterion decisions**: 24,316 pass, 6,191 fail and **9,811 unverified (24.3%)**. These are decisions across candidates and judges, not unique rubric items or independent observations. Unverified evidence and the 23 non-valid/unavailable assignments remain uncertainty; neither should be silently discarded or scored as failure.

### Paired task outcomes

| Judge | GPT favored | Claude favored | Tie | Unresolved | Denominator |
| --- | ---: | ---: | ---: | ---: | ---: |
| OpenAI | 38 | 31 | 8 | 143 | 220 |
| Claude | 26 | 50 | 10 | 134 | 220 |

Cross-judge agreement favors GPT on **17 tasks** and Claude on **29**; both report ties on five. There are **eight opposite-direction decisions**, 121 pairs unresolved under both judges, and 40 other mixed outcomes. Agreement is provisional evidence, not human validation. The apparent direction among resolved pairs changes with judge, and most pairs remain unresolved.

### Task-weighted rubric score bounds

All-primary bounds below retain every original task, equal task weighting, original positive-point denominators and negative penalties. Unassessed work spans the rubric's logical bounds. Ranges reflect evidence uncertainty, not statistical confidence intervals.

| Judge | GPT all-primary bounds (n=220) | Claude all-primary bounds (n=220) | GPT completed-with-artifact bounds (n=211) | Claude completed-with-artifact bounds (n=144) |
| --- | ---: | ---: | ---: | ---: |
| OpenAI | 62.3-86.5% | 44.9-84.0% | 65.2-86.0% | 71.8-89.7% |
| Claude | 67.4-86.2% | 51.3-86.6% | 69.9-86.1% | 78.1-91.3% |

The conditional subsets contain different tasks and exclude many Claude non-deliveries. Their higher Claude lower bounds do **not** establish that Claude is better on matched completed tasks. All-primary intervals overlap under both judges; neither interval midpoints nor averaging judges creates an established overall winner.

Full grading uses local parser/view evidence, not comprehensive Office layout rendering/recalculation, live citation verification, native listening or video/CAD/PSD execution. Parser errors and truncated previews remain unverified. Human approval permitted provisional grading despite these limits; it did not certify grading accuracy. Prioritize the eight opposite-direction pairs, high-weight disagreements and agreed passes/fails for evidence audit before making substantive failure claims.

## 5. Larger-budget Claude retries: separate sensitivity analysis

The saved retry manifest now accounts for all **62 fresh attempts**: **54 completed (87.1%)**, four incomplete and four provider errors, with none left not-run. **53/62 completed with at least one listed artifact**; the same 53 are the only retry attempts with listed artifacts, totaling 80 files. One nominally completed retry has no artifact. These are manifest inventory counts, not a fresh byte-integrity check or proof that all requested deliverables are present and usable.

The retry protocol raises per-response output from 10,000 to 32,000 tokens, cumulative output from 50,000 to 150,000, turns from 14 to 28, and tool calls from 24 to 48. It also changes the HTTP read timeout. These are fresh conversations, not continuations of the original artifacts.

The observed recovery is consistent with sensitivity to the larger-budget configuration, but multiple settings and fresh sampling changed together. It does not identify which change was decisive or establish artifact quality; the primary grading export does not assess retries. Do not replace primary failures with retry successes or merge their counts into an equal-budget comparison. The retry selection also excludes the 14 Claude primary runs labeled completed without artifacts, so 54/62 is not a recovery rate for all Claude operational failures.

## 6. Implications for evaluation and training data

| Audience | Evidence-backed gap | Candidate data/evaluation opportunity | Boundary |
| --- | --- | --- | --- |
| OpenAI researchers | Three incomplete responses contain malformed `web` arguments and cause parser exceptions. | Tool-call examples with bounded arguments, truncation detection, safe recovery, and validation before execution. | Harness handling should also be improved and tested; dataset improvements alone will not fix transport timeouts. |
| OpenAI researchers | Three workflows reach the turn limit; one video assignment ends without its requested file. | Budget-aware completion and early artifact checkpoints; tasks with executable media-production environments. | Tool capability claims need independent verification. |
| Anthropic researchers | 62 incomplete primary runs plus 13 completed-but-tool-exhausted runs; higher-budget fresh retries completed 54/62 conversations, 53 with artifacts. | Long-horizon workflows with explicit budget accounting, prioritized research, early file creation, and final deliverable checks. | Reasoning allocation is not compute-matched; multiple retry settings changed, and retry quality is ungraded. |
| Both audiences | Completion status can conceal non-delivery, including a filtered empty response. | Outcome labels that distinguish delivered, partial, missing, filtered, malformed, and transport-failed attempts. | Serving-layer filters and harness status rules are not automatically model-training defects. |
| Both audiences | 9,811/40,318 valid-assessment criterion decisions are unverified; eight task pairs have opposite-direction judge outcomes. | Expert-reviewed task rubrics, source-linked correctness checks, inspectable gold artifacts, and blinded artifact comparisons. | These are evaluation-quality gaps, not automatically generator defects; human audit is still required. |

These are candidate data interventions, not demonstrated training benefits. Ground the final three proposals in inspected artifacts and affected-task denominators, distinguish critical defects from cosmetic issues, and specify a held-out acceptance test. Do not infer substantive professional failure classes from aggregate rubric scores alone.

## 7. Evidence, verification, and remaining work

Primary experiment ID: `c6d44b16-80ed-4955-bba6-a34c1a10110d`. Its directory has a different UUID:

- [Primary manifest](../../gdpval-data/full_runs/2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d/experiment.json)
- [Primary coverage](../../gdpval-data/full_runs/2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d/coverage.csv)
- [Primary raw runs](../../gdpval-data/full_runs/2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d/runs)
- [Retry manifest](../../gdpval-data/retry_runs/cf411732-395f-430f-941b-9f8ac208918f/experiment.json)
- [Grading state](../../gdpval-data/full_grades/primary-v1/grading.json)
- [Full grading findings](../../gdpval-data/full_grades/primary-v1/reports/FINDINGS.md)
- [Assessment coverage](../../gdpval-data/full_grades/primary-v1/reports/assessments.csv)
- [Criterion decisions and evidence](../../gdpval-data/full_grades/primary-v1/reports/criteria.csv)
- [Paired outcomes](../../gdpval-data/full_grades/primary-v1/reports/pairs.csv)
- [Quality bounds and denominators](../../gdpval-data/full_grades/primary-v1/reports/quality.csv)
- [Criterion disagreements](../../gdpval-data/full_grades/primary-v1/reports/disagreements.csv)
- [Stopping and artifact-status logic](pilot.py)

For each listed run ID, inspect `runs/<run_id>/conversation.json`, `run.json`, saved `response-*.json`, tool traces, and `answer.md`. Task IDs link the two models' attempts through the manifest.

The original operational analysis snapshot was taken at **2026-11-08 17:05:47 UTC**. Its primary manifest SHA-256 was `f1e8e5391b5571caa89aa9fb03073411d9d4409b13ecaf4e4c250de0a1ee2bd9`. The November 17 update reconciled current grading assignment states, exported quality/pair/criterion tables and retry manifest counts. The full export was saved November 11; grading UUID is `51cfbb2b-90ca-42e6-8c61-1c28346844ee`, and retry experiment UUID is `74a6f62c-1949-4067-9598-dddb9ff59232`.

In the November 8 operational audit, all 440 primary conversation statuses were checked against the manifest, and all **550 artifact files** passed saved size and SHA-256 checks. All 15 completed-without-artifact cases were inspected through their final answers and conversation metadata; the five GPT error cases were checked against saved errors and final available responses. The remaining incomplete runs were classified from saved stopping metadata. Those historical file-integrity checks were not repeated for this documentation update. Subsequent automated rubric assessment does not establish professional human review. No new inference was run for this update.

Shared primary limits were 14 turns, 24 executed tool calls, 10,000 output tokens per response, 50,000 cumulative generated tokens, and a 1,800-second scheduling deadline. GPT used low reasoning; Claude used endpoint defaults. Identical numerical limits do not establish equivalent compute allocation. GPT ran before Claude, introducing a timing confound for mutable endpoints and live research. Primary generation recorded **68,618,864 metered tokens combined**; this excludes grading, retries, pilots and smoke tests. Metered token totals do not establish dollar cost; total provider charges remain unreconciled, including possible unknown charges on ambiguous requests.

Audio lacks native listening, image conversion loses detail, and some task modalities are capability-limited. Local execution is not a hardened sandbox. The earlier six-task development pilot and its judgments remain separate evidence and are not pooled with this full run.

**Next analysis:** reconcile the 13 invalid/failed grades without silently retrying, audit judge disagreements and inspect requested deliverables, then apply the frozen-rule 30-task selection and review both outputs plus at least five seeded outside-slice pairs. Preserve original automated decisions and version any human corrections. Follow the [post-run analysis plan](PROJECT_PLAN.md); keep primary operational failures, provisional semantic scores, development pilots and retry results as separate reporting dimensions.
