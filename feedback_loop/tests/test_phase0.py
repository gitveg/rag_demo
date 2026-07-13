from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

from feedback_loop import processor
from feedback_loop.event_schema import make_event_id, record_event_id
from feedback_loop.failure_classifier import (
    classify_execution_result,
    classify_failure,
    is_knowledge_eligible_failure,
)
from feedback_loop import run_and_collect as collector
from feedback_loop.run_and_collect import analyze_execution
from feedback_loop.utils import load_api_kb, save_json


class EventAndClassificationTests(unittest.TestCase):
    def test_event_id_is_stable(self):
        first = make_event_id("run_1", "task_1", 3, 1, "execution", "abc")
        second = make_event_id("run_1", "task_1", 3, 1, "execution", "abc")
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("evt_"))

    def test_legacy_event_id_is_stable(self):
        record = {
            "timestamp": "2026-07-10T00:00:00",
            "task_id": "task",
            "query": "query",
            "attempt": 1,
            "success": False,
            "concise_error": "RuntimeError: bad",
        }
        self.assertEqual(record_event_id(record), record_event_id(dict(record)))

    def test_process_success_is_not_verified_success(self):
        result = analyze_execution("", "", 0)
        self.assertTrue(result["success"])
        self.assertEqual("process_passed", result["outcome"])
        self.assertFalse(result["verified_success"])

    def test_environment_failures_are_not_knowledge_eligible(self):
        samples = {
            "resource": "RuntimeError: Virtual memory allocation (1073741824 B) failed",
            "dependency": "ModuleNotFoundError: No module named 'LuisaRenderPy'",
            "timeout": "TimeoutExpired after 120s",
        }
        for expected, message in samples.items():
            with self.subTest(expected=expected):
                category = classify_failure("RuntimeError", message)
                self.assertEqual(expected, category)
                record = {
                    "success": False,
                    "error_type": "RuntimeError",
                    "concise_error": message,
                    "failure_category": category,
                }
                self.assertFalse(is_knowledge_eligible_failure(record))

    def test_generation_failure_has_explicit_outcome(self):
        outcome, category = classify_execution_result(
            {"success": False, "error_type": "GenerationError"},
            generation_failed=True,
        )
        self.assertEqual("generation_failed", outcome)
        self.assertEqual("generation", category)

    def test_timeout_preserves_partial_output(self):
        exc = subprocess.TimeoutExpired(
            cmd=["python", "code.py"], timeout=3,
            output="partial stdout", stderr="partial stderr",
        )
        with mock.patch.object(collector.subprocess, "run", side_effect=exc):
            result = collector.execute_code("code.py", timeout=3)
        self.assertEqual("timed_out", result["outcome"])
        self.assertEqual("partial stdout", result["stdout"])
        self.assertIn("partial stderr", result["concise_error"])

    def test_generation_failure_is_written_as_terminal_event(self):
        class FakeAgent:
            def __init__(self, rewrite_mode="hyde"):
                self.rewrite_mode = rewrite_mode

            def solve(self, query, save_code=False):
                raise RuntimeError("generation unavailable")

        fake_agent_module = types.ModuleType("agent")
        fake_agent_module.GenesisAgent = FakeAgent
        old_agent_module = sys.modules.get("agent")
        old_root = collector.RAG_DEMO_ROOT
        try:
            with tempfile.TemporaryDirectory() as tmp:
                sys.modules["agent"] = fake_agent_module
                collector.RAG_DEMO_ROOT = tmp
                prompts_path = os.path.join(tmp, "prompts.json")
                log_path = os.path.join(tmp, "logs", "events.jsonl")
                with open(prompts_path, "w", encoding="utf-8") as f:
                    json.dump([{"task_id": "task/unsafe", "query": "test query"}], f)

                collector.run(
                    prompts_file=prompts_path,
                    log_path=log_path,
                    max_prompts=1,
                    auto_process=False,
                    run_id="unit_test_run",
                )

                with open(log_path, "r", encoding="utf-8") as f:
                    record = json.loads(f.readline())
                self.assertEqual("generation_failed", record["outcome"])
                self.assertEqual("generation", record["failure_category"])
                self.assertEqual("task_unsafe", record["task_id"])
                self.assertTrue(record["event_id"].startswith("evt_"))
        finally:
            collector.RAG_DEMO_ROOT = old_root
            if old_agent_module is None:
                sys.modules.pop("agent", None)
            else:
                sys.modules["agent"] = old_agent_module

    def test_agent_init_failure_records_every_selected_prompt(self):
        class BrokenAgent:
            def __init__(self, rewrite_mode="hyde"):
                raise RuntimeError("init unavailable")

        fake_agent_module = types.ModuleType("agent")
        fake_agent_module.GenesisAgent = BrokenAgent
        old_agent_module = sys.modules.get("agent")
        old_root = collector.RAG_DEMO_ROOT
        try:
            with tempfile.TemporaryDirectory() as tmp:
                sys.modules["agent"] = fake_agent_module
                collector.RAG_DEMO_ROOT = tmp
                prompts_path = os.path.join(tmp, "prompts.json")
                log_path = os.path.join(tmp, "logs", "events.jsonl")
                with open(prompts_path, "w", encoding="utf-8") as f:
                    json.dump([
                        {"task_id": "one", "query": "query one"},
                        {"task_id": "two", "query": "query two"},
                    ], f)

                collector.run(
                    prompts_file=prompts_path,
                    log_path=log_path,
                    auto_process=False,
                    run_id="unit_test_init_failure",
                )

                with open(log_path, "r", encoding="utf-8") as f:
                    records = [json.loads(line) for line in f if line.strip()]
                self.assertEqual(2, len(records))
                self.assertTrue(all(r["outcome"] == "generation_failed" for r in records))
        finally:
            collector.RAG_DEMO_ROOT = old_root
            if old_agent_module is None:
                sys.modules.pop("agent", None)
            else:
                sys.modules["agent"] = old_agent_module


class CandidateRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_by_id, cls.known_ids, cls.class_ids = load_api_kb(processor.API_INDEX_FILE)

    def test_loop_c_uses_concise_error(self):
        record = {
            "event_id": "evt_box_vel",
            "task_id": "box_vel",
            "query": "Create a moving box",
            "attempt": 1,
            "success": False,
            "failure_category": "api_usage",
            "stdout": "",
            "stderr": "",
            "concise_error": (
                "Traceback (most recent call last):\n"
                "  File \"code.py\", line 4, in <module>\n"
                "    morph = gs.morphs.Box(size=(1, 1, 1), vel=(1, 0, 0))\n"
                "GenesisException: Unrecognized attribute: vel"
            ),
        }
        candidates = processor.collect_loop_c(
            [record], self.known_ids, self.class_ids, self.api_by_id, {"apis": []}
        )
        self.assertEqual(1, len(candidates))
        self.assertEqual("genesis.options.morphs.Box", candidates[0]["api_id"])
        self.assertIn("vel", candidates[0]["constraints"][0])

    def test_resource_failure_does_not_enter_loop_b(self):
        record = {
            "event_id": "evt_oom",
            "task_id": "oom",
            "query": "test",
            "attempt": 1,
            "success": False,
            "failure_category": "resource",
            "concise_error": "RuntimeError: Virtual memory allocation failed",
            "stderr": "RuntimeError: Virtual memory allocation failed",
            "code_path": "",
        }
        self.assertEqual([], processor.collect_loop_b([record], []))

    def test_pending_candidate_keeps_complete_unit(self):
        unit = {
            "unit_id": "verified_unit",
            "title": "Verified unit",
            "desc": "desc",
            "tags": ["rigid_body"],
            "all_apis": ["genesis.Scene"],
            "key_apis": [],
            "api_docs": [],
            "code": "print('ok')",
            "embedding_text": "embedding",
            "rerank_text": "rerank",
        }
        candidate = {
            "candidate_id": "cand_a_test",
            "type": "A",
            "source_id": "verified_unit",
            "query": "query",
            "all_apis": unit["all_apis"],
            "title": unit["title"],
            "desc": unit["desc"],
            "tags": unit["tags"],
            "code": unit["code"],
            "unit": unit,
        }
        old_dir = processor.LOOP_DIRS["A"]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                processor.LOOP_DIRS["A"] = tmp
                _, json_path = processor.generate_pending_review([candidate], "source.jsonl")
                self.assertIn(os.path.join("runs", "source"), json_path)
                with open(json_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)["candidates"][0]["unit"]
                self.assertEqual(set(unit), set(saved))
                self.assertEqual(unit["code"], saved["code"])
        finally:
            processor.LOOP_DIRS["A"] = old_dir

    def test_compact_run_label_preserves_online_run_kind(self):
        self.assertEqual(
            "online-full",
            processor._run_label("execution_log_online_authorized_20260712_full.jsonl"),
        )
        self.assertEqual("q100-p3", processor._run_label("execution_log_query100_part3.jsonl"))
        self.assertEqual("20260712-183541-850553", processor._run_timestamp("20260712_183541_850553"))

    def test_loop_summary_is_rebuilt_from_run_archives(self):
        old_dir = processor.LOOP_DIRS["C"]
        old_summary = processor.SUMMARY_FILES["C"]
        candidate = {
            "candidate_id": "cand_c_summary",
            "type": "C",
            "api_id": "genesis.options.morphs.Box",
            "constraints": ["Do not pass unsupported attributes."],
            "error_examples": ["Unrecognized attribute: vel"],
            "event_count": 1,
            "entry": {
                "api_id": "genesis.options.morphs.Box",
                "constraints": ["Do not pass unsupported attributes."],
                "error_examples": ["Unrecognized attribute: vel"],
                "event_count": 1,
                "sources": ["event_1"],
            },
        }
        try:
            with tempfile.TemporaryDirectory() as tmp:
                processor.LOOP_DIRS["C"] = os.path.join(tmp, "loop_c")
                processor.SUMMARY_FILES["C"] = os.path.join(tmp, "loop_c_summary.json")
                processor.generate_pending_review([candidate], "sample.jsonl")
                processor.refresh_loop_summary("C")
                with open(processor.SUMMARY_FILES["C"], "r", encoding="utf-8") as f:
                    summary = json.load(f)
                self.assertEqual(1, summary["run_count"])
                self.assertEqual(1, summary["candidate_count"])
                self.assertEqual("C", summary["candidates"][0]["candidate"]["type"])
        finally:
            processor.LOOP_DIRS["C"] = old_dir
            processor.SUMMARY_FILES["C"] = old_summary

    def test_incomplete_a_candidate_is_rejected(self):
        errors = processor._validate_candidate(
            {"type": "A", "unit": {"unit_id": "broken"}}, self.known_ids
        )
        self.assertTrue(any("missing fields" in error for error in errors))

    def test_unknown_c_api_is_rejected(self):
        candidate = {
            "type": "C",
            "api_id": "genesis.does.not.exist",
            "constraints": ["Do not use this."],
            "entry": {"api_id": "genesis.does.not.exist"},
        }
        errors = processor._validate_candidate(candidate, self.known_ids)
        self.assertTrue(any("unknown api_id" in error for error in errors))

    def test_c_entry_constraints_must_match_reviewed_constraints(self):
        api_id = "genesis.options.morphs.Box"
        candidate = {
            "type": "C",
            "api_id": api_id,
            "constraints": ["Reviewed constraint."],
            "entry": {"api_id": api_id, "constraints": ["Different constraint."]},
        }
        errors = processor._validate_candidate(candidate, self.known_ids)
        self.assertTrue(any("entry.constraints" in error for error in errors))


class PersistenceTests(unittest.TestCase):
    def test_progress_uses_event_ids(self):
        old_progress = processor.PROGRESS_FILE
        try:
            with tempfile.TemporaryDirectory() as tmp:
                processor.PROGRESS_FILE = os.path.join(tmp, "progress.json")
                log_path = os.path.join(tmp, "events.jsonl")
                records = [
                    {"event_id": "evt_1", "task_id": "one", "success": True},
                    {"event_id": "evt_2", "task_id": "two", "success": False},
                ]
                with open(log_path, "w", encoding="utf-8") as f:
                    for record in records:
                        f.write(json.dumps(record) + "\n")

                new_records, all_records, offset, _ = processor._get_new_records(log_path)
                self.assertEqual(2, len(new_records))
                processor._update_progress(log_path, offset, {}, processed_records=all_records)
                new_records, _, _, has_progress = processor._get_new_records(log_path)
                self.assertEqual([], new_records)
                self.assertTrue(has_progress)

                replay_records, _, _, replay_has_progress = processor._get_new_records(
                    log_path, reprocess=True
                )
                self.assertEqual(2, len(replay_records))
                self.assertFalse(replay_has_progress)
        finally:
            processor.PROGRESS_FILE = old_progress

    def test_atomic_save_retains_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "data.json")
            save_json(path, {"version": 1})
            save_json(path, {"version": 2}, backup=True)
            with open(path, "r", encoding="utf-8") as f:
                self.assertEqual(2, json.load(f)["version"])
            with open(f"{path}.bak", "r", encoding="utf-8") as f:
                self.assertEqual(1, json.load(f)["version"])


if __name__ == "__main__":
    unittest.main()
