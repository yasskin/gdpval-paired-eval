# GDPval: OpenAI vs. Anthropic Project Plan

Status checked November 17, 2026: all 440 primary generation attempts and the provisional grading queue have finished. The saved November 11 grading export contains 857 valid assessments, nine invalid grades, four failed assessments and 10 unavailable assignments out of 880; no assignments remain not-run. GPT completed 212/220 conversations and Claude 158/220, but completion is not deliverable quality. The separate higher-budget Claude experiment finished with 54 completed, four incomplete and four provider-error retries. Primary outcomes remain unchanged. The next stage is evidence audit, paired analysis and presentation-slice selection, not another generation batch. Professional adjudication and final findings remain outstanding.

## Objective

Run the entire 220-task public GDPval gold subset against one OpenAI model and one Anthropic model, then select an evidence-rich, 30-task slice for a researcher-facing presentation. Answer: **Where do these two model-and-tool configurations differ in producing usable professional deliverables, and which observed gaps could better data plausibly address?**

The goal is not to make either provider win. Select for clear, reproducible differences in either direction, retain ties and shared failures, and distinguish model weaknesses from tool, harness and grading weaknesses. Findings apply to the exact tested configurations, not to all models from either company.

## Scope and Starting Evidence

- Local dataset inventory: 220 unique tasks, 44 occupations, exactly five tasks per occupation.
- 125 tasks include reference files; 95 do not. Reference formats include spreadsheets, PDFs, Word documents, images, audio, video, Photoshop and STEP files.
- Expert deliverable formats include spreadsheets, PDFs, Word documents, presentations, video and code. These are inventory hints, not permission to expose expert answers to the generator or require its filenames to match them.
- The existing single-task runner is an OpenAI-only prototype that rejects reference files. It is not a full-dataset or cross-provider harness.
- The earlier Administrative Services Managers run is a pilot, not comparative evidence: only one OpenAI model was tested. Its provisional local grade was 39/58, with access-related uncertainty. The actual rendered document had two pages even though initial Word statistics reported one. Citation attribution and layout were observed issues.
- Recheck and preserve the current pilot files before reusing them. Do not mix its earlier protocol with the primary paired experiment.

The brief favors a carefully inspected slice rather than all 220 tasks. We will satisfy the broader run goal through automation, but devote manual analysis to the selected slice. If the full run threatens the deadline or budget, narrow the claim transparently rather than claim incomplete coverage as a finished benchmark.

## Experiment Protocol

### Primary Model Comparison

Proposed primary pairing: **GPT-6 Astra vs. Claude Opus 5.5**, using the following available access routes:

| Side      | Model / endpoint ID          | Access route                                                              | Verification so far                                                                                                                |
| --------- | ---------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| OpenAI    | `gpt-6-astra`                | OpenAI API with the configured key                                        | Inference and a synthetic function-call response passed; 85 total tokens                                                           |
| Anthropic | `databricks-claude-opus-5-5` | Direct Databricks model serving with OAuth profile `$DATABRICKS_CONFIG_PROFILE` | Inference and a synthetic function-call response passed through the CLI REST route with automatic tool selection; 509 total tokens |

This is a strong-model comparison using our available endpoints, not a claim that both are each provider's absolute latest flagship or have equal compute. Do not substitute Databricks GPT-OSS for the selected OpenAI model. Keep the primary experiment to this one pair; additional model pairs require a separately approved scope and budget.

Claude access does not require MCP or a working direct Anthropic API key. Use the Databricks SDK and the existing OAuth profile; refresh login and discover endpoints as documented in [the repository agent notes](../../AGENTS.md). Omit `temperature` for Claude as documented by CopilotIQ. Confirm that use of the corporate Databricks workspace is approved for the take-home workload before paid execution.

Before the six-task pilot, run one small, budget-approved inference smoke test per selected model. Check authentication, response/usage capture and the API capabilities needed by the shared harness, including tool calls. Discovery and `READY` status do not establish invocation permission or tool/modality compatibility. A failed gate blocks this pairing until resolved or explicitly revised; do not silently fall back to another model.

Smoke-test result, recorded at 2026-11-05 03:54-03:55 UTC: both selected models returned `report_smoke_test` with `{"message":"SMOKE_TEST_OK"}`. Each request was capped at 256 output tokens. GPT used low reasoning effort and forced function selection (5.293 seconds); Claude rejected forced selection, then passed with `tool_choice: "auto"` (3.517 seconds). No tools were executed and no GDPval tasks were run. The two successful responses reported 594 total tokens combined; the rejected request returned no usage metadata, and dollar cost is not yet reconciled. These checks do not establish a complete tool/result round trip, matched automatic-selection behavior, native SDK compatibility, file/modality support or artifact creation. Preserve all three attempts in [the smoke-test record](inference-smoke-test.json); the pilot and full-run approval gates remain unchanged.

### Models and Fairness

1. Verify inference access to the selected OpenAI API model and Databricks-hosted Claude endpoint without logging credentials. The earlier OpenAI pilot and the current model/endpoint listings are not substitutes for these smoke tests.
2. Freeze the selected model IDs, snapshot/version where available, API versions, serving route, provider-specific reasoning settings and configuration before scored runs. Capture returned model/version metadata and timestamps; document alias/version drift if immutable snapshots are unavailable. Do not default to the old OpenAI pilot model merely because it already ran successfully.
3. Use the same task prompt, reference bytes, common instructions, output requirements and task-level resource policy. Keep rubrics, gold deliverables and previous assessments hidden from both generators.
4. Use a shared harness exposing equivalent search, file access, sandboxed computation and artifact creation, using the same installed libraries and attachment conversion policy. Do not compare OpenAI-hosted search/code execution against plain Claude chat as a clean model comparison; Databricks chat serving does not itself supply these tools. Preserve native image/audio/video content where supported; record every conversion and information loss.
5. Freeze task-level time/token/tool limits and provider-specific reasoning settings. The user approved no total dollar ceiling for generation, GPT low reasoning and Claude endpoint defaults. This is not a compute-matched comparison. Record metered usage and reconcile actual costs separately; do not silently give one model additional retries, tools or corrective feedback.
6. If comparable native modalities or tools are unavailable, label that stratum as a capability/tooling comparison or unsupported by the common harness. Do not present it as a clean base-model comparison. Never silently omit the difficult reference-file tasks.
7. Run all GPT tasks first, then all Claude tasks, as requested. Freeze one seeded task order and reuse it for both passes; cache shared reference inputs and record timestamps, returned model metadata and live search provenance. Sequential provider passes introduce a timing confound, especially for web research and mutable model aliases; disclose it rather than claim randomized provider execution.

### Run Policy

- Primary design: one fresh attempt per task per model, yielding **440 planned generation attempts**. This measures a paired single-attempt outcome, not reliability across repeated samples.
- Preflight all 220 tasks for reference-file presence, accessible formats, renderer support and rubric validity before paid execution. Missing local inputs block launch; unsupported modalities require an explicit policy decision.
- Pilot six diverse tasks covering no-reference research, document/PDF inputs, spreadsheets, presentations, images and a difficult modality where available. Pilot both generators and the grading pipeline. Choose using input/output requirements, not model outcomes.
- Freeze the protocol after pilot fixes. Rerun pilot tasks under the frozen protocol for the primary dataset; retain development runs separately and count their cost.
- Transport/rate-limit retries follow one bounded policy for both providers. They are not opportunities to improve an otherwise completed answer. A repair or revised answer is a separate, labeled experiment.
- Distinguish completed, incomplete, refused, provider-error, harness-error and not-run states. Invalid/missing requested deliverables after a completed attempt are observable failures, not infrastructure errors to retry until success.

## One Unattended Job

Build one resumable CLI workflow: **preflight -> generate -> collect artifacts -> inspect/render -> grade -> aggregate -> select slice -> export review bundle**.

This is one local job containing multiple provider requests, not one enormous request or an assumption that either provider's asynchronous Batch API supports every required tool. Normal SDK calls avoid per-task VS Code tool approvals. Human review happens in a consolidated report after execution, not through approval dialogs for each task.

### Sequential Execution Workflow

1. Run a no-inference preflight: validate all 220 task IDs, occupation coverage, prompts, rubric IDs/weights and reference paths/bytes; check dependencies, renderers, authentication and endpoint discovery. Record supported and unsupported modalities. Metadata access is not a fresh inference or modality-compatibility test.
2. After one explicit full-run configuration approval, launch one resumable CLI job. Attempt all 220 tasks with `gpt-6-astra` first, then all 220 with `databricks-claude-opus-5-5`, initially with concurrency one. Reuse identical prompts, reference bytes, libraries and task-level limits in separate workspaces and conversations.
3. Checkpoint each stage and preserve original responses, tools, artifacts, usage and errors immediately. Continue after task-scoped failures; do not regenerate completed poor answers. Apply one bounded transport/rate-limit retry policy, recording ambiguous timeout outcomes and possible duplicate charges.
4. Inspect/render saved artifacts after generation, then run both blinded judges against both providers' outputs. Keep grading independently resumable so changing a grade never incurs regeneration. Randomize judge assessment order with a fixed seed.
5. Export the full 220-by-two status matrix, separate judge scores and uncertainty, failure accounting, usage and consolidated review bundle. Human adjudication and final slice review remain separate from unattended execution.

No per-task chat approvals are required once the approved script is launched. Authentication/quota failures checkpoint and stop with an actionable message, not an interactive prompt. Refresh login outside the unattended job if necessary. Generation now has explicit approval for no total dollar ceiling and for best-effort local execution rather than isolation; task-level limits remain enforced. This is a disclosed protocol exception, not evidence that local execution is secure or that costs are bounded in dollars.

The full-set generation CLI is now implemented in [full_run.py](full_run.py). It reuses the tested adapters and tools, keeps one conversation active at a time, and does not invoke judges. Calibration, professional review and complete modality support remain limits on grading and claims, not hidden exclusions from generation. The original isolated-runtime requirement is explicitly waived for this authorized generation run only.

### Authorized Generation Launch

Prepared at 16:48 UTC on 2026-11-05: experiment UUID `c6d44b16-80ed-4955-bba6-a34c1a10110d`, stored in `gdpval-data/full_runs/2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d`. All 440 runs are `not_run`; no new inference was used to prepare them. The directory UUID is a storage location; the manifest's `experiment_id` is the authoritative foreign key.

Run from the repository root; the same command resumes the prepared experiment:

```powershell
uv run --no-project --python .venv\Scripts\python.exe python turing/field_engineer_take_home_project/full_run.py run --experiment gdpval-data/full_runs/2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d
```

For a read-only progress snapshot, use the same command with `status` instead of `run`. The experiment directory contains `status.json`, `coverage.csv`, the frozen `experiment.json` and UUID-linked per-run response/tool/artifact/request ledgers. A launcher lock rejects a second process for the same experiment. Startup verifies source, dataset, reference and dependency hashes and checks both providers' metadata without inference before any generation.

Frozen limits: 14 model turns, 24 executed tool calls, 10,000 output tokens per response, 50,000 generated tokens per conversation, a 1,800-second scheduling deadline and a 150-second Python-tool timeout. An in-flight API request can exceed the scheduling deadline. Both providers use automatic tools. Transport retries allow at most three requests per response slot, with 5/15-second backoff; ambiguous outcomes and possible additional charges remain in the request ledger. Authentication/quota/rate-limit exhaustion or three consecutive provider errors stop scheduling with exit code 2. Completed, incomplete and failed task attempts are retained, not automatically regenerated on resume. A crash can repeat a tool whose side effect occurred before its trace was saved; tool execution is not transactional.

All 220 tasks are included for both models. Audio/video/PSD/STEP/archive limitations are flagged using reference and expected deliverable format hints without exposing gold answers to generators. Native listening, video/CAD editing and complete archive-format support are not promised. Shared failures in these tasks cannot be presented as clean base-model weaknesses. Grading remains unrun and provisional until separately calibrated; no full-set score or final 30-task selection is produced by this generation command.

Validation: 21 offline tests passed, including 440-run coverage/order/resume, changed-prompt rejection, bounded retries, duplicate-launch locking and authentication stops. Input hashes were reverified while preparing the real manifest. Actual full-set unattended completion and native-modality support are not established by these checks.

### Preflight Results: 2026-11-05

Checked at **16:25 UTC**, using the repository's Python 3.12.10 environment. No inference, generation, paid judging, live search or model-generated code was run. Provider checks were read-only metadata requests; Office checks started and closed separate application instances without opening documents.

| Check                 | Result                                                                                                                                                                                                                      |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dataset coverage      | PASS: 220 unique task UUIDs, 44 occupations, five tasks each; 125 reference-bearing tasks and 95 without references.                                                                                                        |
| Prompts and rubrics   | PASS: nonempty prompts; 10,453 unique criterion UUIDs with finite numeric weights, nonempty criteria and positive task denominators. All 94 negative-weight criteria retained. No duplicate task or per-task criterion IDs. |
| Reference integrity   | PASS: all 261 entries are distinct, present, nonempty and resolve inside the reference directory; 1,656,670,179 bytes hashed. No missing/unsafe paths.                                                                      |
| Reference structure   | PASS at checked depth: 157 Office/ZIP container CRC checks, 74 PDF opens, 14 image validations and ten audio-header checks. No exceptions. This is not semantic validation or full rendering/decoding.                      |
| Python dependencies   | PASS: all 20 checked imports, including provider SDKs, document/media parsers and numerical libraries.                                                                                                                      |
| Office availability   | PASS: Word, Excel and PowerPoint 16.0 start through COM. Full-dataset document rendering remains untested.                                                                                                                  |
| Offline harness tests | PASS: all 16 adapter, local-tool, grading and report tests. Best-effort audit tests do not certify sandbox isolation.                                                                                                       |
| OpenAI metadata       | PASS: authenticated lookup of `gpt-6-astra`; no fresh inference or immutable snapshot verification.                                                                                                                         |
| Claude metadata       | PASS: OAuth profile `$DATABRICKS_CONFIG_PROFILE`; `databricks-claude-opus-5-5` is `READY`, `NOT_UPDATING`, task `llm/v1/chat`. No fresh invocation or modality verification.                                                      |
| Local capacity        | 455.57 GiB free at check time. `uv` and `databricks` available; `docker`, `podman` and `ffmpeg` absent from PATH. No isolated runtime verified.                                                                             |

Reference inventory: DOCX 67, XLSX 86, PDF 74, PPTX 1, ZIP 3, PNG 9, JPG 3, WEBP 2, WAV 8, MP3 2, MP4 2, PSD 1, STEP 2 and TXT 1. Counts are file entries, not disjoint task strata. MP4 affects one task, PSD one and STEP two; archive contents may introduce additional unsupported formats. TXT, MP4, PSD and STEP contents were not structurally validated. Audio headers are readable, but native listening is unavailable. One MP3 decoder emitted an ID3-comment metadata warning without failing the header check; full decoding remains unverified.

Snapshot fingerprints:

- Dataset Parquet SHA-256: `f8422fab9b21d90c0ee5f0659842ab666d418cb8940842918f9f4b0df7ae0202`.
- Reference manifest SHA-256: `0bc42b02a40607ecd8255c5d485e3684fd3abd771ef3f45be2462baa3d0d0157`, computed over sorted compact JSON mapping each dataset-relative reference path to its byte count and SHA-256.
- Key installed versions: OpenAI 3.42.1, Databricks SDK 0.157.0, PyArrow 26.0.1, python-docx 1.2.0, openpyxl 3.1.5, python-pptx 1.0.2, PyMuPDF 2.0, soundfile 0.14.0 and pywin32 312. Capture the complete dependency manifest again when freezing the full-run configuration.

**Historical decision at 16:25 UTC: inputs and metadata passed; launch was blocked.** The authorized generation launch above supersedes its orchestration, execution, modality and budget gates through tested implementation and explicit user-approved exceptions. This preflight still does not validate artifact creation across all formats, current tool round trips, provider rate capacity, exact pricing or professional grading accuracy.

Implementation requirements:

- Provider adapters share the same task contract. Isolation remains the preferred design; the authorized generation run instead uses explicitly approved credential-stripped local subprocesses with best-effort restrictions. Treat reference files and generated artifacts as untrusted inputs and do not call this a hardened sandbox.
- Generator and grader contexts are separate. A rubric or expert answer must never leak through a reused conversation, sandbox or cached attachment.
- Persist each task/model state before and after a stage. Resume completed generation without paying to regenerate it; resume grading independently. Use bounded concurrency and exponential backoff; one failure must not discard the rest of the batch.
- Persist complete raw responses, tool traces, inputs/hashes, deliverable hashes, timing, API usage and errors. Keep keys out of files and logs.
- Every experiment, task run, judge assessment and failure annotation gets an opaque UUID. Carry the dataset task UUID and rubric item UUIDs as real references. Names and row numbers are display-only; never recover relationships through prompt or filename matching.
- Store the dataset snapshot/checksum, frozen configuration and source-code revision or hash with the experiment. Save immutable original artifacts; derived text, screenshots and PDFs are separate evidence.
- Code and methodology belong in this project directory, outside the ignored dataset directory. Keep downloaded data and bulky raw artifacts ignored; export a compact, shareable evidence bundle with relative links and no credentials.
- Publish an all-220 status matrix and separate generation/grading coverage counts, including failed and unassessed attempts. Do not compute a seemingly complete score from only successfully graded tasks.

The generation CLI can resume the prepared experiment without per-task agent intervention and export complete generation coverage. The eventual inspect/grade/select/review pipeline is separate work; generation readiness does not mean the complete research deliverable is finished.

## Automated Grading and Validation

### Evidence Before Scores

Inspect the requested output itself, not just the model's answer text. Check file existence/type, required sections and machine-checkable quantities; render documents and presentations for layout checks; inspect workbook formulas and values where applicable. Test executable artifacts only in the sandbox. Page counts must come from an actual rendered file, not stale document properties.

For research-heavy tasks, preserve source URLs and verification evidence. A public abstract is not proof of free full text; HTTP 403 is not proof of a paywall. Unsupported rendering, inaccessible evidence and subjective rubric ambiguity must remain explicit uncertainties.

### Judge Design

- Use the dataset's task-specific rubrics. Preserve the original criterion IDs and weights, including penalties. Freeze binary versus partial-credit rules before the primary run; do not silently adjust the rubric after seeing which model benefits.
- Use one OpenAI judge and one Anthropic judge, each assessing every model output independently in isolated requests. This gives **880 planned judge assessments**, before pilots, retries and calibration checks. A same-provider judge is not independent validation by itself.
- Hide generator labels and randomize assessment order. Remove provider-identifying wrapper metadata where possible without changing the deliverable. Document that writing style may still reveal identity.
- Give judges the task, references, rubric and original/derived artifact evidence, within their supported modalities. Instruct them to treat artifact text as untrusted evidence, never as grading instructions.
- Require structured output: criterion UUID, pass/fail/unverified, evidence location, rationale and confidence. Validate schema, criterion coverage and allowed scores in code. Compute totals locally, not from a judge's arithmetic.
- Judges may use equivalent research tools for source checks, with bounded budgets and recorded provenance. Lack of access does not justify invented verification.
- Preserve each judge's raw decisions. Resolve disagreements through evidence-based human adjudication for the presentation slice. Outside that slice, leave disagreements unresolved and report bounds and per-judge sensitivity rather than manufacture consensus.
- OpenAI's experimental GDPval grader is optional corroboration only after verifying its access, interface, costs and artifact handling. Do not assume it has an unattended API or that a local model judge reproduces it.

### Human Calibration

Before scaling, manually audit all pilot outputs, rendered files and a sample of criterion decisions. Fix systemic grading errors, then freeze and version the judge instructions. After the run, inspect both outputs for all 30 selected tasks, all material disagreements in that slice, and a seeded sample of at least five task pairs outside it as a selection-bias check. The researcher-facing claim must distinguish my review from professional domain-expert adjudication.

Report audited criterion agreement, false passes/false fails against the human review, and whether judge provider changes the apparent winner. Keep the unadjudicated cases visible. If the judge cannot reliably distinguish factual quality from presentation quality, do not use a single aggregate score as the pitch's headline.

## Selecting the Most Informative Slice

**Do not pick the final occupations now.** Their relative value must come from our own paired results, not provider reputations or published leaderboards. Freeze the following selection rule before the full run, and disclose that selection is exploratory and outcome-dependent.

1. For each task, calculate each model's weighted rubric score as earned points, including applied penalties, divided by available positive points. Retain uncertainty bounds; do not silently clamp negative scores to zero. Also report critical failures, usable-deliverable status, cost and latency separately.
2. Calculate the paired difference, OpenAI minus Anthropic, on the same task. Agreement-backed differences and objective checks are stronger selection evidence than a single judge's preference. Do not treat unresolved differences as established wins.
3. Rank occupations by the mean absolute, agreement-backed task-level score difference. Unresolved pairs contribute zero to this ranking, not a guessed midpoint. Eligibility requires at least four of five task pairs with inspectable artifacts and usable grading evidence. Publish exclusions and the full occupation ranking. Break ties by evidence coverage, then occupation name.
4. Select the top six eligible occupations and retain **all five tasks in each**, for a 30-task slice. This avoids selecting only the flattering tasks inside an occupation. If fewer than six qualify, disclose the smaller slice and its coverage rather than relax criteria silently.
5. Manually audit the selected 30 task pairs. Correct grading errors in a versioned assessment; retain the originally selected slice, show corrected ranking sensitivity and do not silently replace inconvenient examples. If the apparent separation disappears, report that as the finding.
6. Choose four to six presentation examples from the audited slice: clear OpenAI advantages, clear Anthropic advantages, and ties/shared failures where they actually exist. Do not force a balanced story or invent differences. Include a counterexample to the headline pattern when available.

Report full-dataset results beside selected-slice results. A slice selected for large observed differences will exaggerate separation by construction; it is an explanatory case study, not an unbiased estimate of overall model superiority. Five tasks do not support sweeping occupation-level conclusions.

Repeat generation on up to six key examples for both models if budget permits, as a labeled stability check. Repeats of selected tasks are not an independent holdout. A confirmatory claim would need fresh, unseen tasks and a prospectively frozen protocol. Any paired bootstrap interval from the primary run is descriptive, should account for occupation clustering, and does not remove selection bias or capture all generation/judge variability.

## Failure Taxonomy and Data Opportunities

Use multiple labels per failure, one primary mechanism, severity and an evidence pointer. Distinguish observation from causal hypothesis. Do not manufacture thirty failures if fewer are observed.

| Failure class                      | What to inspect                                                              | Potential dataset contribution                                                          |
| ---------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Reference grounding                | Claims, calculations or decisions contradict supplied files                  | Source-linked tasks, provenance annotations and contradictory-reference examples        |
| Research and citation integrity    | Wrong author/date, unverifiable source, unsupported factual claim            | Claim-to-source supervision, citation verification and access-status labels             |
| Quantitative reasoning             | Formula errors, wrong units, inconsistent totals, unsupported assumptions    | Auditable workbooks, intermediate calculations and executable checks                    |
| Constraint and artifact compliance | Wrong format, missing sections, page/slide limits, broken deliverable        | Rendered gold artifacts, machine-checkable constraints and repair pairs                 |
| Domain judgment and risk           | Professionally consequential omission, unsafe recommendation, poor trade-off | Expert rationales, risk severity and acceptable alternatives                            |
| Completeness and actionability     | Generic prose instead of the requested decision or usable output             | Task decomposition, complete artifacts and expert acceptance criteria                   |
| Tool or modality limitations       | Reference cannot be parsed; artifact cannot be created or inspected          | Matched tool-access tests; better data may help but cannot replace missing capabilities |
| Grader/harness defects             | Stale page metadata, inaccessible evidence, false pass, dropped input        | Evaluation fixtures and calibrated grading evidence, not a claim of model weakness      |

For every proposed data investment, show the observed failure count and denominator, affected tasks/models, representative evidence, why training/evaluation data could help, and an alternative explanation. Propose a small follow-up experiment. Do not claim GDPval establishes that buying or training on such data will improve performance; that requires separate validation and appropriate rights.

## Researcher-Facing Deliverable and Pitch

Prefer a one-page document over building a website until the evidence is ready. It must be understandable in two minutes:

- Exact tested models and shared-tool policy; full-run and selected-slice coverage; actual spend.
- One paired results chart with full-dataset context, selected occupations and uncertainty.
- Three evidence-backed failure patterns, their severity and contrasting artifact excerpts.
- A concrete dataset proposal: task distribution, reference formats, gold artifacts, expert annotations, negative examples and measurable acceptance tests.
- Limits: selected sample, judge reliability, single attempts, tooling effects and non-expert human review.

Prepare two audience-specific versions of the same truthful story. For OpenAI, lead with gaps directly observed in its tested model and the corresponding data/acceptance tests. For Anthropic, lead with gaps observed in its tested model. Show the other model's successful artifacts as concrete counterexamples when justified, not as evidence of a provider-wide trait. Do not invent either company's internal priorities.

Proposed 15-minute call structure: 2 minutes on methods/coverage, 4 minutes pitching to OpenAI, 4 minutes pitching to Anthropic, and 5 minutes for questions, adjusted to the interviewers' format. Be ready to defend sample selection, costs, judge disagreement, critical errors and why the proposed data addresses a real rather than tooling-induced gap.

## Budget and Execution Gates

Pilot authorization update: the user confirmed corporate Databricks workload approval, explicitly requested no hard dollar ceiling for this six-task pilot, and chose local execution. The development pilot therefore uses credential-stripped local Python subprocesses with best-effort filesystem/network/process audit restrictions, not a hardened sandbox. This is an explicit deviation from the isolated-execution and dollar-cap design, not approval of the full 220-task run. The same two selected models serve as separate blinded provisional judges. See [the pilot protocol](PILOT.md) for frozen selection, limits and modality caveats. Full-run gates below remain in force.

Full-generation authorization supersedes the pilot-only scope: on 2026-11-05 the user requested unblocking launch without a budget constraint, then explicitly approved local execution with its security limitations, attempting all capability-limited tasks, and the tested GPT-low/Claude-default settings for generation first. No dollar ceiling is imposed. Paid grading, adjudication and final claims remain separate; this is not approval to silently add models, change configurations or rerun poor task outcomes.

The base plan involves **440 generation attempts + 880 judge assessments = 1,320 logical model requests**, excluding tool subcalls, pilots, retries and stability checks. Do not estimate dollars from request count alone.

After the pilot, forecast by input/output format and reference size using current prices for the exact models. Include input, cached input where applicable, output/reasoning, search, sandbox/container, media processing and rendering charges. Track generation and grading separately. The earlier pilot's 5,285 tokens are not a representative full-run cost estimate.

Launch decisions and remaining grading gates:

- Confirm the proposed generator pair through inference smoke tests; choose and verify exact judge IDs separately.
- Confirm authorization to use the corporate Databricks workspace for this workload.
- Generation budget decision complete: explicitly uncapped. Continue metered usage and unknown-charge accounting; do not invent reconciled USD totals. A paid grading stage needs its own approved configuration.
- Choose per-task time/token/tool caps, provider concurrency and a conservative spend-estimation policy.
- Approve the modality/tooling policy and preflight coverage report.

If a later stage adopts a dollar cap, stop scheduling when remaining budget cannot cover reserved in-flight and proposed work. Current generation is explicitly uncapped; provider quota/authentication failures still stop scheduling. Persist state and report partial coverage. Actual invoices may lag; distinguish metered usage estimates from reconciled charges.

## Milestones Within the One-Week Deadline

| Stage                              | Output / exit condition                                                                                                  |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Day 1: freeze design and inventory | Model access, task manifest, artifact coverage, privacy/security policy, provisional budget                              |
| Days 1-2: build and pilot          | Common provider harness, sandbox, renderers, structured grading, six-task paired pilot; budget and protocol approved     |
| Days 2-3: full unattended run      | All 220 tasks attempted per model, or every blocked task explicitly accounted for; resumable raw artifacts and costs     |
| Days 3-4: grade and select         | Automated judgments, all-220 coverage/results, frozen-rule occupation ranking and selected 30-task review bundle         |
| Days 4-5: audit and classify       | Inspect 60 selected outputs, outside-slice spot checks, adjudications, failure ledger and stability checks if affordable |
| Days 6-7: communicate and rehearse | One-pager, evidence appendix, reproducible code/configuration, cost statement and two specific pitches                   |

This is larger than the brief's two-to-four-hour focused-work suggestion. Run time can be unattended, but artifact inspection and sound adjudication still require substantial human time. Time-box infrastructure work and favor a truthful partial result over an elaborate but unvalidated pipeline.

## Submission Checklist

- [ ] Frozen experiment configuration and task/reference manifest.
- [ ] Shareable runner, dependencies, tests, setup instructions and documented resume command.
- [ ] Complete 220-by-two status matrix with no silent exclusions.
- [ ] Artifact hashes, original responses, judge decisions and reproducible score aggregation.
- [ ] Full results, 30-task exploratory slice, selection rule and ranking sensitivity.
- [ ] Human-reviewed failure ledger with stable IDs, severity, evidence and adjudication notes.
- [ ] Judge-validation summary, limitations and separate infrastructure-failure accounting.
- [ ] Actual or clearly labeled estimated spend, including pilots, grading and retries.
- [ ] One-page researcher-facing findings and targeted data proposal; two pitch outlines.
- [ ] Submission bundle/link ready for Sam Vangelos; nothing sent without explicit approval.

## Immediate Next Step

Execute the post-run analysis plan below, starting with an offline results freeze and coverage reconciliation. Preserve the frozen primary, retry and grading environments. No new generation, paid judging, executable-artifact testing or expanded rendering is authorized by this analysis plan. Historical launch notes below are checkpoints, not current queue status.

## Post-Run Analysis Plan: November 17

### Questions and Current Evidence

Answer three different questions without collapsing them into a single leaderboard:

1. **Delivery:** did the tested configuration finish and produce the requested, usable deliverables within its limits?
2. **Quality:** when evidence is inspectable, how well does the actual output satisfy the original professional-task rubric?
3. **Opportunity:** which verified failures suggest a concrete data investment, rather than a missing tool, serving problem or grading defect?

The saved [full findings](../../gdpval-data/full_grades/primary-v1/reports/FINDINGS.md), [paired outcomes](../../gdpval-data/full_grades/primary-v1/reports/pairs.csv) and [quality bounds](../../gdpval-data/full_grades/primary-v1/reports/quality.csv) establish this starting point:

| Observation | Current result | Analysis consequence |
| --- | --- | --- |
| Completed with at least one artifact | GPT 211/220 (95.9%); Claude 144/220 (65.5%) | A 30.5-percentage-point delivery-proxy gap, not proof of correct or complete deliverables. |
| Valid automated assessments | 857/880; 13 invalid/failed; 10 infrastructure-unavailable | Account for every assignment; do not score unassessed work as zero. |
| OpenAI judge task outcomes | GPT wins 38, Claude wins 31, ties 8, unresolved 143 | Keep all 220 tasks in the denominator. |
| Claude judge task outcomes | GPT wins 26, Claude wins 50, ties 10, unresolved 134 | The apparent direction changes with judge; no overall quality-winner headline. |
| Cross-judge outcomes | Both favor GPT on 17 tasks, both favor Claude on 29, both tie on five; eight opposite-direction decisions; 121 unresolved under both | These are audit priorities and provisional agreement, not human-validated truth. The remaining 40 pairs have other mixed outcomes. |
| Higher-budget Claude retries | 54/62 completed, four incomplete, four provider errors | A separate selected-cohort sensitivity result; artifact validity and quality still require verification. |

These are saved results, not a fresh inference run. The model comparison is GPT-6 Astra at low reasoning versus Databricks-hosted Claude Opus 5.5 at endpoint defaults, not ChatGPT versus the Claude consumer product. Preserve the sequential-provider timing, unequal reasoning allocation and modality caveats.

### 1. Freeze and Reconcile the Analysis Inputs

Work offline first. Snapshot report hashes and record the primary experiment, grading workspace, retry experiment, policy hash and export timestamp in the analysis provenance. Join using task, run, assessment and criterion UUIDs, never names or filenames.

- Reconcile 220 tasks, 440 original runs, 880 assignments and 62 parent-linked retries against manifests and exported rows. Verify that each task has both generators and each original run has both judge assignments.
- Inspect the reasons and remaining original budgets for the nine invalid and four failed assessments. Classify them as schema/coverage, exhausted budget, transport or other observed failure; preserve their original records. Do not automatically retry them. If recovery is needed, propose it separately and retain the current export as the baseline.
- Retain the 10 unavailable assignments from five primary infrastructure failures. Distinguish missing source evidence, missing requested outputs and parser-limited evidence.
- Mark the existing pilot one-pager, provisional failure report and calibration report as historical when citing them. Do not overwrite them with full-run claims or edit frozen machine-generated reports by hand.

**Exit:** a reconciled coverage table and exception list with no unexplained omissions. Analysis can proceed with explicit uncertainty; perfect grading completion is not required.

### 2. Build the Full-Set Comparison Before Selecting Examples

Produce three linked views, with the original 220-task denominator visible:

- **Operational funnel:** attempted -> conversation completed -> any artifact -> requested deliverables present -> inspected usability. Separate incomplete, filtered/empty, provider-error and harness-error outcomes. File presence alone only supports the first artifact proxy, not the later usability stages.
- **Rubric quality:** task-weighted lower/upper evidence bounds for each generator under each judge, retaining negative penalties. Show all-primary bounds, the existing generator-specific completed-with-artifact subsets, and a common matched subset where both generators completed with artifacts. The generator-specific subsets contain different tasks and are not a clean paired comparison.
- **Paired outcomes:** per-judge win/loss/tie/unresolved counts, paired difference bounds and the cross-judge outcome matrix. Overlapping bounds remain unresolved, not ties; uncertainty ranges are not confidence intervals. Never average the two judges into an invented consensus.

Break these views down by reference-bearing versus no-reference tasks, capability-limit flags, input/output format and occupation. Format groups can overlap; state each denominator. Treat five-task occupation summaries as descriptive inspection aids. Report uncertainty coverage by generator, judge, format and criterion weight so missing evidence cannot masquerade as quality.

Use paired task-level differences, not subtraction of means from unmatched subsets. Any bootstrap is optional and descriptive, clustered by occupation; do not spend time on significance claims before evidence quality is established.

**Exit:** a coverage/funnel chart, per-judge quality-bounds chart and paired-outcome table traceable to saved assessment IDs.

### 3. Audit the Judges and Select the Review Slice

First triage the eight opposite-direction task pairs, high-weight pass/fail disagreements, wide evidence bounds and parser failures. Measure whether judge leniency changes by generator, but do not label it causal self-provider bias: the same pattern can arise from evidence interpretation or calibration.

Then apply the existing six-occupation selection rule above without choosing occupations to fit a story:

- Require at least four of five task pairs per occupation with inspectable artifacts and usable grades from both judges for both generators. Exclude unsupported evidence from clean quality claims and publish eligibility reasons.
- Before computing the ranking, make the agreement-backed difference operational: use the smaller absolute separating margin across the two judges when both favor the same generator; use zero for ties, unresolved or conflicting directions. Average over all five occupation tasks, with nonqualifying pairs contributing zero. This conservative implementation uses interval separation, not uncertain score midpoints.
- Publish all 44 occupation rankings and exclusions. Select the top six eligible occupations, keep all five tasks in each and use the previously specified coverage/name tie-breaks. If fewer qualify, retain the smaller slice rather than relaxing the gate.
- Freeze the selected IDs before correcting their grades. Retain the initial selection after audit; show corrected ranking sensitivity and how midpoint-based ranking would differ, without swapping inconvenient examples.

Review both original outputs for every selected task: 60 candidate outputs for a full slice. Add at least five seeded task pairs outside the slice, sampled independently of observed score gaps, and label the disagreement-triage sample separately.

For each reviewed pair, check requested files/constraints, reference grounding, quantitative results, sources and professionally consequential omissions. Audit all material criterion disagreements and high-severity decisions in the slice, plus a recorded sample of apparently agreed passes and fails. If a necessary view, recalculation, listening check or source verification is unavailable under the current policy, retain uncertainty and request a separately approved inspection path; do not execute untrusted code or silently expand tooling.

Record reviewer decisions before consulting judge rationales where practical. Preserve automated judgments and save corrections as versioned human annotations with evidence pointers. Report audited pass/fail agreement and false-pass/false-fail counts with explicit audited denominators; separate unverified decisions. This is a targeted, non-expert audit, not a full-dataset or professional error-rate estimate.

**Exit:** a frozen selection manifest, reviewed evidence bundle and judge-validation summary. If agreement-backed quality differences disappear, report that rather than forcing a comparative claim.

### 4. Turn Verified Failures into a Researcher-Useful Taxonomy

Use the failure classes above and record each finding with an annotation UUID, task/run/criterion IDs, observed defect, severity, evidence location, primary mechanism, secondary labels, reviewer and uncertainty.

- Separate delivery/resource failures from substantive errors in delivered work, and separate both from infrastructure, missing tools and grader defects.
- Deduplicate repeated symptoms of one underlying defect. Count affected tasks/candidates as well as criterion decisions, with the inspected denominator for each.
- Prioritize consequential errors over cosmetic differences. Retain shared failures, counterexamples and successful outputs that clarify an acceptance standard.
- Target roughly 30 well-supported failure instances if available; do not invent a quota or claim causality from tool traces alone.

For each of the strongest three patterns, specify the observed count/denominator, contrasting artifact evidence, alternative explanation, and the smallest useful dataset package: task distribution, references, gold deliverables, expert rationales, negative/repair examples and machine-checkable acceptance tests. Explain why data could help and what tooling change would still be needed. Propose a held-out follow-up test; do not claim these results demonstrate training improvement or confer training rights.

**Exit:** a human-reviewed failure ledger and three evidence-backed data-opportunity briefs.

### 5. Analyze Claude Retries as a Separate Sensitivity Study

Join the 62 retries to their original incomplete attempts. Verify requested-artifact presence, then report completed/incomplete/provider-error transitions, time and metered usage. Treat 54/62 (87.1%) as conversation completion only until delivery checks are done.

Inspect whether recovered outputs actually address the original missing work. Quality comparisons require their own labeled assessment protocol and approval if paid judging or expanded inspection is needed; current primary grades do not grade retry artifacts.

Do not substitute retries into the 220-task primary, compare retry Claude scores against primary GPT as an equal-budget experiment, or generalize recovery to all Claude failures. The cohort excludes 14 originally completed-but-artifact-missing attempts. Multiple limits and fresh sampling changed together, so recovery does not identify a single causal budget parameter.

**Exit:** a separately labeled retry transition/resource table, with quality explicitly unknown where unassessed.

### 6. Reconcile Cost and Package the Story

Account for primary generation, primary grading, retries, development pilots, smoke tests and failed/ambiguous requests separately. Deduplicate request ledgers by recorded IDs; distinguish metered tokens, available price-based estimates and reconciled billed charges. Include web/tool charges if available, retain unknowns and do not infer USD from request counts or incomplete usage records.

Deliver:

1. **Full-set appendix:** protocol/provenance, coverage, both judges, uncertainty, modality limits, selection ranking and cost accounting.
2. **Reviewed case bundle:** selected IDs, original/derived artifact links, versioned review annotations and failure ledger.
3. **One-page findings document:** exact configurations, one full-set comparison visual, three verified failure patterns, a concrete dataset proposal and short limitations. Replace the pilot-facing headline only after the audit supports it.
4. **Two pitch outlines:** lead with the tested GPT configuration's verified gaps for OpenAI and the tested Claude configuration's verified gaps for Anthropic; use the other output as a counterexample only when inspected. Keep the underlying evidence identical.

Choose four to six presentation cases from the audited slice, including directional advantages and shared failures where they actually exist. Rehearse a 15-minute methods/two-audience pitch and prepare answers on grading validity, selection bias, budget sensitivity and why the proposed data addresses the observed problem.

**Completion gate:** every headline number has a denominator and reproducible source; every showcased failure has inspected evidence; primary/retry/pilot results are distinct; uncertainty and unknown costs remain visible. No new model run, website build or outbound submission is needed to complete this analysis.

### Execution Order

Start with input reconciliation and the full-set tables. Next triage grading uncertainty, freeze the slice and devote most of the analysis effort to artifact review. Build the taxonomy and data proposals from that review, then finish the one-pager and pitches. Retry/resource accounting can proceed independently once inputs are reconciled.

If review time is limited, reduce the number of completed case studies and disclose the unreviewed remainder. Do not label all 30 tasks audited merely because automated grading exists. The original one-week schedule above is historical, not evidence that these remaining steps are complete.

### Full-Grading Authorization and Launch

After all 24 calibration assessments completed and reports were exported, the user requested grading and recording the remaining 846 assessments and explicitly approved full grading with no dollar ceiling, unchanged judges and existing local-parser limits. The user was told about 254/964 unverified criterion decisions (26.3%) and unresolved comparisons. Approval permits provisional automated grading, not expert validation or audited false-pass/false-fail rates.

[Full approval](../../gdpval-data/full-grading-approval.json) binds grading UUID `51cfbb2b-90ca-42e6-8c61-1c28346844ee`, the unchanged policy hash and calibration-results SHA-256 `428c3ee4fd404088e34b070d217af4945bc2673940e0281ebe6a61b9752cfd20`. [run_full_grading.ps1](run_full_grading.ps1) schedules sequential batches of at most 24 through the frozen grader. Its offline validation passed with 846 pending, 24 completed and 10 unavailable; provider credential acquisition also passed. The launcher is running, initially preparing contexts offline. Each judgment/request is checkpointed; the launcher stops on authentication, blocked/new failed assessments or lack of progress, rather than silently granting new budgets. Consolidated reports are exported after the queue ends. Launch does not establish completion.

The grading workspace records `grading.json`, `judgments/<assessment UUID>/assessment.json`, `full-progress.json` and `full-grading.log`. Primary and retry generation remain separate and unchanged. Historical launch/recovery notes below describe their respective checkpoints, not current full-stage approval status.

### November 9 Inspection and Calibration Launch

The user explicitly approved paid six-task calibration with GPT-6 Astra low reasoning and Claude Opus 5.5 endpoint defaults, no dollar ceiling and the documented local-parser limits, then a pause for human review. This is not authorization for the remaining full-scope assessments. The user also requested resuming the existing higher-budget Claude retry experiment, not creating another cohort or repeating its finished attempts.

The independent grading workspace is `gdpval-data/full_grades/primary-v1`, grading UUID `51cfbb2b-90ca-42e6-8c61-1c28346844ee`. Preparation completed with all 440 primary candidates and 880 judge assignments. The frozen policy SHA-256 is `c47ea4141aecd94e332adcf58ebc36ccdb1ed80af1d023bd87c538624849e19f`. The separate `gdpval-data/calibration-approval.json` binds approval to that UUID/hash and only the calibration scope; its human calibration-review approval remains false.

Full-primary offline inspection completed with 440 evidence candidate records. The terminal executed only the first command of the original multiline launch, so the paid calibration command was subsequently launched directly for at most 24 assessments across the seeded six task pairs. Check `inspection.log` and `calibration.log` inside the grading workspace. Calibration launch alone does not establish successful paid judgments. Aggregation/report export requires a separate command after calibration; it is not automatically queued. After calibration, review criterion evidence, disagreements and unavailable modalities before authorizing any full-scope grading. Original primary and retry outputs remain separate and unchanged by grading.

The resumed Claude retry queue started from eight completed, one incomplete, one provider-error and 52 not-run attempts. A live pending attempt was observed making model/tool calls. Terminal-managed workers are used; prior log files are historical and may not receive output from the resumed worker. Run/request checkpoints and `progress.json` remain authoritative. Finished retries are skipped, not regenerated.

Launch validation: all 15 focused offline grading tests passed after adding bounded Windows permission-error retries to the grading-only checkpoint writer and moving temporary fixtures under ignored data. The generator checkpoint implementation and frozen generation sources were not edited. Grading policy/approval bindings and editor diagnostics passed. Completed full-set inspection, successful paid judgments, professional quality and reconciled USD charges remain unverified at launch.

### November 9 Recovery Checkpoint

Inspection completed all 440 candidates. The first calibration launch processed 24 assignments but yielded only five completed grades, 13 blocked assignments and six failures; processing is not calibration success. The blocked contexts recorded permission errors and were subsequently recovered through the existing offline `prepare_judge` routine without inference or frozen-source changes.

Claude retries halted at 20:26 UTC after three consecutive provider errors: 26 completed, one incomplete, four provider errors and 31 not run. A no-inference SDK authentication check confirmed an invalid Databricks OAuth refresh token despite successful CLI metadata listing. Browser login then succeeded, SDK token acquisition was reverified without displaying credentials, and the existing retry queue was relaunched for pending attempts only. Finished and failed generation attempts were not reset.

Offline aggregation of partial calibration outcomes was launched separately and still held the grading workspace lock at the recovery check. Resume unfinished calibration with the original approval and `--retry-failed` only after aggregation releases that lock; this preserves original per-slot/turn/token limits and completed grades. Full-scope grading remains blocked on successful calibration and explicit human review. Neither report export completion nor resumed paid calibration is established by this checkpoint.

### Independent Full-Set Evidence, Grading and Reporting

`full_grade.py` never invokes generation or writes into primary/retry directories. It creates a new grading workspace outside both. `prepare` copies original manifest bytes, dataset, frozen generator source, UTF-8 prompt/rubric bytes, references and candidate artifacts; a complete primary-file byte-count/SHA-256 inventory also binds the preserved responses, requests and other primary files. Every later stage verifies primary and copied-input integrity. Source corruption is not repaired or regenerated. All 440 original attempts receive both judge assignments (880), including infrastructure errors and missing outputs. Pilots and retries are never merged.

Run from the root of the evals checkout (no dependency synchronization, endpoint requests or inference in the offline stages):

```powershell
uv run --no-sync python turing\field_engineer_take_home_project\full_grade.py policy --policy gdpval-data\grading-policy.json
uv run --no-sync python turing\field_engineer_take_home_project\full_grade.py prepare --source gdpval-data\full_runs\2cfa5e88-1fd6-47bd-94bc-9c3bef333a2d --workspace gdpval-data\full_grades\primary-v1 --policy gdpval-data\grading-policy.json
uv run --no-sync python turing\field_engineer_take_home_project\full_grade.py inspect --workspace gdpval-data\full_grades\primary-v1
uv run --no-sync python turing\field_engineer_take_home_project\full_grade.py status --workspace gdpval-data\full_grades\primary-v1
uv run --no-sync python turing\field_engineer_take_home_project\full_grade.py aggregate --workspace gdpval-data\full_grades\primary-v1
```

`prepare` requires a new workspace; `inspect`, `grade` and `aggregate` resume independently. `inspect --limit 12` bounds new candidate evidence records per launch. Inspection subprocesses have bounded timeouts and checkpoint parser errors as unavailable evidence, not false criteria. Reuses existing file inspectors and image/PDF view rendering, **never Office COM**. Unsupported Office layout/recalculation, native listening, video/CAD/PSD and live citation verification remain unverified. No executable artifacts or model-generated code are run. Local parsers are not a hardened sandbox; additional rendering/access requires a separately approved, revised grading protocol.

Defaults are deliberately unpaid: `budget.uncapped_approved=false`, empty authorization, no model calls. For eventual paid use, approve the separate grading budget and exact model IDs/instructions **before prepare**, then set the policy's `budget` authorization and approval boolean. Do not edit the workspace's frozen policy after preparation; prepare another grading workspace for a policy revision, leaving generation unchanged. Grading uses its own loop, not the pilot's hardcoded ten-turn `grade=True` branch: defaults are 16 turns, 32 tool calls, 12,000 output tokens per response, 60,000 generated tokens, 1,800-second scheduling budget, 240-second request timeout, at most two transport retries, sequential execution and at most 24 assessments per launch. These are independent judge budgets, not generator-budget changes; in-flight requests/OAuth work can exceed the scheduling deadline. Raw requests, ambiguous outcomes/charges, responses, read-only tool traces and conversations are checkpointed separately. Failed assessments are not retried automatically; `--retry-failed` resumes only within the original slot/turn/token limits, never regenerates an answer or grants new grading budgets.

Preparation also emits `approval-template.json` and a seeded six-task calibration sample (complete pairs, both judges). Copy the template to an approval file outside the frozen inputs and explicitly set `approved`, `corporate_workload_approved`, `local_parser_limits_approved`, reviewer and authorization. Approval is bound to `grading_id`, policy hash and stage scope. These commands are **examples for a later explicitly approved paid stage, not authorization or execution now**:

```powershell
uv run --no-sync python turing\field_engineer_take_home_project\full_grade.py grade --workspace gdpval-data\full_grades\primary-v1 --scope calibration --allow-paid --approval gdpval-data\calibration-approval.json
uv run --no-sync python turing\field_engineer_take_home_project\full_grade.py aggregate --workspace gdpval-data\full_grades\primary-v1
uv run --no-sync python turing\field_engineer_take_home_project\full_grade.py grade --workspace gdpval-data\full_grades\primary-v1 --scope full --allow-paid --approval gdpval-data\full-grading-approval.json --limit 24
```

Before the full-scope command, all calibration assignments must be valid completed or explicitly unavailable, with at least one fully graded task pair. Audit sample criteria and prior pilot disagreements; document unresolved limits/resolutions. The full approval must have `scope="full"` and `calibration_review.approved=true`, nonempty review notes, and `calibration_review.results_sha256` equal to the SHA-256 of the exported `calibration-results.json`. This is an explicit human gate, not automatic calibration success. Both contexts contain only original prompt/rubric/reference/candidate bytes and fresh inspection evidence; no generator final answer, wrapper identity, generation trace or other judgment is supplied. Original content/style/filenames may still incidentally reveal identity.

Accounting policy: provider/harness failures are `unavailable` without inference, **not semantic zero**; missing listed source files are source-loss unavailable. Completed/incomplete outputs lacking deliverables remain eligible for rubric-specific absence assessment: judges must justify each failure against that criterion, retaining uncertainty elsewhere and all negative penalties. Every assignment remains `not_run`, `completed`, `invalid_grade`, `failed`, `blocked` or `unavailable`; no silent omissions. Aggregate unassessed bounds span the original rubric's logical minimum/maximum, not invented artifact scores.

`aggregate`/`report` make `reports\results.json`, assessment/criterion/pair/quality/disagreement CSVs and `FINDINGS.md`, with no inference. Every original task is paired separately by judge; task-weighted original-rubric percentages retain negative scores, lower/upper uncertainty, unresolved overlap and disagreements without a fictitious consensus. All-primary quality bounds and operational status denominators are separate from the completed-with-artifact conditional quality subset. Each occupation has only five tasks; results do not establish provider/occupation-wide quality. USD remains unreconciled, final slice selection and professional adjudication remain unimplemented approval/review work.

Focused offline validation:

```powershell
uv run --no-sync python -m unittest discover -s turing\field_engineer_take_home_project -p test_full_grade.py -v
```

## Higher-Budget Claude Retry Experiment

The user requested inspection and regeneration of the 62 incomplete Claude tasks, then explicitly requested higher limits and retries. The original experiment `c6d44b16-80ed-4955-bba6-a34c1a10110d` remains immutable; retry results must not replace its single-attempt outcomes or be presented as an equal-budget primary comparison.

Checkpoint diagnosis, with overlapping counts: 52/62 ended with `finish_reason: length`, 38 reached the 50,000-generated-token conversation cap, 15 reached 14 model turns, and five reached 24 executed tool calls. Eleven stopped on response truncation without reaching the other limits; none reached the 1,800-second scheduling deadline. Only nine had saved artifacts. Fifty-six terminal responses contained a reasoning block without visible text in content; some still had tool calls. Returned usage did not provide a reasoning-token breakdown, so reasoning's exact contribution cannot be quantified. The original loop immediately terminates on a truncated response without tool calls, even with conversation budget remaining; retries retain that termination rule rather than treating incomplete reasoning as a completed answer.

The independent [retry runner](retry_claude.py) uses fresh conversations and workspaces, with no prior answers, tool traces, rubric or expert deliverables exposed to the model. Each retry has a new run UUID, its task UUID, `parent_experiment_id` and `parent_run_id`. It attempts only the original 62 Claude incompletes, canary first and then the original relative order. Completed primary outputs and all GPT attempts are excluded.

### Recommended Generation Limits

Use the **Retry** column below as the recommended limits for this repository's future GDPval generation jobs. Keep concurrency at one and transport retries bounded at three requests per response slot. These recommendations are supported by the Claude failure diagnosis and successful canary, not a guarantee of full-set completion or quality.

For a new paired comparison, apply and freeze the recommended task-level limits for both generators and smoke-test each provider's request limits. Do not change an existing frozen experiment on resume. This records a recommendation only; the original runner defaults and experiment manifests remain unchanged. Grading budgets require a separate configuration.

| Limit                             |       Primary |         Retry |
| --------------------------------- | ------------: | ------------: |
| Output tokens per response        |        10,000 |        32,000 |
| Generated tokens per conversation |        50,000 |       150,000 |
| Model turns                       |            14 |            28 |
| Executed tool calls               |            24 |            48 |
| HTTP read timeout                 |   240 seconds |   600 seconds |
| Scheduling deadline               | 1,800 seconds | 1,800 seconds |
| Python tool timeout               |   150 seconds |   150 seconds |

Same Claude endpoint and default reasoning, automatic tools, installed dependencies, reference bytes, attachment policy and approved best-effort local security restrictions. The system instruction reflects the increased turn/tool limits. Transport retries remain bounded at three requests per response slot with UUID-linked ledgers and unknown-charge accounting. Source hashes, original manifest hash and parent inputs are verified before resume. A failed first canary blocks the batch; authentication/quota failures and three consecutive provider errors halt scheduling. Finished retry attempts are not automatically regenerated.

Retry experiment UUID: `74a6f62c-1949-4067-9598-dddb9ff59232`, stored in `gdpval-data/retry_runs/cf411732-395f-430f-941b-9f8ac208918f`. Three focused offline tests passed; editor diagnostics were clear. The live canary, linked to parent run `2d7ba696-004a-4103-889b-5b0c5cccb2ea`, completed in 25 turns with 26 tool calls, 63,930 generated tokens and 1,387.844 seconds of recorded conversation time. It saved a notebook, seven figures and a findings document. Its original attempt stopped after one 10,000-token response without tools or artifacts. This validates generation flow and artifact creation, not professional quality or rubric satisfaction.

Resume from the repository root:

```powershell
uv run --no-project --python .venv\Scripts\python.exe python turing/field_engineer_take_home_project/retry_claude.py run --experiment gdpval-data/retry_runs/cf411732-395f-430f-941b-9f8ac208918f
```

Use `status` instead of `run` for a read-only snapshot. The remaining 61 attempts were launched as a sequential unattended process after the canary passed. The independent monitor updates `progress.json` and `progress.log` every 180 seconds; generation output is in `generation.log` and `generation-errors.log`. Coverage, artifacts, raw responses, tool traces and request ledgers remain in the retry directory. Grading is not invoked.
