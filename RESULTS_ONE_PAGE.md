# Can AI do real professional work? GPT-6 Astra vs. Claude Opus 5.5 on GDPval

**Updated November 18, 2026** · [Results site](https://yasskin.github.io/evals-site/) · [Code](https://github.com/yasskin/gdpval-paired-eval) · Provisional results; AI grades, with a completed human check of the selected failure ledger, not expert adjudication.

**Bottom line:** GPT handed in a file far more often: **211 of 220 tasks (95.9%)**, against **144 of 220 (65.5%)** for Claude. Whose files were *better* is still mostly unclear: the two-judge summary has no agreed winner on **174 of 220 tasks**. Where both judges agreed on a winner, Claude's work was better on **29** tasks and GPT's on **17**. The Claude judge's 50–26 lean toward Claude is unlikely to be chance (p=.008); the GPT judge's 38–31 lean toward GPT is within chance (p=.47).

## Key results in plain English

| Finding | GPT-6 Astra | Claude Opus 5.5 |
| --- | ---: | ---: |
| Finished and saved at least one file (headline) | **211/220** | **144/220** |
| Cut off by a limit before finishing | 3 | 62 |
| Both judges agree this model's work was better | 17 | **29** |
| Clear wins by the GPT judge / Claude judge | 38 / 26 | 31 / 50 |
| Estimated cost per delivered file (answer stage) | $0.58 | $1.93 |

- **Claude often ran out of room.** On 62 tasks it was still working when it hit the limits, and on 13 more it used all 24 actions and then replied in text instead of a file. Given more room in a separate follow-up, it finished 54 of the 62, and 53 of those included a file.
- **On quality, there is no clear overall winner.** About 2 in 3 tasks had no clear winner under either judge. Judges could not verify **24.3%** of checklist items; PowerPoint, video and ZIP files were almost entirely unverifiable.
- **The delivery gap varies by sector** (p=.019), driven mostly by Claude's uneven delivery: it produced files on 9 of 25 Finance & insurance tasks but 24 of 25 Wholesale trade tasks. After correcting for comparisons across nine sectors, Finance & insurance is the only sector with a significant delivery gap. No sector shows a significant quality difference. These sector results are exploratory: [details](https://yasskin.github.io/evals-site/sectors.html).

## 1. What we ran, how we graded, what it cost

- **Tasks:** all **220 public GDPval gold tasks** from 44 occupations. The brief suggests a 20–40 task slice. We ran all 220 because a single unattended job made it affordable and a full run avoids hand-picking. We then selected a **30-task score-inspection slice** with a rule fixed in advance: all five tasks from each of the six eligible occupations ranked highest on score gaps both judges agree on ([how we chose](https://yasskin.github.io/evals-site/methods.html#slice)).
- **Models:** one try per task for GPT-6 Astra (low reasoning) and Claude Opus 5.5 (default settings, via Databricks). Both had the same tools and the same limits: 14 rounds of work, 24 actions and 50,000 written tokens per task. Reasoning effort was not matched.
- **Grading:** each model/task assessment used both a GPT judge and a Claude judge against the task's expert-written weighted checklist, without the judges being told which model made the work. They agree on **95.7%** of pass/fail calls they could both check (kappa 0.85). The Claude judge favors Claude 50–26 (p = 0.008); the GPT judge favors GPT 38–31 (p = 0.47, within chance). We lead with tasks where both judges agree and **never average the two judges**.
- **Cost:** about **$1,165** at list prices for everything (OpenAI $522, Anthropic $643): main run $401, grading $536, Claude retry $198, pilot $29. These are estimates, not invoices ([breakdown](https://yasskin.github.io/evals-site/methods.html#cost)).
- **Coding agent:** used to plan, build, operate and check the workflow; a human approved paid stages, budgets and published claims ([what the agent did](https://yasskin.github.io/evals-site/data.html#agent)).

## 2. Failure modes: which matter, and which are noise

- **85 tasks with no usable file (9 GPT, 76 Claude), all classified against the run records.** Most of Claude's are real model-plus-limits gaps: 33 ran out of the token budget, 14 had the final reply cut off, 15 used all 14 turns, and 13 wrote the work as chat text instead of saving the file. GPT's include **noise**: 2 server timeouts, plus 3 web-search requests cut off mid-way (partly the harness).
- **Separate from the 30-task score-inspection slice, the 30-item failure ledger is now hand-checked.** It contains checklist items both AI judges failed, selected and prioritized for manual review; the 30 entries need not be 30 distinct tasks. The reviewer confirmed 21 as drafted, reclassified 7, and rejected 2 judge fail calls. Final dispositions: 20 model failures, 8 grading/rubric issues, and 2 rejected calls; 8 items are high severity. This is a selected failure sample, not a model-wide error rate. See the [item-by-item audit and notes](https://yasskin.github.io/evals-site/audit.html) and the [failure analysis](https://yasskin.github.io/evals-site/failures.html).
  - **GPT**'s audited model failures mostly involve *domain judgment and completeness*: 5 domain-judgment and 2 completeness items. One example is a heat-map analysis that left out whether a hotspot was within 10 °C of a safety limit.
  - **Claude**'s audited model failures include 2 quantitative, 2 reference-grounding, 2 domain-judgment and 1 format item. These findings are a small, deliberately selected slice, not an estimate of overall error rates.

## 3. Gaps, and the dataset that would close them

| | For OpenAI: "Delivering a file is not the same as finishing the job" | For Anthropic: "Deliver first, then improve" |
| --- | --- | --- |
| **The gap** | Files arrive reliably but skip specific requirements. On 67 of the 143 tasks where both models delivered, both judges failed a GPT item that they passed for Claude. | Claude spends its budget researching and planning, then runs out before saving the file. 76 of 220 tasks ended with no usable file. |
| **Dataset contents** | Requirement-dense deliverables (legal, safety, deal, financial, clinical) with expert gold files, a linked requirement checklist with severity labels, and pairs of polished-but-incomplete drafts with expert corrections. | Long, multi-step assignments with an explicit visible budget; gold sessions that save a basic valid file early and then improve it; failed sessions paired with repaired sessions. The 62 cut-off runs are ready-made examples. |
| **Worth buying for evaluation** | Measures what delivery rates hide: AI judges flagged a GPT checklist miss on 67 of 143 both-delivered tasks. This is a candidate completeness measure, not 67 human-verified errors. On checkable items the judges agreed 95.7% of the time; agreement is not accuracy, so validate against expert-reviewed files before using it as a score. | Tests finishing real work within fixed limits, which grading only the answer text would miss. The headline check (the file exists, opens and matches the format) needs no AI judge. Rerunning with more room separates "can't" from "ran out of room". |
| **Worth buying for training** | Teaches the model to cover every stated requirement without losing delivery reliability. | Teaches budget management: turn the work into a delivered file within fixed limits. |
| **Test before scaling** | Re-run at a higher reasoning setting with expert omission counts. Build the dataset only if the omissions persist. | Re-run the 62 tasks raising one limit at a time. Build the dataset only if a "save a draft early" instruction does not close the gap. |

Pitch assumption: treat GDPval as a stand-in for a Turing-built dataset. Proposed pilot: about 300 tasks per dataset, scaled only if a held-out test with expert-scored critical omissions or completion improves.

## 4. Honest limits

- **Sample:** one try per task. Sectors have 20–25 tasks each. The 30-task slice was chosen for large gaps, so it exaggerates differences by design.
- **Grader reliability:** AI judges with measurable self-preference. A quarter of checklist items could not be verified. Calibration was an approval after reviewing a 6-task report, not a human check of the grades. One reviewer checked all 30 selected ledger items; this spot-check does not validate AI-judge passes, unverified items or overall grades, and is not independent expert adjudication.
- **Comparability:** reasoning effort was not matched, and Claude ran through Databricks serving. The retry changed several limits at once and its files are ungraded; it never replaces the main results.
- **Cost:** list-price estimates. They exclude web-search fees and Databricks platform charges.

All claims come from our own runs, not from published leaderboards. The four sections above cover the brief's evaluation, hand-classified failures, company-specific dataset pitches, and limitations. The required 15-minute OpenAI/Anthropic role-play is a separate live presentation; this handout is not a substitute. More detail: [results site](https://yasskin.github.io/evals-site/) · [worked example](https://yasskin.github.io/evals-site/example.html) · [failure findings](PROVISIONAL_FAILURE_FINDINGS.md) · [project plan](PROJECT_PLAN.md) · [audit CSV](failure_audit.csv) · [code](https://github.com/yasskin/gdpval-paired-eval)