import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import full_run
import pilot
import watch_progress

LIMITS = {"max_output_tokens": 32000, "max_generated_tokens": 150000, "max_turns": 28, "max_tool_calls": 48}
CANARY_PARENT_RUN = "2d7ba696-004a-4103-889b-5b0c5cccb2ea"


def retry_system():
    original = "14 model turns and 24 tool calls"
    if pilot.SYSTEM.count(original) != 1:
        raise ValueError("Original budget instruction changed")
    return pilot.SYSTEM.replace(original, "28 model turns and 48 tool calls")


def selected(parent):
    runs = [run for run in parent["runs"] if run["provider"] == "anthropic" and run["status"] == "incomplete"]
    if len(runs) != 62:
        raise ValueError("Expected exactly 62 original incomplete Claude attempts")
    return sorted(runs, key=lambda run: run["run_id"] != CANARY_PARENT_RUN)


def source_hashes():
    return {name: pilot.digest(pilot.PROJECT / name) for name in ("retry_claude.py", "watch_progress.py")}


def initialize(root, parent_root, collection):
    parent = full_run.verify(parent_root, collection)
    originals = selected(parent)
    experiment_id = str(uuid4())
    manifest = {
        "experiment_id": experiment_id,
        "parent_experiment_id": parent["experiment_id"],
        "parent_root": parent_root.resolve().as_posix(),
        "parent_manifest_sha256": pilot.digest(parent_root / "experiment.json"),
        "created_at": pilot.now(),
        "experiment_type": "fresh_attempt_budget_retry_not_primary_comparison",
        "source_sha256": source_hashes(),
        "system": retry_system(),
        "policy": {**parent["policy"], **LIMITS, "provider_order": ["anthropic"], "request_read_timeout_seconds": 600},
        "protocol_changes": "Fresh conversations/workspaces; larger response/conversation/turn/tool budgets and HTTP timeout. Same endpoint, default reasoning, tools, 1800-second scheduling deadline and local security limitations. No original artifacts or feedback supplied. Canary first, remaining original order unchanged. Generation only.",
        "runs": [],
        "judgments": [],
    }
    for original in originals:
        manifest["runs"].append(
            {
                **{key: original[key] for key in ("task_id", "provider", "model", "capability_limits")},
                "run_id": str(uuid4()),
                "experiment_id": experiment_id,
                "parent_experiment_id": parent["experiment_id"],
                "parent_run_id": original["run_id"],
                "status": "not_run",
            }
        )
    root.mkdir(parents=True, exist_ok=False)
    pilot.save(root / "experiment.json", manifest)
    return manifest


def verify(root, collection):
    manifest = json.loads((root / "experiment.json").read_text(encoding="utf-8"))
    parent_root = Path(manifest["parent_root"])
    parent = full_run.verify(parent_root, collection)
    if pilot.digest(parent_root / "experiment.json") != manifest["parent_manifest_sha256"]:
        raise ValueError("Original experiment changed")
    expected_policy = {**parent["policy"], **LIMITS, "provider_order": ["anthropic"], "request_read_timeout_seconds": 600}
    if manifest["source_sha256"] != source_hashes() or manifest["system"] != retry_system() or manifest["policy"] != expected_policy:
        raise ValueError("Frozen retry protocol changed")
    originals = selected(parent)
    if manifest["parent_experiment_id"] != parent["experiment_id"] or len(manifest["runs"]) != 62 or len({run["run_id"] for run in manifest["runs"]}) != 62:
        raise ValueError("Retry experiment identity or coverage mismatch")
    for run, original in zip(manifest["runs"], originals):
        if run["experiment_id"] != manifest["experiment_id"] or run["parent_experiment_id"] != parent["experiment_id"] or run["parent_run_id"] != original["run_id"]:
            raise ValueError("Retry parent/run identity mismatch")
        if any(run[key] != original[key] for key in ("task_id", "provider", "model", "capability_limits")):
            raise ValueError("Retry task/model mismatch")
    return manifest


def generate(root, collection, limit=None):
    manifest = verify(root, collection)
    canary = manifest["runs"][0]
    if canary["status"] != "not_run" and (canary["status"] != "completed" or not canary.get("artifacts")):
        raise ValueError("Previously failed canary requires inspection; no automatic restart")
    base_invoke = pilot.invoke
    base_post = pilot.requests.post
    attempted = 0
    consecutive_errors = 0

    def adapter(*arguments):
        def post(*positional, **keywords):
            return base_post(*positional, **{**keywords, "timeout": (30, 600)})

        with patch.object(pilot.requests, "post", side_effect=post):
            return base_invoke(*arguments)

    manifest.pop("halt", None)
    with patch.dict(pilot.POLICY, manifest["policy"]), patch.object(pilot, "SYSTEM", manifest["system"]):
        for index, run in enumerate(manifest["runs"]):
            if run["status"] != "not_run":
                continue
            directory = root / "runs" / run["run_id"]
            saved = directory / "run.json"
            prior = json.loads(saved.read_text(encoding="utf-8")) if saved.exists() else None
            if prior and any(prior.get(key) != run[key] for key in ("run_id", "experiment_id", "parent_experiment_id", "parent_run_id", "task_id", "provider", "model")):
                raise ValueError("Retry checkpoint identity mismatch")
            if prior and prior["status"] != "not_run":
                result = prior
            else:
                with patch.object(pilot, "invoke", side_effect=lambda *arguments: full_run.invoke(adapter, root, run, *arguments)):
                    result = pilot.generate_run(root, run, collection[run["task_id"]])
            manifest["runs"][index] = result
            attempted += 1
            consecutive_errors = consecutive_errors + 1 if result["status"] == "provider_error" else 0
            requests = [json.loads(path.read_text(encoding="utf-8")) for path in (directory / "requests").glob("*.json")]
            blocked = result["status"] == "provider_error" and any(item.get("http_status") in {401, 402, 403, 429} for item in requests)
            canary_failed = index == 0 and (result["status"] != "completed" or not result.get("artifacts"))
            if blocked or consecutive_errors >= 3 or canary_failed:
                manifest["halt"] = {"at": pilot.now(), "run_id": run["run_id"], "reason": "Canary failed, authentication/quota blocked, or three consecutive provider errors; inspect before resume."}
            pilot.save(root / "experiment.json", manifest)
            full_run.summary(root, manifest)
            watch_progress.update(root)
            if manifest.get("halt") or (limit is not None and attempted >= limit):
                break
    return manifest


class RetryTests(unittest.TestCase):
    def parent(self):
        return {"experiment_id": str(uuid4()), "policy": dict(pilot.POLICY), "runs": [{"run_id": CANARY_PARENT_RUN if index == 0 else str(uuid4()), "task_id": str(uuid4()), "provider": "anthropic", "model": pilot.MODELS["anthropic"], "capability_limits": [], "status": "incomplete"} for index in range(62)] + [{"provider": "openai", "status": "incomplete"}, {"provider": "anthropic", "status": "completed"}]}

    def test_exact_selection_parent_links_and_immutable_parent(self):
        parent = self.parent()
        with tempfile.TemporaryDirectory() as temporary, patch.object(full_run, "verify", return_value=parent):
            parent_root = Path(temporary)
            pilot.save(parent_root / "experiment.json", parent)
            before = pilot.digest(parent_root / "experiment.json")
            root = parent_root / "retry"
            manifest = initialize(root, parent_root, {})
            self.assertEqual(len(manifest["runs"]), 62)
            self.assertEqual(manifest["runs"][0]["parent_run_id"], CANARY_PARENT_RUN)
            self.assertTrue(all(run["parent_experiment_id"] == parent["experiment_id"] for run in manifest["runs"]))
            self.assertEqual(verify(root, {}), manifest)
            self.assertEqual(pilot.digest(parent_root / "experiment.json"), before)
            manifest["runs"][0]["task_id"] = str(uuid4())
            pilot.save(root / "experiment.json", manifest)
            with self.assertRaisesRegex(ValueError, "task/model"):
                verify(root, {})

    def test_canary_gate_and_resume(self):
        parent = self.parent()
        with tempfile.TemporaryDirectory() as temporary, patch.object(full_run, "verify", return_value=parent), patch("builtins.print"):
            parent_root = Path(temporary)
            pilot.save(parent_root / "experiment.json", parent)
            root = parent_root / "retry"
            manifest = initialize(root, parent_root, {})
            collection = {run["task_id"]: {} for run in manifest["runs"]}
            with patch.object(pilot, "generate_run", side_effect=lambda root, run, task: {**run, "status": "completed", "artifacts": [{"path": "deliverables/test.pdf"}]}) as worker:
                generate(root, collection, limit=1)
                self.assertEqual(worker.call_count, 1)
                generate(root, collection)
                self.assertEqual(worker.call_count, 62)
                generate(root, collection)
                self.assertEqual(worker.call_count, 62)

    def test_failed_canary_stops(self):
        parent = self.parent()
        with tempfile.TemporaryDirectory() as temporary, patch.object(full_run, "verify", return_value=parent), patch("builtins.print"):
            parent_root = Path(temporary)
            pilot.save(parent_root / "experiment.json", parent)
            root = parent_root / "retry"
            manifest = initialize(root, parent_root, {})
            collection = {run["task_id"]: {} for run in manifest["runs"]}
            with patch.object(pilot, "generate_run", side_effect=lambda root, run, task: {**run, "status": "incomplete"}) as worker:
                result = generate(root, collection)
                self.assertEqual(worker.call_count, 1)
                self.assertIn("halt", result)
                with self.assertRaisesRegex(ValueError, "Previously failed canary"):
                    generate(root, collection)


def main():
    parser = argparse.ArgumentParser(description="Separate, UUID-linked fresh retries of the 62 incomplete Claude attempts.")
    parser.add_argument("command", choices=["prepare", "run", "status", "test"])
    parser.add_argument("--experiment", type=Path)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--limit", type=int)
    arguments = parser.parse_args()
    if arguments.command == "test":
        unittest.main(argv=[__file__])
        return
    if arguments.experiment is None or (arguments.limit is not None and arguments.limit < 1):
        parser.error("--experiment required; --limit must be positive")
    root = arguments.experiment.resolve()
    if arguments.command == "status":
        manifest = json.loads((root / "experiment.json").read_text(encoding="utf-8"))
        print(json.dumps(full_run.summary(root, manifest, write=False), indent=2))
    elif arguments.command == "prepare":
        if arguments.parent is None:
            parser.error("--parent required for prepare")
        manifest = initialize(root, arguments.parent.resolve(), pilot.tasks())
        print(json.dumps(full_run.summary(root, manifest)))
    else:
        with full_run.exclusive(root):
            manifest = generate(root, pilot.tasks(), arguments.limit)
        if manifest.get("halt"):
            raise SystemExit(2)


if __name__ == "__main__":
    main()
