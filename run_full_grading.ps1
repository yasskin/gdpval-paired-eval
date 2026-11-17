param(
    [string]$Workspace = 'gdpval-data/full_grades/primary-v1',
    [string]$Approval = 'gdpval-data/full-grading-approval.json',
    [switch]$ValidateOnly,
    [switch]$PrepareOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repository = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $repository
$Workspace = (Resolve-Path $Workspace).Path
$Approval = (Resolve-Path $Approval).Path
$grader = Join-Path $PSScriptRoot 'full_grade.py'
$policy = Get-Content -Raw -Encoding UTF8 (Join-Path $Workspace 'policy.json') | ConvertFrom-Json
$authorization = Get-Content -Raw -Encoding UTF8 $Approval | ConvertFrom-Json

function Read-GradingState {
    Get-Content -Raw -Encoding UTF8 (Join-Path $Workspace 'grading.json') | ConvertFrom-Json
}

function Get-StatusCounts($State) {
    $counts = [ordered]@{}
    foreach ($status in @('not_run', 'completed', 'invalid_grade', 'failed', 'blocked', 'unavailable')) {
        $counts[$status] = @($State.assignments | Where-Object { $_.status -eq $status }).Count
    }
    [pscustomobject]$counts
}

function Save-Progress($State, [string]$Stage, [int]$Batch) {
    $progress = [ordered]@{
        grading_id = $State.grading_id
        checked_at = [DateTime]::UtcNow.ToString('o')
        stage = $Stage
        batch = $Batch
        statuses = Get-StatusCounts $State
    }
    $progress | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Workspace 'full-progress.json')
    Write-Output ($progress | ConvertTo-Json -Depth 5 -Compress)
}

$state = Read-GradingState
$policyHash = (Get-FileHash (Join-Path $Workspace 'policy.json') -Algorithm SHA256).Hash.ToLowerInvariant()
$calibrationHash = (Get-FileHash (Join-Path $Workspace 'calibration-results.json') -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $authorization.approved -or $authorization.scope -ne 'full' -or
    -not $authorization.corporate_workload_approved -or -not $authorization.local_parser_limits_approved -or
    -not $authorization.calibration_review.approved -or -not $policy.budget.uncapped_approved -or
    $authorization.grading_id -ne $state.grading_id -or $authorization.policy_sha256 -ne $policyHash -or
    $authorization.calibration_review.results_sha256 -ne $calibrationHash) {
    throw 'Full-stage approval, workload approval or frozen hash binding failed.'
}
if ($policy.max_assessments_per_launch -ne 24) {
    throw 'This launcher requires the frozen 24-assessment batch policy.'
}
if ($ValidateOnly) {
    Write-Output ('Validated full-stage approval; no inference. Counts: ' + ((Get-StatusCounts $state) | ConvertTo-Json -Compress))
    return
}

$contextCode = @'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import full_grade as fg
workspace = Path(sys.argv[2])
state = fg.read(workspace / 'grading.json')
pending = [item for item in state['assignments'] if item['status'] in {'not_run', 'blocked'}][:24]
deferred = []
for assignment in pending:
    try:
        fg.prepare_judge(workspace, assignment, state)
    except PermissionError:
        deferred.append(assignment)
for assignment in deferred:
    directory = workspace / 'judgments' / assignment['assessment_id']
    building = directory / 'context-build'
    context = directory / 'context'
    if not context.exists():
        if fg.inventory(building) != fg.read(directory / 'context-inventory.json'):
            raise ValueError('Staged context differs from its saved inventory')
        try:
            building.rename(context)
        except PermissionError:
            print('Verified context rename is locked; offline preparation may resume.', file=sys.stderr, flush=True)
            sys.exit(75)
    fg.prepare_judge(workspace, assignment, state)
print('Offline contexts prepared:', len(pending), flush=True)
'@

function Invoke-ContextPreparation {
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        & uv run --no-sync python -c $contextCode $PSScriptRoot $Workspace
        if ($LASTEXITCODE -eq 0) { return }
        if ($LASTEXITCODE -ne 75) { throw 'Offline context setup failed; no new grading batch launched.' }
        Write-Output "Offline context rename locked on preparation attempt $attempt of 3."
    }
    throw 'Offline context rename remained locked after three preparation attempts; no inference attempted.'
}

$launcherLock = [System.IO.File]::Open((Join-Path $Workspace 'full-launcher.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
$batch = 0
try {
    if ($PrepareOnly) {
        Invoke-ContextPreparation
        return
    }
    $maximumBatches = [int][Math]::Ceiling((@($state.assignments | Where-Object { $_.status -in @('not_run', 'blocked') }).Count) / 24.0)
    while (@($state.assignments | Where-Object { $_.status -in @('not_run', 'blocked') }).Count -gt 0) {
        if ($batch -ge $maximumBatches) {
            throw 'Batch bound reached with unfinished assignments; inspect recorded failures before resuming.'
        }
        $batch++
        Save-Progress $state 'authentication_check' $batch
        & uv run --no-sync python -c "import os; from databricks.sdk.core import Config; assert os.environ.get('OPENAI_API_KEY'), 'OPENAI_API_KEY is missing'; Config(profile='$($policy.databricks_profile)').authenticate(); print('Provider credentials available; not displayed')"
        if ($LASTEXITCODE -ne 0) { throw 'Authentication failed; no new grading batch launched.' }
        Invoke-ContextPreparation
        $before = Get-StatusCounts $state
        Save-Progress $state 'grading' $batch
        & uv run --no-sync python $grader grade --workspace $Workspace --scope full --allow-paid --approval $Approval --limit 24
        if ($LASTEXITCODE -ne 0) { throw 'Grading batch failed; checkpoints retained.' }
        $state = Read-GradingState
        $after = Get-StatusCounts $state
        Save-Progress $state 'batch_saved' $batch
        if ($after.blocked -gt 0 -or $after.failed -gt $before.failed) {
            throw 'New blocked or failed assessments require inspection before scheduling more paid work.'
        }
        if ($after.not_run -ge $before.not_run) {
            throw 'No pending-assessment progress; stopping rather than repeating paid work.'
        }
    }
    Save-Progress $state 'exporting' $batch
    & uv run --no-sync python $grader aggregate --workspace $Workspace
    if ($LASTEXITCODE -ne 0) { throw 'Report export failed; individual grades remain saved.' }
    Save-Progress (Read-GradingState) 'finished' $batch
}
catch {
    Save-Progress (Read-GradingState) 'halted' $batch
    throw
}
finally {
    $launcherLock.Dispose()
}