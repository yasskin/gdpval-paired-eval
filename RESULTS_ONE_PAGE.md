# Can AI do real professional work? GPT-6 Astra vs. Claude Opus 5.5 on GDPval

**Updated November 17, 2026** · [Results site](https://yasskin.github.io/evals-site/) · [Code](https://github.com/yasskin/gdpval-paired-eval) · Provisional results; AI-graded, not yet checked by human experts.

**Bottom line:** GPT handed in a file far more often: **211 of 220 tasks (95.9%)**, against **144 of 220 (65.5%)** for Claude. Whose files were *better* is still mostly unclear. The AI judges often could not tell, and each favored its own company's model. Where both judges agreed, Claude's work was better on **29** tasks and GPT's on **17**.

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
- **By sector, only Finance & insurance shows a significant gap.** Claude delivered on 9 of 25 finance tasks, against 24 of 25 in wholesale trade; no sector shows a significant quality difference. Treat this as exploratory: [details](https://yasskin.github.io/evals-site/sectors.html).

## 1. What we ran, how we graded, what it cost

- **Tasks:** all **220 public GDPval gold tasks** from 44 occupations. The brief suggests a 20–40 task slice. We ran all 220 because a single unattended job made it affordable and a full run avoids hand-picking. We then chose a **30-task slice for close inspection** with a rule fixed in advance: six occupations ranked by the score gap that both judges agree on ([how we chose](https://yasskin.github.io/evals-site/methods.html#slice)).
- **Models:** one try per task for GPT-6 Astra (low reasoning) and Claude Opus 5.5 (default settings, via Databricks). Both had the same tools and the same limits: 14 rounds of work, 24 actions and 50,000 written tokens per task. Reasoning effort was not matched.
- **Grading:** each file was graded twice, by a GPT judge and by a Claude judge, against the task's expert-written weighted checklist, without the judges being told which model made it. Judges agree on **95.7%** of pass/fail calls they could both check (kappa 0.85). The Claude judge favors Claude 50–26 (p = 0.008); the GPT judge favors GPT 38–31 (p = 0.47, within chance). We lead with the tasks where both judges agree and **never average the two judges**.
- **Cost:** about **$1,165** at list prices for everything (OpenAI $522, Anthropic $643): main run $401, grading $536, Claude retry $198, pilot $29. These are estimates, not invoices ([breakdown](https://yasskin.github.io/evals-site/methods.html#cost)).

## 2. Failure modes: which matter, and which are noise

- **85 tasks with no usable file (9 GPT, 76 Claude), all classified against the run records.** Most of Claude's are real model-plus-limits gaps: 33 ran out of the token budget, 14 had the final reply cut off, 15 used all 14 turns, and 13 wrote the work as chat text instead of saving the file. GPT's include **noise**: 2 server timeouts, plus 3 web-search requests cut off mid-way (partly the harness).
- **30 errors inside delivered files, in a draft taxonomy** (12 GPT, 12 Claude, 6 shared). We took only checklist items that **both** judges failed, prioritized by weight. 8 are high severity (could mislead a decision) and 4 are grading problems or tool limits, not model weaknesses.
  - **GPT** mostly misses *domain judgment and completeness*: 5 domain-judgment errors, 3 completeness. One example is a heat-map analysis that left out whether a hotspot was within 10 °C of a safety limit.
  - **Claude** mostly makes *quantitative and grounding* errors: 4 quantitative, 3 reference grounding. One example is a wrong legal identifier in a case file.
- The ledger is a draft until each item is hand-checked against the original file ([failures page](https://yasskin.github.io/evals-site/failures.html)).

## 3. Gaps, and the dataset that would close them

| | For OpenAI: "Delivering a file is not the same as finishing the job" | For Anthropic: "Deliver first, then improve" |
| --- | --- | --- |
| **The gap** | Files arrive reliably but skip specific requirements. On 67 of the 143 tasks where both models delivered, both judges failed a GPT item that they passed for Claude. | Claude spends its budget researching and planning, then runs out before saving the file. 76 of 220 tasks ended with no usable file. |
| **Dataset contents** | Requirement-dense deliverables (legal, safety, deal, financial, clinical) with expert gold files, a linked requirement checklist with severity labels, and pairs of polished-but-incomplete drafts with expert corrections. | Long, multi-step assignments with an explicit visible budget; gold sessions that save a basic valid file early and then improve it; failed sessions paired with repaired sessions. The 62 cut-off runs are ready-made examples. |
| **Worth buying for evaluation** | Expert checklists turn "complete" into pass/fail checks, so critical omissions can be counted on held-out tasks. | Automatic acceptance tests (the file exists, opens and matches the requested format) plus expert review of core requirements. |
| **Worth buying for training** | Teaches the model to cover every stated requirement without losing delivery reliability. | Teaches budget management: turn the work into a delivered file within fixed limits. |
| **Test before scaling** | Re-run at a higher reasoning setting with expert omission counts. Build the dataset only if the omissions persist. | Re-run the 62 tasks raising one limit at a time. Build the dataset only if a "save a draft early" instruction does not close the gap. |

Proposed pilot: about 300 tasks for each dataset, scaled only if the held-out test improves.

## 4. Honest limits

- **Sample:** one try per task. Sectors have 20–25 tasks each. The 30-task slice was chosen for large gaps, so it exaggerates differences by design.
- **Grader reliability:** AI judges with measurable self-preference. A quarter of checklist items could not be verified. Calibration was an approval after reviewing a 6-task report, not a human check of the grades. **The human hand audit of the 30 failures is still pending.**
- **Comparability:** reasoning effort was not matched, and Claude ran through Databricks serving. The retry changed several limits at once and its files are ungraded; it never replaces the main results.
- **Cost:** list-price estimates. They exclude web-search fees and Databricks platform charges.

All claims come from our own runs, not from published leaderboards. More detail: [results site](https://yasskin.github.io/evals-site/) · [worked example](https://yasskin.github.io/evals-site/example.html) · [failure findings](PROVISIONAL_FAILURE_FINDINGS.md) · [project plan](PROJECT_PLAN.md) · [code](https://github.com/yasskin/gdpval-paired-eval)