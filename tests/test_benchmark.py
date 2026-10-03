"""Synthetic fixtures live only in temporary directories; these are not measurements."""
import contextlib
import csv
import io
import json
import os
from pathlib import Path
import random
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import benchmark as b


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(b, 'ROOT', self.root)
        self.deps_patch = patch.object(b, 'DEPS', self.root / '.deps')
        self.root_patch.start()
        self.deps_patch.start()
        self.env_patch = patch.dict(os.environ, {}, clear=True)
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.deps_patch.stop()
        self.root_patch.stop()
        self.temp.cleanup()

    def raw(self, outcomes):
        raw = self.root / 'raw'
        raw.mkdir()
        tasks = []
        for i, outcome in enumerate(outcomes):
            task = f'python/exercises/practice/task-{i}'
            tasks.append(task)
            path = raw / 'aider' / task
            path.mkdir(parents=True)
            if outcome is not None:
                b.write_json(path / '.aider.results.json', outcome)
        b.write_json(raw / 'tasks.json', tasks)
        return raw

    def test_complete_and_retry_outcomes(self):
        raw = self.raw([{'tests_outcomes': [False, True]}, {'tests_outcomes': [False, False]}])
        for task in json.loads((raw / 'tasks.json').read_text()):
            b.write_json(raw / 'aider' / task / '.benchmark.timing.json', {'wall_time_sec': 4})
        result = b.analyze(raw, {'result': {'total_time_sec': 12}})
        self.assertEqual((result['passed'], result['failed'], result['pass_rate']), (1, 1, .5))
        self.assertEqual(result['avg_time_sec'], 4)
        self.assertEqual(result['total_time_sec'], 12)

    def test_missing_exception_empty_and_nonboolean_are_unknown(self):
        raw = self.raw([{'tests_outcomes': [True]}, None, {'exception': 'test fixture'},
                        {'tests_outcomes': []}, {'tests_outcomes': ['false']},
                        {'tests_outcomes': [1]}, ['unexpected']])
        result = b.analyze(raw, {})
        self.assertEqual(result['completed_tasks'], 1)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(result['unknown_tasks'], 6)
        self.assertIsNone(result['pass_rate'])
        self.assertIsNone(result['per_language']['python']['pass_rate'])
        self.assertIsNone(result['avg_time_sec'])

    def test_truncated_json_does_not_become_failure(self):
        raw = self.raw([{'tests_outcomes': [True]}])
        next(raw.rglob('.aider.results.json')).write_text('{')
        self.assertEqual(b.analyze(raw, {})['unknown_tasks'], 1)

    def test_aider_duration_is_not_task_wall_time(self):
        result = b.analyze(self.raw([{'tests_outcomes': [True], 'duration': 7}]), {})
        self.assertIsNone(result['avg_time_sec'])
        self.assertEqual(result['tasks'][0]['aider_duration_sec'], 7)

    def test_missing_stats_are_null(self):
        result = b.analyze(self.raw([None]), {})
        for key in ('peak_memory_mb', 'peak_swap_mb', 'battery_drop', 'tokens_per_sec'):
            self.assertIsNone(result[key])

    def test_sampled_peaks_and_ac_battery(self):
        raw = self.raw([None])
        (raw / 'stats.csv').write_text('memory_used_mb,swap_used_mb,power_source\n100,0,Battery Power\n150,2,AC Power\nnan,,Battery Power\n')
        meta = {'observations': {'before': {'battery_percent': 90, 'power_source': 'Battery Power'},
                                 'after': {'battery_percent': 87, 'power_source': 'Battery Power'}}}
        result = b.analyze(raw, meta)
        self.assertEqual(result['peak_memory_mb'], 150)
        self.assertEqual(result['peak_swap_mb'], 2)
        self.assertIsNone(result['battery_drop'])

    def test_defaults_env_precedence_and_no_execution(self):
        (self.root / 'configs').mkdir()
        (self.root / 'configs/benchmark.env').write_text('BENCHMARK_TEST_COUNT=10\nRUN_LABEL=trial\n')
        with patch.dict(os.environ, {'BENCHMARK_TEST_COUNT': '3'}):
            self.assertEqual(b.config()['BENCHMARK_TEST_COUNT'], '3')
        (self.root / 'configs/benchmark.env').write_text('MODEL_NAME=$(touch injected)\n')
        with self.assertRaises(ValueError):
            b.config()
        self.assertFalse((self.root / 'injected').exists())

    def test_reject_implicit_full_runs_and_credential_urls(self):
        for value in ('0', '-1', 'many'):
            with patch.dict(os.environ, {'BENCHMARK_TEST_COUNT': value}):
                with self.assertRaises(ValueError):
                    b.config()
        with patch.dict(os.environ, {'OLLAMA_BASE_URL': 'http://secret@localhost:11434'}):
            with self.assertRaises(ValueError):
                b.config()

    def test_manifest_replay_and_validation(self):
        for n in range(5):
            p = b.DEPS / f'polyglot-benchmark/python/exercises/practice/t{n}/.meta'
            p.mkdir(parents=True)
            (p / 'config.json').write_text('{}')
        cfg = b.config()
        selected = b.select_tasks(cfg)
        self.assertEqual(len(selected), 3)
        self.assertEqual(selected, b.select_tasks(cfg))
        b.write_json(self.root / 'tasks.json', selected[::-1])
        cfg['TASK_MANIFEST'] = 'tasks.json'
        self.assertEqual(b.select_tasks(cfg), selected[::-1])
        b.write_json(self.root / 'tasks.json', ['../../outside'] * 3)
        with self.assertRaises(ValueError):
            b.select_tasks(cfg)

    def test_native_stats_units(self):
        def fake(args, **kwargs):
            return {'vm_stat': 'Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages active: 10.\nPages inactive: 20.\nPages wired down: 30.\nPages occupied by compressor: 4.\n',
                    'sysctl': 'total = 1024.00M used = 1.50G free = 0M',
                    'top': 'CPU usage: 3.00% user, 2.00% sys, 95.00% idle',
                    'pmset': "Now drawing from 'Battery Power'\n -InternalBattery-0 88%; discharging; 3:12 remaining"}[args[0]]
        with patch.object(b.platform, 'system', return_value='Darwin'), patch.object(b, 'command', side_effect=fake):
            stats = b.stats_sample()
        self.assertEqual(stats['memory_used_mb'], 1)
        self.assertEqual(stats['swap_used_mb'], 1536)
        self.assertEqual(stats['cpu_percent'], 5)
        self.assertEqual(stats['battery_percent'], 88)

    def test_metadata_does_not_request_serial_or_user_info(self):
        calls = []
        with patch.object(b, 'command', side_effect=lambda args, **kw: calls.append(args)), patch.object(b, 'pins', return_value={}):
            info = b.system_info()
        text = repr(calls).lower()
        for prohibited in ('system_profiler', 'serial', 'uuid', 'whoami', 'home'):
            self.assertNotIn(prohibited, text)
        self.assertIsNone(info['physical_memory_bytes'])

    def test_empty_summary_has_only_header(self):
        with contextlib.redirect_stdout(io.StringIO()):
            b.summarize()
        with (self.root / 'results/summary/results.csv').open() as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows, [b.SUMMARY_FIELDS])

    def test_run_lifecycle_without_real_docker_or_model(self):
        source = Path(b.__file__).parent / 'container-entry.py'
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/container-entry.py').write_text(source.read_text())
        (self.root / 'metadata/runs').mkdir(parents=True)
        cfg = b.config()
        cfg['MODEL_NAME'] = 'fixture:tag'
        tasks = [f'python/exercises/practice/t{n}' for n in range(3)]
        invocation = []
        def fake_call(args, **kwargs):
            invocation.extend(args)
            raw = next((self.root / 'results/raw').iterdir())
            self.assertFalse((raw / 'aider').exists(), 'Upstream must create/copy the exercise destination')
            for task in tasks:
                p = raw / 'aider' / task
                p.mkdir(parents=True)
                b.write_json(p / '.aider.results.json', {'tests_outcomes': [True]})
            return 0
        with contextlib.ExitStack() as stack:
            for name, value in [('doctor', 0), ('model_info', {'name': 'fixture:tag', 'digest': 'fixture-digest'}),
                                ('select_tasks', tasks), ('system_info', {}), ('pins', {}),
                                ('image_info', {'Id': 'sha256:fixture', 'Architecture': 'arm64'}),
                                ('api', {'version': 'fixture'}), ('command', '{}'), ('stats_sample', {})]:
                stack.enter_context(patch.object(b, name, return_value=value))
            stack.enter_context(patch.object(b.subprocess, 'run'))
            stack.enter_context(patch.object(b.subprocess, 'call', side_effect=fake_call))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            self.assertEqual(b.run(cfg), 0)
        meta = json.loads(next((self.root / 'metadata/runs').glob('*.json')).read_text())
        self.assertEqual(meta['result']['status'], 'completed')
        self.assertEqual(meta['result']['pass_rate'], 1)
        self.assertIn('--cap-drop=ALL', invocation)
        self.assertIn('sha256:fixture', invocation)
        self.assertNotIn('/var/run/docker.sock', ' '.join(invocation))
        self.assertEqual(invocation[invocation.index('--num-tests') + 1], '3')

    def test_container_adapter_refuses_host_execution(self):
        source = Path(b.__file__).parent / 'container-entry.py'
        with patch.object(Path, 'exists', return_value=False):
            with self.assertRaises(SystemExit):
                runpy.run_path(str(source))

    def test_adapter_replays_order_and_records_task_wall_time(self):
        # Exercise the actual adapter against a tiny harness, without importing Aider.
        source = (Path(b.__file__).parent / 'container-entry.py').read_text()
        task = 'python/exercises/practice/chosen'
        ns = {'random': random, 'Path': Path, 'destination': self.root, 'seen': []}
        exec('def run_test(original, testdir):\n'
             '    testdir.mkdir(parents=True)\n'
             '    seen.append(str(testdir.relative_to(destination)))\n'
             'def main():\n'
             '    items = ["python/exercises/practice/other", "python/exercises/practice/chosen"]\n'
             '    random.shuffle(items)\n'
             '    for item in items: run_test(None, destination / item)\n'
             'app = main\n', ns)
        read_text = Path.read_text
        def fake_read(path, *args, **kwargs):
            return json.dumps([task]) if str(path) == '/run-data/tasks.json' else read_text(path, *args, **kwargs)
        original_shuffle = random.shuffle
        original_path = sys.path[:]
        original_argv = sys.argv[:]
        try:
            with patch.dict(os.environ, {'AIDER_DOCKER': '1'}), patch.object(Path, 'exists', return_value=True), \
                    patch.object(Path, 'read_text', fake_read), patch.object(os, 'chdir'), \
                    patch.object(runpy, 'run_path', return_value=ns):
                exec(compile(source, 'container-entry.py', 'exec'), {})
        finally:
            random.shuffle = original_shuffle
            sys.path[:] = original_path
            sys.argv[:] = original_argv
        self.assertEqual(ns['seen'], [task])
        timing = json.loads((self.root / task / '.benchmark.timing.json').read_text())
        self.assertGreaterEqual(timing['wall_time_sec'], 0)


if __name__ == '__main__':
    unittest.main()
