import argparse
import collections
import json
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path


def snapshot(manifest):
    providers = {}
    pairs = collections.defaultdict(list)
    for run in manifest["runs"]:
        provider = providers.setdefault(run["provider"], {"completed": 0, "attempted": 0, "total": 0, "incomplete": 0, "failed": 0})
        provider["total"] += 1
        provider["completed"] += run["status"] == "completed"
        provider["attempted"] += run["status"] not in {"not_run", "running"}
        provider["incomplete"] += run["status"] == "incomplete"
        provider["failed"] += run["status"] in {"provider_error", "harness_error", "refused"}
        pairs[run["task_id"]].append(run["status"])
    return {
        "experiment_id": manifest["experiment_id"],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "providers": providers,
        "completed": sum(item["completed"] for item in providers.values()),
        "attempted": sum(item["attempted"] for item in providers.values()),
        "total": len(manifest["runs"]),
        "paired_tasks_completed": sum(len(states) == 2 and all(state == "completed" for state in states) for states in pairs.values()),
        "halt": manifest.get("halt"),
    }


def update(root):
    manifest = json.loads((root / "experiment.json").read_text(encoding="utf-8"))
    report = snapshot(manifest)
    temporary = root / "progress.json.tmp"
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(root / "progress.json")
    parts = []
    for provider, label in (("openai", "GPT"), ("anthropic", "Claude")):
        item = report["providers"].get(provider, {"completed": 0, "total": 0})
        parts.append(f"{label} {item['completed']}/{item['total']}")
    failed = sum(item["failed"] for item in report["providers"].values())
    incomplete = sum(item["incomplete"] for item in report["providers"].values())
    line = f"{report['checked_at']} | Completed: {'; '.join(parts)}; combined {report['completed']}/{report['total']} | attempted {report['attempted']}; incomplete {incomplete}; failed {failed}"
    if report["halt"]:
        line += " | HALTED: " + report["halt"].get("reason", "see experiment manifest")
    with (root / "progress.log").open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")
    print(line, flush=True)
    return report


def watch(root, interval):
    def tick():
        try:
            report = update(root)
            if report["halt"] or report["attempted"] == report["total"]:
                print("Progress monitor stopped: experiment halted or all attempts finished.", flush=True)
                return
        except (OSError, ValueError) as error:
            print(f"Progress snapshot unavailable: {type(error).__name__}; retrying next interval.", flush=True)
        threading.Timer(interval, tick).start()

    tick()


class ProgressTests(unittest.TestCase):
    def test_completed_is_not_attempted(self):
        manifest = {
            "experiment_id": "experiment",
            "runs": [
                {"task_id": "first", "provider": "openai", "status": "completed"},
                {"task_id": "first", "provider": "anthropic", "status": "incomplete"},
                {"task_id": "second", "provider": "openai", "status": "provider_error"},
                {"task_id": "second", "provider": "anthropic", "status": "not_run"},
            ],
        }
        report = snapshot(manifest)
        self.assertEqual((report["completed"], report["attempted"], report["total"]), (1, 3, 4))
        self.assertEqual(report["paired_tasks_completed"], 0)
        self.assertEqual(report["providers"]["openai"]["failed"], 1)


def main():
    parser = argparse.ArgumentParser(description="Independent progress monitor; never invokes providers or modifies evaluation checkpoints.")
    parser.add_argument("--experiment", type=Path)
    parser.add_argument("--interval", type=int, default=180)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--test", action="store_true")
    arguments = parser.parse_args()
    if arguments.test:
        unittest.main(argv=[__file__])
        return
    if arguments.experiment is None or arguments.interval < 30:
        parser.error("--experiment is required; --interval must be at least 30 seconds")
    root = arguments.experiment.resolve()
    if arguments.once:
        update(root)
    else:
        watch(root, arguments.interval)


if __name__ == "__main__":
    main()
