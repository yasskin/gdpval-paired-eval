# GDPval Full Run: OpenAI vs. Anthropic

**Updated November 17, 2026; grading export November 11.**

**Bottom line:** GPT completed with at least one artifact on **211/220 tasks (95.9%)**, versus Claude on **144/220 (65.5%)** under the primary limits. This is a delivery proxy, not a correctness score. Provisional quality outcomes are judge-sensitive and mostly unresolved; there is no defensible overall quality winner.

## What We Tested

All **220 public GDPval gold tasks across 44 occupations**, one fresh attempt each by **GPT-6 Astra** (`gpt-6-astra`, low reasoning) and **Claude Opus 5.5** (`databricks-claude-opus-5-5`, endpoint defaults). Both used shared local Python, web and image tools, with 14 turns, 24 executed tool calls and 50,000 generated tokens per conversation. GPT ran first, then Claude; reasoning compute was not matched.

Both models separately judged both generators using the original weighted rubrics and blinded wrapper identities. Of **880 assignments, 857 yielded valid assessments**, nine were invalid, four failed and 10 were unavailable because of five primary infrastructure failures. Validity checks do not establish professional grading accuracy.

## Full-Set Results

| Primary outcome | GPT | Claude |
| --- | ---: | ---: |
| Conversation completed | 212/220 | 158/220 |
| Completed with any artifact (headline) | 211/220 | 144/220 |
| Any artifact, including runs that hit a limit | 212/220 | 153/220 |
| Incomplete conversation | 3/220 | 62/220 |
| Completed without artifacts | 1/220 | 14/220 |
| Provider/harness error | 5/220 | 0/220 |

| Judge; all 220 paired tasks | GPT favored | Claude favored | Tie | Unresolved |
| --- | ---: | ---: | ---: | ---: |
| OpenAI judge | 38 | 31 | 8 | 143 |
| Claude judge | 26 | 50 | 10 | 134 |

Both judges favor GPT on 17 tasks and Claude on 29; eight tasks have opposite-direction decisions. Unverified evidence accounts for **9,811/40,318 criterion decisions (24.3%)** in valid assessments. Overlapping score bounds are unresolved, not ties or statistical confidence intervals. Judges are not averaged; missing assessments are not semantic zeros.

## By Sector (exploratory)

GDPval's nine sectors have 20–25 tasks each. Paired tests compare the models task by task: exact McNemar for delivery and an exact sign test on decided pairs for each judge. Per-sector p-values are Holm-adjusted across the nine sectors, and a permutation test checks whether the gap varies by sector.

![Delivery by sector](site/sector_delivery.svg)

- **Delivery gap varies by sector (permutation p = 0.019).** GPT delivers on 88–100% of tasks in every sector, while Claude ranges from **9/25 in Finance & insurance** to **24/25 in Wholesale trade**.
- **Only Finance & insurance is significant after correction (15 GPT-only vs. 0 Claude-only; adjusted p < 0.001).** Claude was incomplete on 15/25 Finance tasks. Seven sectors show 28–32-point GPT leads that are nominally significant (p < 0.05) but not after Holm correction, and Wholesale trade shows no gap.

![Quality by sector](site/sector_quality.svg)

- **No sector shows a significant quality difference under either judge.** The smallest adjusted p is 0.63, and the quality pattern does not vary by sector (permutation p = 0.91 with the OpenAI judge; p = 0.32 with the Claude judge).
- Pooled across sectors, the OpenAI judge's 38–31 split is not significant (p = 0.47). The Claude judge's 50–26 split for Claude is significant (p = 0.008), consistent with apparent self-preference rather than a reliable quality verdict.

This breakdown was not pre-registered, sectors are small, and sector is confounded with file types and inputs. Treat it as hypothesis-generating. Source: `analyze_sectors.py` → `site/sector_results.json`.

## Observed Gaps and Data Opportunities

- **GPT:** three malformed/truncated web-tool arguments caused parser failures. Candidate intervention: bounded tool-call examples and safe recovery tests, alongside adapter fixes; transport timeouts are not training-data failures.
- **Claude:** 62 incomplete attempts and 13 completed-but-tool-exhausted attempts expose budget/file-production gaps. Candidate data: long-horizon workflows with budget accounting, early artifact checkpoints and deliverable acceptance checks.
- **Both:** uncertain and conflicting grades motivate expert-reviewed, source-linked rubrics and inspectable gold artifacts before asserting substantive quality gaps.

**Separate retry study:** fresh, higher-budget attempts on the 62 Claude incompletes produced 54 completed conversations (87.1%); 53 had at least one listed artifact. Four remained incomplete and four had provider errors. Multiple limits changed together; retry quality is ungraded and results never replace the primary.

**Limits and cost:** single attempts; sequential provider passes; incomplete modality support; no full-set Office rendering/recalculation or live citation verification; no expert adjudication or final 30-task audit. Primary generation alone recorded **68.62 million tokens**; grading, retries and development are additional. Total USD charges remain unreconciled. Local execution was not a hardened sandbox.

**Next:** audit disagreements and the frozen-rule review slice, then turn verified failures into a concrete dataset proposal and audience-specific pitches.

[Detailed findings and evidence](PROVISIONAL_FAILURE_FINDINGS.md) | [Full grading export](../../gdpval-data/full_grades/primary-v1/reports/FINDINGS.md) | [Analysis plan](PROJECT_PLAN.md) | [Separate development pilot](PILOT_RESULTS.md)
