"""Focused offline fixtures; no paid requests, Office execution or system temp."""

import copy
import json
import shutil
import time
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import full_grade as fg


class FullGradeTests(unittest.TestCase):
    def setUp(self):
        self.task_count = 220 if self._testMethodName == "test_880_accounted_offline_snapshot_and_reports" else 8
        self.directory = fg.pilot.DATA / (".full-grade-tests-" + str(uuid4()))
        self.directory.mkdir()
        self.data = self.directory / "data-root"
        (self.data / "data").mkdir(parents=True)
        (self.data / "data" / "fixture.parquet").write_bytes(b"fake dataset, never read as parquet")
        (self.data / "reference_files").mkdir()
        (self.data / "reference_files" / "input.txt").write_bytes(b"original reference\r\n")
        self.source = self.directory / "primary"
        self.source.mkdir()
        self.workspace = self.directory / "grading"
        self.experiment_id = str(uuid4())
        self.collection = {}
        selections, runs = [], []
        for index in range(self.task_count):
            task_id = str(uuid4())
            references = ["reference_files/input.txt"] if index == 0 else []
            rubric = [{"rubric_item_id": str(uuid4()), "criterion": "Deliver an accurate file", "score": 5}, {"rubric_item_id": str(uuid4()), "criterion": "Contains unsupported assertion", "score": -2}]
            task = {"task_id": task_id, "prompt": "Produce a file.\r\nKeep original prompt bytes.", "occupation": "Occupation " + str(index // 5), "reference_files": references, "rubric_json": json.dumps(rubric)}
            self.collection[task_id] = task
            selections.append(
                {
                    "task_id": task_id,
                    "occupation": task["occupation"],
                    "prompt_sha256": fg.text_hash(task["prompt"]),
                    "references": [{"path": ref, "sha256": fg.pilot.digest(self.data / ref), "bytes": (self.data / ref).stat().st_size} for ref in references],
                }
            )
            for provider in fg.PROVIDERS:
                run_id = str(uuid4())
                directory = self.source / "runs" / run_id / "deliverables"
                materialize = index < 8
                if materialize:
                    directory.mkdir(parents=True)
                status = "provider_error" if index == 1 and provider == "openai" else "harness_error" if index == 2 and provider == "openai" else "incomplete" if index == 3 else "completed"
                artifacts = []
                if materialize and index != 3 and status == "completed":
                    artifact = directory / "result.txt"
                    artifact.write_bytes(b"actual candidate\r\n")
                    artifacts.append({"path": "deliverables/result.txt", "sha256": fg.pilot.digest(artifact), "bytes": artifact.stat().st_size})
                run = {"run_id": run_id, "experiment_id": self.experiment_id, "task_id": task_id, "provider": provider, "model": fg.DEFAULT_POLICY["judge_models"][provider], "status": status, "artifacts": artifacts}
                runs.append(run)
                if materialize:
                    fg.save(directory.parent / "run.json", run)
                    (directory.parent / "answer.md").write_text("GENERATOR ID AND FINAL ANSWER MUST NOT ENTER CONTEXT", encoding="utf-8")
        manifest = {
            "experiment_id": self.experiment_id,
            "policy": {"pilot_only": False, "generator_models": fg.DEFAULT_POLICY["judge_models"]},
            "runs": runs,
            "selection": selections,
            "judgments": [],
            "source_sha256": {name: fg.pilot.digest(fg.pilot.PROJECT / name) for name in fg.FROZEN_FILES},
            "dataset_sha256": {"fixture.parquet": fg.pilot.digest(self.data / "data" / "fixture.parquet")},
        }
        fg.save(self.source / "experiment.json", manifest)
        self.data_patch = patch.object(fg.pilot, "DATA", self.data)
        self.data_patch.start()

    def tearDown(self):
        self.data_patch.stop()
        for attempt in range(10):
            try:
                shutil.rmtree(self.directory)
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(0.2)
            else:
                break

    def prepare(self, paid=False):
        policy = copy.deepcopy(fg.DEFAULT_POLICY)
        if paid:
            policy["budget"] = {"uncapped_approved": True, "authorization": "OFFLINE MOCK authorization"}
        return fg.prepare(self.source, self.workspace, policy, self.collection, self.experiment_id, self.task_count)

    def evidence(self):
        return fg.inspect_evidence(self.workspace, worker=lambda path, seconds: {"text": path.read_text()})

    def test_windows_checkpoint_permission_retry(self):
        path = self.directory / "checkpoint.json"
        original_save = fg.pilot.save
        with patch.object(fg.os, "name", "nt"), patch.object(fg.time, "sleep"), patch.object(fg.pilot, "save", side_effect=[PermissionError("locked"), None]) as writer:
            fg.save(path, {"status": "completed"})
        self.assertEqual(writer.call_count, 2)
        with patch.object(fg.os, "name", "nt"), patch.object(fg.time, "sleep"), patch.object(fg.pilot, "save", side_effect=PermissionError("locked")) as writer, self.assertRaises(PermissionError):
            fg.save(path, {"status": "completed"})
        self.assertEqual(writer.call_count, 10)
        original_save(path, {"status": "completed"})
        self.assertEqual(fg.read(path), {"status": "completed"})

    def approval(self, state, scope="calibration"):
        approval = fg.read(self.workspace / "approval-template.json")
        approval.update(approved=True, scope=scope, reviewer="Offline test reviewer", authorization="Mock only", corporate_workload_approved=True, local_parser_limits_approved=True)
        if scope == "full":
            approval["calibration_review"] = {"approved": True, "results_sha256": fg.pilot.digest(self.workspace / "calibration-results.json"), "notes": "Mock review"}
        path = self.directory / (scope + "-approval.json")
        fg.save(path, approval)
        return path

    @staticmethod
    def submission(rubric, positive="pass", negative="unverified"):
        return {
            "criteria": [{"rubric_item_id": item["rubric_item_id"], "verdict": positive if item["score"] > 0 else negative, "evidence": "candidate/result.txt, paragraph 1", "rationale": "Fresh observed evidence or explicitly not inspectable", "confidence": "high"} for item in rubric],
            "limitations": ["Offline fake test"],
        }

    def caller(self, provider, policy, messages, tokens, timeout):
        rubric_text = messages[0]["content"].split("\n\nORIGINAL RUBRIC:\n")[1].split("\n\nFRESH ARTIFACT/REFERENCE EVIDENCE:")[0]
        submission = self.submission(json.loads(rubric_text))
        return {"raw": {"mock": True}, "usage": {"input_tokens": 12, "output_tokens": 20}, "message": {"role": "assistant", "content": None, "tool_calls": [{"id": "grade", "function": {"name": "submit_grade", "arguments": json.dumps(submission)}}]}}

    def test_880_accounted_offline_snapshot_and_reports(self):
        before = fg.inventory(self.source)
        state = self.prepare()
        self.assertEqual(len(state["runs"]), 440)
        self.assertEqual(len(state["assignments"]), 880)
        self.assertEqual(sum(a["status"] == "unavailable" for a in state["assignments"]), 4)
        self.assertEqual(self.evidence(), 440)
        self.assertEqual(self.evidence(), 0)
        with patch.object(fg, "request", side_effect=AssertionError("Must be offline")):
            report = fg.aggregate(self.workspace)
        self.assertEqual(report["judgment_denominator"], 880)
        self.assertEqual(report["judgment_statuses"]["not_run"], 876)
        self.assertEqual(report["paired_by_judge"]["openai"]["unresolved"], 220)
        self.assertEqual(report["operational_outcomes"]["openai"]["primary_attempts"], 220)
        self.assertEqual(len(report["assessments"]), 880)
        self.assertEqual(fg.inventory(self.source), before)
        self.assertEqual((self.workspace / "tasks" / next(iter(self.collection)) / "prompt.txt").read_bytes(), next(iter(self.collection.values()))["prompt"].encode())
        self.assertEqual((self.workspace / "snapshot" / "reference_files" / "input.txt").read_bytes(), b"original reference\r\n")
        self.assertTrue((self.workspace / "reports" / "FINDINGS.md").exists())
        self.assertEqual(len((self.workspace / "reports" / "criteria.csv").read_text().splitlines()), 1761)

    def test_missing_source_not_blanket_zero_and_modified_artifact_rejected(self):
        manifest = fg.read(self.source / "experiment.json")
        original = manifest["runs"][0]
        (self.source / "runs" / original["run_id"] / "deliverables" / "result.txt").unlink()
        state = self.prepare()
        lost = [a for a in state["assignments"] if a["run_id"] == original["run_id"]]
        self.assertEqual([a["status"] for a in lost], ["unavailable", "unavailable"])
        report = fg.aggregate(self.workspace)
        rows = [a for a in report["assessments"] if a["run_id"] == original["run_id"]]
        self.assertEqual((rows[0]["lower_percent"], rows[0]["upper_percent"]), (-40, 100))
        shutil.rmtree(self.workspace)
        other = manifest["runs"][1]
        (self.source / "runs" / other["run_id"] / "deliverables" / "result.txt").write_text("changed")
        with self.assertRaisesRegex(ValueError, "integrity"):
            self.prepare()

    def test_policy_source_and_pairing_integrity_blocks(self):
        self.prepare()
        policy = fg.read(self.workspace / "policy.json")
        policy["max_turns"] += 1
        fg.save(self.workspace / "policy.json", policy)
        with self.assertRaisesRegex(ValueError, "policy changed"):
            fg.verify(self.workspace)
        fg.save(self.workspace / "policy.json", fg.DEFAULT_POLICY)
        (self.source / "new.txt").write_text("changed primary")
        with self.assertRaisesRegex(ValueError, "Primary bytes changed"):
            fg.verify(self.workspace)

    def test_duplicate_pair_and_workspace_overlap_rejected(self):
        with self.assertRaises(ValueError):
            fg.prepare(self.source, self.source / "grading", collection=self.collection, expected_id=self.experiment_id)
        manifest = fg.read(self.source / "experiment.json")
        manifest["runs"][-1]["task_id"] = manifest["runs"][1]["task_id"]
        fg.save(self.source / "experiment.json", manifest)
        with self.assertRaisesRegex(ValueError, "pairing"):
            self.prepare()

    def test_paid_gates_block_before_caller(self):
        state = self.prepare()
        caller = Mock()
        with self.assertRaisesRegex(ValueError, "Paid stage blocked"):
            fg.grade(self.workspace, "calibration", caller=caller)
        approval = self.approval(state)
        with self.assertRaisesRegex(ValueError, "grading budget"):
            fg.grade(self.workspace, "calibration", True, approval, caller=caller)
        caller.assert_not_called()

    def test_calibration_gate_resume_and_isolated_context(self):
        state = self.prepare(paid=True)
        self.evidence()
        approval = self.approval(state)
        caller = Mock(side_effect=self.caller)
        expected = sum(a["status"] == "not_run" and a["task_id"] in state["calibration_task_ids"] for a in state["assignments"])
        self.assertEqual(fg.grade(self.workspace, "calibration", True, approval, caller=caller), expected)
        self.assertEqual(fg.grade(self.workspace, "calibration", True, approval, caller=caller), 0)
        self.assertLessEqual(caller.call_count, 24)
        report = fg.aggregate(self.workspace)
        full = self.approval(state, "full")
        self.assertEqual(fg.grade(self.workspace, "full", True, full, limit=1, caller=caller), 1)
        completed = next(a for a in fg.verify(self.workspace)[0]["assignments"] if a["status"] == "completed" and (self.workspace / "candidates" / a["candidate_id"] / "result.txt").exists())
        context = self.workspace / "judgments" / completed["assessment_id"] / "context"
        self.assertFalse((context / "answer.md").exists())
        self.assertFalse((context / "grading.json").exists())
        self.assertFalse((context / "assessment.json").exists())
        self.assertEqual((context / "candidate" / "result.txt").read_bytes(), b"actual candidate\r\n")
        self.assertEqual(report["task_denominator"], self.task_count)
        self.assertEqual(len(report["quality_by_judge"]), 4)

    def test_full_approval_requires_completed_calibration(self):
        state = self.prepare(paid=True)
        self.evidence()
        fg.aggregate(self.workspace)
        full = self.approval(state, "full")
        with self.assertRaisesRegex(ValueError, "Calibration sample"):
            fg.grade(self.workspace, "full", True, full, caller=Mock())

    def test_schema_penalties_disagreement_and_ties(self):
        rubric = next(iter(self.collection.values()))["rubric_json"]
        rubric = json.loads(rubric)
        self.assertEqual(fg.strict_grade(self.submission(rubric), rubric)["lower_percent"], 60)
        penalty = fg.strict_grade(self.submission(rubric, negative="pass"), rubric)
        self.assertEqual((penalty["lower_percent"], penalty["upper_percent"]), (60, 60))
        self.assertEqual(fg.paired({"lower_percent": 60, "upper_percent": 100}, {"lower_percent": 70, "upper_percent": 90}), "unresolved")
        self.assertEqual(fg.paired(penalty, penalty), "tie")
        self.assertEqual(fg.paired({"lower_percent": 90, "upper_percent": 100}, penalty), "win")
        invalid = self.submission(rubric)
        invalid["criteria"].append(invalid["criteria"][0])
        with self.assertRaises(ValueError):
            fg.strict_grade(invalid, rubric)

    def test_invalid_answer_is_not_grade_or_artifact(self):
        state = self.prepare(paid=True)
        self.evidence()
        approval = self.approval(state)
        caller = Mock(return_value={"message": {"role": "assistant", "content": "Perfect final answer"}, "usage": {"output_tokens": 1}})
        fg.grade(self.workspace, "calibration", True, approval, limit=1, caller=caller)
        assignments = fg.verify(self.workspace)[0]["assignments"]
        self.assertEqual(sum(a["status"] == "invalid_grade" for a in assignments), 1)
        fg.grade(self.workspace, "calibration", True, approval, limit=1, caller=caller)
        self.assertEqual(caller.call_count, 2)

    def test_transport_retry_caps_and_unknown_checkpoint(self):
        directory = self.directory / "judge"
        directory.mkdir()
        caller = Mock(side_effect=fg.pilot.requests.Timeout())
        with patch.object(fg.time, "sleep"), self.assertRaises(RuntimeError):
            fg.response_slot(directory, 0, "openai", fg.DEFAULT_POLICY, [], 200, 100, caller)
        self.assertEqual(caller.call_count, 3)
        with self.assertRaises(RuntimeError):
            fg.response_slot(directory, 0, "openai", fg.DEFAULT_POLICY, [], 200, 100, caller)
        self.assertEqual(caller.call_count, 3)
        ledger = directory / "requests" / "01" / "00.json"
        fg.save(ledger, {"status": "started", "attempt": 1})
        good = Mock(return_value={"message": {"role": "assistant", "content": ""}, "usage": {}})
        fg.response_slot(directory, 1, "openai", fg.DEFAULT_POLICY, [], 200, 100, good)
        self.assertEqual(fg.read(ledger)["status"], "outcome_unknown")

    def test_evidence_errors_checkpoint_without_inference(self):
        self.prepare()
        worker = Mock(side_effect=TimeoutError("fake"))
        self.assertEqual(fg.inspect_evidence(self.workspace, limit=1, worker=worker), 1)
        state, _ = fg.verify(self.workspace)
        evidence = fg.read(self.workspace / "evidence" / (state["runs"][0]["candidate_id"] + ".json"))
        self.assertEqual(evidence["status"], "completed")
        self.assertEqual(evidence["artifacts"][0]["inspection_error"], "TimeoutError")
        self.assertEqual(fg.inspect_local(self.data / "reference_files" / "input.txt", 30), {"text": "original reference\n"})

    def test_checkpoint_recovery_before_aggregate_and_no_consensus(self):
        state = self.prepare(paid=True)
        self.evidence()
        run = state["runs"][0]
        selected = [a for a in state["assignments"] if a["run_id"] == run["run_id"]]
        for index, assignment in enumerate(selected):
            directory, _, _, rubric = fg.prepare_judge(self.workspace, assignment, state)
            submission = self.submission(rubric, positive="pass" if index == 0 else "fail", negative="fail")
            fg.save(directory / "grade-submission.json", submission)
            result = {**assignment, "status": "completed", "score": fg.strict_grade(submission, rubric), "submission_sha256": fg.pilot.digest(directory / "grade-submission.json")}
            fg.save(directory / "assessment.json", result)
        report = fg.aggregate(self.workspace)
        self.assertEqual(report["judgment_statuses"]["completed"], 2)
        self.assertTrue(any(item["kind"] == "disagreement" for item in report["criterion_disagreements_and_unknowns"]))
        self.assertNotIn("consensus_score", report)
        self.assertTrue(all(row["outcome"] == "unresolved" for row in report["pairs"] if row["task_id"] == run["task_id"]))

    def test_independent_judge_budget_exceeds_pilot_ten_turns(self):
        state = self.prepare(paid=True)
        self.evidence()
        assignment = next(a for a in state["assignments"] if a["status"] == "not_run")
        calls = 0

        def caller(provider, policy, messages, tokens, timeout):
            nonlocal calls
            calls += 1
            if calls <= 11:
                return {"message": {"role": "assistant", "content": None, "tool_calls": [{"id": str(calls), "function": {"name": "inspect", "arguments": '{"path":"candidate/result.txt"}'}}]}, "usage": {"output_tokens": 1}}
            return self.caller(provider, policy, messages, tokens, timeout)

        with patch.object(fg, "judge_tool", return_value={"inspection": "mock evidence"}):
            result = fg.judge_one(self.workspace, assignment, state, fg.read(self.workspace / "policy.json"), caller)
        self.assertEqual((result["status"], result["turns"]), ("completed", 12))
        self.assertEqual(fg.pilot.POLICY["max_turns"], 14)

    def test_bounded_worker_view_and_path_restriction(self):
        from PIL import Image

        context = self.directory / "context"
        (context / "candidate").mkdir(parents=True)
        Image.new("RGB", (16, 16), "blue").save(context / "candidate" / "fixture.png")
        output = fg.judge_tool("view", {"path": "candidate/fixture.png"}, context, fg.DEFAULT_POLICY, 30)
        self.assertTrue(output["image_url"].startswith("data:image/jpeg;base64,"))
        with self.assertRaises(ValueError):
            fg.judge_tool("inspect", {"path": "../outside.txt"}, context, fg.DEFAULT_POLICY, 30)


if __name__ == "__main__":
    unittest.main()
