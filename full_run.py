import argparse
import collections
import csv
import hashlib
import json
import math
import os
import random
import tempfile
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pilot
import requests


def initialize(root, collection):
    if len(collection) != 220:
        raise ValueError("Expected all 220 GDPval tasks")
    occupations = collections.Counter(task["occupation"] for task in collection.values())
    if len(occupations) != 44 or set(occupations.values()) != {5}:
        raise ValueError("Expected 44 occupations with five tasks each")
    for task_id, task in collection.items():
        UUID(task_id)
        if task["task_id"] != task_id or not task["prompt"].strip():
            raise ValueError("Invalid task identity or prompt")
        rubric = json.loads(task["rubric_json"])
        if not isinstance(rubric, list) or not rubric:
            raise ValueError("Empty rubric")
        criterion_ids = [str(UUID(item["rubric_item_id"])) for item in rubric]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("Duplicate rubric criterion")
        for item in rubric:
            score = item["score"]
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not item["criterion"].strip():
                raise ValueError("Invalid rubric weight or criterion")
        if sum(max(item["score"], 0) for item in rubric) <= 0:
            raise ValueError("No positive rubric denominator")
    task_ids = sorted(collection)
    random.Random(20261104).shuffle(task_ids)
    experiment_id = str(uuid4())
    root.mkdir(parents=True, exist_ok=False)
    policy = {
        **pilot.POLICY,
        "pilot_only": False,
        "concurrency": 1,
        "transport_retries": 2,
        "uncapped_budget_approved": True,
        "local_execution_approved": True,
        "capability_limits_approved": True,
        "user_authorization": "Full-run uncapped spending, local execution limitations, capability-limited task labels and existing model settings explicitly approved by the user.",
        "security_deviation": "Explicitly approved credential-stripped local subprocesses; best-effort audit restrictions, NOT a hardened sandbox.",
        "judge_policy": "Generation only; grading requires a separate stage. Pilot judgments are provisional and not reused.",
        "provider_order": ["openai", "anthropic"],
        "unsupported_modalities": "Attempt all tasks; label audio/video/PSD/STEP and archive capability limits. No claim of native listening or full support.",
    }
    manifest = {
        "experiment_id": experiment_id,
        "created_at": pilot.now(),
        "policy": policy,
        "dataset_sha256": {path.name: pilot.digest(path) for path in sorted((pilot.DATA / "data").glob("*.parquet"))},
        "source_sha256": {name: pilot.digest(pilot.PROJECT / name) for name in ("full_run.py", "pilot.py", "pilot_tools.py", "pilot_worker.py")},
        "dependencies": {distribution.metadata["Name"]: distribution.version for distribution in pilot.importlib.metadata.distributions()},
        "selection": [],
        "runs": [],
        "judgments": [],
    }
    for task_id in task_ids:
        UUID(task_id)
        task = collection[task_id]
        references = []
        for filename in task["reference_files"]:
            source = (pilot.DATA / filename).resolve()
            if not source.is_relative_to((pilot.DATA / "reference_files").resolve()) or not source.is_file() or source.stat().st_size == 0:
                raise ValueError("Missing or unsafe reference: " + filename)
            references.append({"path": filename, "sha256": pilot.digest(source), "bytes": source.stat().st_size})
        formats = {Path(item["path"]).suffix.lower() for item in references} | {Path(filename).suffix.lower() for filename in task.get("deliverable_files", [])}
        limits = sorted(formats & {".wav", ".mp3", ".mp4", ".psd", ".step", ".zip"})
        manifest["selection"].append({"task_id": task_id, "occupation": task["occupation"], "references": references, "capability_limits": limits, "prompt_sha256": hashlib.sha256(task["prompt"].encode()).hexdigest()})
    for provider in policy["provider_order"]:
        for selection in manifest["selection"]:
            manifest["runs"].append({"run_id": str(uuid4()), "experiment_id": experiment_id, "task_id": selection["task_id"], "provider": provider, "model": pilot.MODELS[provider], "status": "not_run", "capability_limits": selection["capability_limits"]})
    pilot.save(root / "experiment.json", manifest)
    return manifest


@contextmanager
def exclusive(root):
    with (root / "launcher.lock").open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def verify(root, collection):
    manifest = json.loads((root / "experiment.json").read_text(encoding="utf-8"))
    if manifest["policy"].get("pilot_only") or not all(manifest["policy"].get(name) for name in ("uncapped_budget_approved", "local_execution_approved", "capability_limits_approved")):
        raise ValueError("Full-run approvals missing")
    expected = {(task_id, provider) for task_id in collection for provider in ("openai", "anthropic")}
    actual = {(run["task_id"], run["provider"]) for run in manifest["runs"]}
    if len(collection) != 220 or len(manifest["runs"]) != 440 or actual != expected or len({run["run_id"] for run in manifest["runs"]}) != 440:
        raise ValueError("Incomplete or duplicate full-set run manifest")
    for run in manifest["runs"]:
        if run["experiment_id"] != manifest["experiment_id"] or run["model"] != manifest["policy"]["generator_models"][run["provider"]]:
            raise ValueError("Run identity/model mismatch")
    for name, checksum in manifest["source_sha256"].items():
        if pilot.digest(pilot.PROJECT / name) != checksum:
            raise ValueError("Frozen source changed: " + name)
    current_dataset = {path.name: pilot.digest(path) for path in sorted((pilot.DATA / "data").glob("*.parquet"))}
    if current_dataset != manifest["dataset_sha256"]:
        raise ValueError("Frozen dataset changed")
    current_dependencies = {distribution.metadata["Name"]: distribution.version for distribution in pilot.importlib.metadata.distributions()}
    if current_dependencies != manifest["dependencies"]:
        raise ValueError("Frozen Python dependencies changed")
    for selection in manifest["selection"]:
        task = collection[selection["task_id"]]
        if hashlib.sha256(task["prompt"].encode()).hexdigest() != selection["prompt_sha256"]:
            raise ValueError("Frozen prompt changed")
        if task["reference_files"] != [item["path"] for item in selection["references"]]:
            raise ValueError("Frozen reference list changed")
        for reference in selection["references"]:
            source = (pilot.DATA / reference["path"]).resolve()
            if not source.is_relative_to((pilot.DATA / "reference_files").resolve()) or pilot.digest(source) != reference["sha256"]:
                raise ValueError("Frozen reference changed")
    return manifest


def http_status(error):
    response = getattr(error, "response", None)
    status = getattr(error, "status_code", None) or (response.status_code if response is not None else None)
    if status is None and isinstance(error, RuntimeError):
        prefix = str(error).partition(":")[0].split()
        if len(prefix) == 3 and prefix[:2] == ["Databricks", "HTTP"] and prefix[2].isdigit():
            status = int(prefix[2])
    return status


def invoke(original, root, run, provider, system, messages, tools, output_tokens):
    directory = root / "runs" / run["run_id"]
    state = json.loads((directory / "conversation.json").read_text(encoding="utf-8"))
    turn = state["turns"]
    attempts = directory / "requests"
    attempts.mkdir(exist_ok=True)
    prior = [json.loads(path.read_text(encoding="utf-8")) for path in attempts.glob("*.json")]
    prior = [item for item in prior if item["turn"] == turn]
    for item in prior:
        if item["status"] == "started":
            item["status"] = "outcome_unknown"
            pilot.save(attempts / (item["request_id"] + ".json"), item)
    for attempt in range(len(prior), 3):
        record = {"request_id": str(uuid4()), "experiment_id": run["experiment_id"], "run_id": run["run_id"], "provider": provider, "turn": turn, "attempt": attempt + 1, "started_at": pilot.now(), "status": "started"}
        path = attempts / (record["request_id"] + ".json")
        pilot.save(path, record)
        try:
            result = original(provider, system, messages, tools, output_tokens)
        except Exception as error:
            status = http_status(error)
            transient = status in {408, 429, 500, 502, 503, 504} or isinstance(error, (requests.Timeout, requests.ConnectionError)) or type(error).__name__ in {"APITimeoutError", "APIConnectionError"}
            record.update(status="failed", error_type=type(error).__name__, http_status=status, outcome_unknown=status is None or status >= 500 or status == 408, finished_at=pilot.now())
            pilot.save(path, record)
            if not transient or attempt == 2:
                raise RuntimeError(f"Provider request failed: {type(error).__name__}; HTTP {status}; see request ledger") from None
            time.sleep((5, 15)[attempt])
        else:
            pilot.save(directory / f"response-{turn:02d}.json", result)
            record.update(status="completed", usage=result["usage"], finished_at=pilot.now())
            pilot.save(path, record)
            return result
    raise RuntimeError("Transport attempt limit already exhausted; no new request issued")


def summary(root, manifest, write=True):
    by_provider = {}
    for provider in manifest["policy"]["provider_order"]:
        runs = [run for run in manifest["runs"] if run["provider"] == provider]
        by_provider[provider] = {"statuses": dict(collections.Counter(run["status"] for run in runs)), "artifact_count": sum(len(run.get("artifacts", [])) for run in runs), "metered_tokens": sum(item.get("total_tokens", item.get("input_tokens", item.get("prompt_tokens", 0)) + item.get("output_tokens", item.get("completion_tokens", 0))) for run in runs for item in run.get("usage", []))}
    report = {"experiment_id": manifest["experiment_id"], "updated_at": pilot.now(), "providers": by_provider, "halt": manifest.get("halt"), "grading": "not_run", "usd": "unreconciled; uncapped budget approved", "limitations": manifest["policy"]["security_deviation"]}
    if not write:
        return report
    pilot.save(root / "status.json", report)
    with (root / "coverage.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["experiment_id", "task_id", "run_id", "provider", "model", "status", "artifact_count", "capability_limits"])
        writer.writeheader()
        for run in manifest["runs"]:
            writer.writerow({**{key: run[key] for key in ("experiment_id", "task_id", "run_id", "provider", "model", "status")}, "artifact_count": len(run.get("artifacts", [])), "capability_limits": ";".join(run["capability_limits"])})
    return report


def generate(root, collection):
    manifest = verify(root, collection)
    pilot.POLICY.update(manifest["policy"])
    original = pilot.invoke
    manifest.pop("halt", None)
    consecutive_errors = 0
    for index, run in enumerate(manifest["runs"]):
        if run["status"] != "not_run":
            continue
        saved = root / "runs" / run["run_id"] / "run.json"
        prior = json.loads(saved.read_text(encoding="utf-8")) if saved.exists() else None
        if prior and any(prior[key] != run[key] for key in ("run_id", "experiment_id", "task_id", "provider", "model")):
            raise ValueError("Run checkpoint identity mismatch")
        if prior and prior["status"] != "not_run":
            result = prior
        else:
            pilot.invoke = lambda *arguments: invoke(original, root, run, *arguments)
            try:
                result = pilot.generate_run(root, run, collection[run["task_id"]])
            except Exception as error:
                result = {**run, "status": "harness_error", "error_type": type(error).__name__, "finished_at": pilot.now()}
            finally:
                pilot.invoke = original
        manifest["runs"][index] = result
        consecutive_errors = consecutive_errors + 1 if result["status"] == "provider_error" else 0
        requests_directory = root / "runs" / run["run_id"] / "requests"
        failures = [json.loads(path.read_text(encoding="utf-8")) for path in requests_directory.glob("*.json")]
        blocked = any(item.get("http_status") in {401, 402, 403, 429} for item in failures) and result["status"] == "provider_error"
        if blocked or consecutive_errors >= 3:
            manifest["halt"] = {"at": pilot.now(), "run_id": run["run_id"], "reason": "Authentication, quota/rate limit, or three consecutive provider errors; fix externally then resume. Failed tasks are not automatically regenerated."}
        pilot.save(root / "experiment.json", manifest)
        print(json.dumps(summary(root, manifest)), flush=True)
        if manifest.get("halt"):
            break
    return manifest


class FullRunTests(unittest.TestCase):
    def test_all_tasks_sequential_and_resume(self):
        collection = self.collection()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "experiment"
            manifest = initialize(root, collection)
            self.assertEqual(len(manifest["runs"]), 440)
            self.assertEqual(len({run["run_id"] for run in manifest["runs"]}), 440)
            self.assertEqual([run["provider"] for run in manifest["runs"][:220]], ["openai"] * 220)
            self.assertEqual([run["task_id"] for run in manifest["runs"][:220]], [run["task_id"] for run in manifest["runs"][220:]])
            with patch("builtins.print"), patch.object(pilot, "generate_run", side_effect=lambda root, run, task: {**run, "status": "completed"}) as worker:
                generate(root, collection)
                self.assertEqual(worker.call_count, 440)
                generate(root, collection)
                self.assertEqual(worker.call_count, 440)

    def collection(self):
        result = {}
        for index in range(220):
            task_id = str(uuid4())
            result[task_id] = {"task_id": task_id, "prompt": "test", "occupation": str(index // 5), "reference_files": [], "rubric_json": json.dumps([{"rubric_item_id": str(uuid4()), "criterion": "test", "score": 1}])}
        return result

    def test_changed_prompt_blocks_requests(self):
        collection = self.collection()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "experiment"
            initialize(root, collection)
            next(iter(collection.values()))["prompt"] = "changed"
            with self.assertRaises(ValueError), patch.object(pilot, "generate_run") as worker:
                generate(root, collection)
            worker.assert_not_called()

    def test_retry_is_bounded_and_preserves_unknown_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = {"run_id": str(uuid4()), "experiment_id": str(uuid4())}
            working = root / "runs" / run["run_id"]
            working.mkdir(parents=True)
            pilot.save(working / "conversation.json", {"turns": 0})
            original = Mock(side_effect=requests.Timeout())
            with patch.object(time, "sleep"), self.assertRaises(RuntimeError):
                invoke(original, root, run, "openai", "", [], [], 100)
            self.assertEqual(original.call_count, 3)
            records = [json.loads(path.read_text()) for path in (working / "requests").glob("*.json")]
            self.assertTrue(all(record["outcome_unknown"] for record in records))
            with self.assertRaises(RuntimeError):
                invoke(original, root, run, "openai", "", [], [], 100)
            self.assertEqual(original.call_count, 3)

    def test_exclusive_lock_rejects_second_launcher(self):
        with tempfile.TemporaryDirectory() as directory, exclusive(Path(directory)), self.assertRaises(OSError), exclusive(Path(directory)):
            self.fail("Second launcher acquired the lock")

    def test_authentication_failure_stops_scheduling(self):
        collection = self.collection()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "experiment"
            initialize(root, collection)

            def failure(root, run, task):
                requests_directory = root / "runs" / run["run_id"] / "requests"
                requests_directory.mkdir(parents=True)
                pilot.save(requests_directory / "failed.json", {"http_status": 401})
                return {**run, "status": "provider_error"}

            with patch("builtins.print"), patch.object(pilot, "generate_run", side_effect=failure) as worker:
                manifest = generate(root, collection)
            self.assertEqual(worker.call_count, 1)
            self.assertIsNotNone(manifest.get("halt"))
            self.assertEqual(sum(run["status"] == "not_run" for run in manifest["runs"]), 439)


def check_access():
    try:
        model = pilot.OpenAI(timeout=30, max_retries=0).models.retrieve(pilot.MODELS["openai"])
        configuration = pilot.Config(profile=pilot.PROFILE)
        if configuration.host.rstrip("/") != os.environ.get("DATABRICKS_HOST", configuration.host).rstrip("/"):
            raise ValueError("Databricks profile points to an unexpected workspace")
        response = requests.get(configuration.host + "/api/2.0/serving-endpoints/" + pilot.MODELS["anthropic"], headers=configuration.authenticate(), timeout=(15, 30))
        response.raise_for_status()
        endpoint = response.json()
        if endpoint.get("state", {}).get("ready") != "READY" or endpoint.get("task") != "llm/v1/chat":
            raise ValueError("Claude endpoint is not ready for chat")
    except Exception as error:
        raise RuntimeError(f"Read-only access preflight failed: {type(error).__name__}; HTTP {http_status(error)}. Refresh authentication externally; no inference issued.") from None
    return {"checked_at": pilot.now(), "openai_model": model.id, "claude_endpoint": endpoint["name"], "scope": "Read-only metadata; no new inference or modality test"}


def main():
    parser = argparse.ArgumentParser(description="Sequential full GDPval generation; no interactive per-task approvals or grading.")
    parser.add_argument("stage", choices=["prepare", "run", "status", "test"])
    parser.add_argument("--experiment", type=Path)
    parser.add_argument("--allow-local-execution", action="store_true")
    parser.add_argument("--allow-capability-limits", action="store_true")
    parser.add_argument("--uncapped-budget", action="store_true")
    arguments = parser.parse_args()
    if arguments.stage == "test":
        unittest.main(argv=[__file__])
        return
    if arguments.stage == "status":
        if not arguments.experiment:
            parser.error("--experiment is required")
        root = arguments.experiment.resolve()
        print(json.dumps(summary(root, json.loads((root / "experiment.json").read_text(encoding="utf-8")), write=False), indent=2))
        return
    if arguments.experiment:
        if arguments.stage == "prepare":
            parser.error("prepare creates a new UUID experiment; omit --experiment")
        root = arguments.experiment.resolve()
    else:
        if not all((arguments.allow_local_execution, arguments.allow_capability_limits, arguments.uncapped_budget)):
            parser.error("New experiments require --allow-local-execution --allow-capability-limits --uncapped-budget")
        root = pilot.DATA / "full_runs" / str(uuid4())
        initialize(root, pilot.tasks())
        print("Experiment: " + str(root), flush=True)
    if arguments.stage == "prepare":
        print(json.dumps(summary(root, verify(root, pilot.tasks())), indent=2))
    else:
        with exclusive(root):
            manifest = verify(root, pilot.tasks())
            manifest["access_preflight"] = check_access()
            pilot.save(root / "experiment.json", manifest)
            manifest = generate(root, pilot.tasks())
            if manifest.get("halt"):
                raise SystemExit(2)


if __name__ == "__main__":
    main()
