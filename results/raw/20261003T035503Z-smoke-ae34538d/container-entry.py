#!/usr/bin/env python3
"""Execute the pinned upstream harness with an explicit task order, inside Docker."""
import json
import os
from pathlib import Path
import random
import runpy
import sys
import time

if not Path('/.dockerenv').exists() or os.environ.get('AIDER_DOCKER') != '1':
    raise SystemExit('This adapter must only run inside Docker.')

tasks = json.loads(Path('/run-data/tasks.json').read_text())
original_shuffle = random.shuffle


def ordered_tasks(items):
    # Intercept only the harness exercise list, not randomness in libraries.
    if items and all(isinstance(x, str) and '/exercises/practice/' in x for x in items):
        if not set(tasks).issubset(items):
            raise RuntimeError('Saved task manifest differs from available exercises')
        items[:] = tasks
    else:
        original_shuffle(items)


random.shuffle = ordered_tasks
os.chdir('/aider')
sys.path.insert(0, '/aider/benchmark')
sys.argv = ['/aider/benchmark/benchmark.py'] + sys.argv[1:]
namespace = runpy.run_path('/aider/benchmark/benchmark.py', run_name='benchmark_adapter')
upstream_run_test = namespace['run_test']


def timed_test(*args, **kwargs):
    started = time.monotonic()
    try:
        return upstream_run_test(*args, **kwargs)
    finally:
        testdir = Path(args[1])
        if testdir.is_dir():
            (testdir / '.benchmark.timing.json').write_text(json.dumps({
                'wall_time_sec': time.monotonic() - started,
            }))


namespace['main'].__globals__['run_test'] = timed_test
namespace['app']()
