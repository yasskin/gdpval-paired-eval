# Six-Task Paired Development Pilot

Executed experiment: `bb4ee7bd-2402-46e4-8891-afad90831589`. See
[paired results](PILOT_RESULTS.md) and [structured results](PILOT_RESULTS.json).
All twelve generation attempts and 24 judge attempts are saved. Ten artifacts were
produced; nine generation conversations completed and three reached limits.
Twenty-three assessments are valid; one Claude judge reached its ten-turn limit.

## Authorization and Limits

The user explicitly approved corporate Databricks use for this workload, requested
no hard dollar ceiling, and chose local execution. This authorizes this pilot only,
not the full 220-task experiment. Model requests, tokens, time and tool calls remain
bounded. Actual dollar charges require separate billing reconciliation.

Local model-generated code runs in a fresh Python subprocess with stripped
credentials and best-effort Python audit restrictions. It is **not a hardened
sandbox**. Reference/artifact inputs remain untrusted. No private directories are
intentionally mounted or exposed. Office rendering uses trusted harness code with
macros disabled and links not updated. Original artifacts are preserved.

Both generators use the same local Python, public-web retrieval/search and image
inspection tools. No provider-hosted search or code interpreter is used. Python
files persist between tool calls; interpreter state does not. Package versions,
source hashes, dataset hashes, reference hashes and policy are saved at preparation.

## Frozen Selection

Selection uses declared input/output requirements before either new model output
is observed. The earlier GPT-4.1 research artifact is not reused or shown to models.

| Task UUID                              | Coverage                                              |
| -------------------------------------- | ----------------------------------------------------- |
| `f84ea6ac-8f9f-428c-b96c-d0884e30f7c7` | No-reference academic research; one-page Word table   |
| `1e5a1d7f-12c1-48c6-afd9-82257b3f2409` | PDF reference; operational Word schedule              |
| `b39a5aa7-cd1b-47ad-b249-90afd22f8f21` | Spreadsheet reference; formula-driven financial model |
| `a69be28f-9a84-47c9-992e-b90446cdca9d` | Spreadsheet analysis; sales presentation as PDF       |
| `b9665ca1-4da4-4ff9-86f2-40b9a8683048` | Image reference; engineering schematic PDF            |
| `ff85ee58-bc9f-4aa2-806d-87edeabb1b81` | Difficult audio modality; resynchronization/mixing    |

## Configurations

- OpenAI generator and judge: `gpt-6-astra`, Responses API, low reasoning effort.
- Anthropic generator and judge: `databricks-claude-opus-5-5`, Databricks CLI REST
  initially, then REST authenticated through `databricks-sdk` with OAuth profile
  `$DATABRICKS_CONFIG_PROFILE`; endpoint-default reasoning settings.
- Automatic tool choice on both; no temperature or forced functions.
- Six tasks, two fresh generation attempts per task, two blinded cross-provider
  assessments per usable attempt: twelve generations and up to 24 assessments.
- At most 14 generation turns, 10 judge turns, 24 tool calls, 10,000 output tokens
  per response, 50,000 generated tokens per conversation, 30 minutes per conversation.
  A request already in flight can exceed that conversation scheduling deadline.
- At most two conversations concurrently; no automatic transport retries or
  regeneration of completed tasks. Seed `20261104` fixes provider ordering.
- Raw responses, per-call usage, tool traces, files, UUID relationships and hashes
  are stored beneath the ignored local dataset directory's pilot subdirectory.
- Resume skips saved responses and completed attempts. Failed attempts are retained,
  not silently replaced. Harness fixes require a documented protocol change.

Development repairs: the CLI killed three requests after one minute of inactivity.
Each received one logged continuation from its saved conversation using SDK OAuth
and REST timeout `(30, 240)` seconds, without resetting the task or limits. The
original request outcomes and charges are unknown. Two completed Claude artifacts
were recovered from structured terminal responses without further inference. The
manifest preserves original termination states, source hashes and amendment history.
These mixed-protocol pilot results are not a frozen confirmatory comparison.

## Evidence and Caveats

Original reference bytes are copied into each separate task workspace. Generators
receive neither rubrics nor expert deliverables. Judges get task-specific rubrics,
reference copies, candidate artifacts and derived inspection files, but no generator
label, generation conversation or other judge's assessment.

Images/PDF pages are converted identically to RGB JPEG at maximum 1800 pixels and
quality 88; this loses detail. Audio supports numerical DSP, waveform inspection
and LUFS measurement, but **not native listening**. Perceptual audio criteria must
remain unverified. This stratum is a tool-capability experiment, not evidence of
native audio-model performance. Public web access can fail or provide weak results;
source provenance and limitations must remain visible.

Word/PDF inspection uses actual rendered pages. Workbook evidence includes formulas
and, when Excel is available, a recalculated derived copy. No renderer success is
assumed. Missing evidence is unverified. Binary rubric decisions and original
weights (including penalties) are aggregated locally; unverified criteria produce
score bounds rather than manufactured certainty. These are unofficial, uncalibrated
judgments. No claim is made of professional domain-expert adjudication.

## Commands

Run from the repository root using the existing Python 3.12 environment:

```powershell
uv run --no-project --python .venv\Scripts\python.exe python -m unittest discover -s turing\field_engineer_take_home_project -p "pilot*.py" -v
uv run --no-project --python .venv\Scripts\python.exe python turing\field_engineer_take_home_project\pilot.py prepare
uv run --no-project --python .venv\Scripts\python.exe python turing\field_engineer_take_home_project\pilot.py generate --experiment <printed-experiment-directory>
uv run --no-project --python .venv\Scripts\python.exe python turing\field_engineer_take_home_project\pilot_grade.py <printed-experiment-directory>
uv run --no-project --python .venv\Scripts\python.exe python turing\field_engineer_take_home_project\pilot_report.py <printed-experiment-directory>
```

The prepared manifest contains exact installed dependency versions. Required extra
packages are python-docx, openpyxl, python-pptx, reportlab, pymupdf, pypdf,
soundfile and pyloudnorm, alongside the existing OpenAI, PyArrow, NumPy/SciPy,
pandas, Pillow, matplotlib, requests, databricks-sdk and Windows COM packages.

## Non-Expert Spot Review

Contact sheets of all seven PDF/rendered-document artifacts were visually reviewed.
The research one-page failure was confirmed. GPT's property-manager document has a
blank second page, and Claude's sales appendix has right-edge clipped text. Both
financial workbooks were recalculated and scanned: no Excel error-valued cells
were found. This does not prove correct formulas or scenario behavior. Audio was
measured but not listened to. No professional engineering, financial or audio
certification, full source audit, or complete rubric adjudication is claimed.
