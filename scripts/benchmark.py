#!/usr/bin/env python3
"""Host orchestration and read-only result analysis; Python standard library only."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from urllib.parse import urlsplit
import uuid

ROOT = Path(__file__).resolve().parent.parent
DEPS = ROOT / '.deps'
DEFAULTS = {
    'MODEL_NAME': '', 'OLLAMA_BASE_URL': 'http://127.0.0.1:11434',
    'OLLAMA_DOCKER_BASE_URL': 'http://host.docker.internal:11434',
    'BENCHMARK_TEST_COUNT': '3', 'BENCHMARK_THREADS': '1', 'BENCHMARK_SEED': '0',
    'BENCHMARK_TRIES': '2', 'MODEL_NUM_CTX': '8192', 'MODEL_TEMPERATURE': '0',
    'EDIT_FORMAT': 'whole', 'RUN_LABEL': 'smoke', 'STATS_INTERVAL_SEC': '5',
    'DOCKER_IMAGE': 'local-llm-aider-benchmark:pinned', 'DOCKER_MEMORY': '6g',
    'DOCKER_CPUS': '4', 'TASK_MANIFEST': '',
}
STATS_FIELDS = ['timestamp', 'cpu_percent', 'load_1m', 'memory_used_mb',
                'swap_used_mb', 'battery_percent', 'battery_state', 'power_source']
SUMMARY_FIELDS = ['run_id', 'timestamp', 'model', 'benchmark', 'task_count',
                  'passed', 'failed', 'pass_rate', 'total_time_sec', 'avg_time_sec',
                  'peak_memory_mb', 'peak_swap_mb', 'battery_start', 'battery_end',
                  'battery_drop', 'completed_tasks', 'unknown_tasks', 'status']


def now():
    return datetime.now(timezone.utc).isoformat()


def command(args, timeout=20):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def config():
    cfg = dict(DEFAULTS)
    path = Path(os.environ.get('BENCHMARK_CONFIG', str(ROOT / 'configs/benchmark.env')))
    if path.exists():
        for n, line in enumerate(path.read_text().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, sep, value = line.partition('=')
            key, value = key.strip(), value.strip()
            if not sep or key not in DEFAULTS:
                raise ValueError(f'Unknown configuration key on line {n}')
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            cfg[key] = value
    cfg.update({k: os.environ[k] for k in cfg if k in os.environ})
    for key in ('BENCHMARK_TEST_COUNT', 'BENCHMARK_THREADS', 'BENCHMARK_TRIES', 'MODEL_NUM_CTX'):
        if int(cfg[key]) < 1:
            raise ValueError(f'{key} must be a positive integer (no implicit full runs)')
    int(cfg['BENCHMARK_SEED'])
    for key in ('STATS_INTERVAL_SEC', 'DOCKER_CPUS'):
        if not math.isfinite(float(cfg[key])) or float(cfg[key]) <= 0:
            raise ValueError(f'{key} must be finite and positive')
    if cfg['MODEL_TEMPERATURE'] != '0':
        raise ValueError('This methodology requires MODEL_TEMPERATURE=0')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}', cfg['RUN_LABEL']):
        raise ValueError('RUN_LABEL must contain 1–48 letters, digits, _ or -')
    if cfg['EDIT_FORMAT'] not in ('whole', 'diff', 'diff-fenced', 'udiff'):
        raise ValueError('Unsupported EDIT_FORMAT; single-model editing only')
    if cfg['MODEL_NAME'] and (not re.fullmatch(r'[A-Za-z0-9_.:/-]+', cfg['MODEL_NAME'])
                              or cfg['MODEL_NAME'].startswith(('ollama/', 'ollama_chat/'))):
        raise ValueError('MODEL_NAME must be the native Ollama identifier, without provider prefix')
    if not re.fullmatch(r'[1-9][0-9]*[mgMG]', cfg['DOCKER_MEMORY']):
        raise ValueError('DOCKER_MEMORY must be a positive integer followed by m or g')
    for key, allowed in [('OLLAMA_BASE_URL', {'127.0.0.1', 'localhost', '::1'}),
                         ('OLLAMA_DOCKER_BASE_URL', {'host.docker.internal'})]:
        url = urlsplit(cfg[key])
        if (url.scheme != 'http' or url.hostname not in allowed or url.username or
                url.password or url.path not in ('', '/') or url.query or url.fragment):
            raise ValueError(f'{key} must be a local HTTP endpoint without credentials or path')
        cfg[key] = cfg[key].rstrip('/')
    return cfg


def api(cfg, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(cfg['OLLAMA_BASE_URL'] + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    # Local endpoints must not pass through a configured external proxy.
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=10) as r:
        return json.load(r)


def pins():
    return json.loads((ROOT / 'configs/dependencies.json').read_text())


def git_info(path):
    if not (path / '.git').exists():
        return {'commit': None, 'dirty': None}
    state = command(['git', '-C', str(path), 'status', '--porcelain'])
    return {'commit': command(['git', '-C', str(path), 'rev-parse', 'HEAD']),
            'dirty': bool(state) if state is not None else None}


def system_info():
    mac = platform.system() == 'Darwin'
    def sysctl(name):
        return command(['sysctl', '-n', name]) if mac else None
    memory = sysctl('hw.memsize')
    return {
        'timestamp': now(), 'hostname': platform.node(),
        'macos_version': command(['sw_vers', '-productVersion']) if mac else None,
        'macos_build': command(['sw_vers', '-buildVersion']) if mac else None,
        'darwin_version': platform.release() if mac else None,
        'os': platform.system(), 'architecture': platform.machine(),
        'chip': sysctl('machdep.cpu.brand_string'),
        'physical_memory_bytes': int(memory) if memory and memory.isdigit() else None,
        'hardware_model': sysctl('hw.model'),
        'ollama_version': command(['ollama', '--version']),
        'docker_version': command(['docker', '--version']),
        'docker_server_version': command(['docker', 'version', '--format', '{{.Server.Version}}']),
        'git_version': command(['git', '--version']), 'python_version': platform.python_version(),
        'repo': git_info(ROOT),
        'dependencies': {name: git_info(DEPS / name) for name in pins()},
    }


def model_info(cfg):
    name = cfg['MODEL_NAME']
    models = api(cfg, '/api/tags').get('models', [])
    names = {name, name + ':latest'} if ':' not in name.split('/')[-1] else {name}
    found = next((m for m in models if m.get('name') in names), None)
    if not found:
        raise ValueError('Configured model is not installed; pull your chosen model manually')
    detail = api(cfg, '/api/show', {'model': found['name']})
    if detail.get('remote_model') or detail.get('remote_host') or found.get('remote_model'):
        raise ValueError('Cloud/remote models are outside this local benchmark scope')
    if not found.get('digest'):
        raise ValueError('Ollama did not return a model digest')
    return {key: found.get(key) for key in ('name', 'digest', 'size', 'modified_at', 'details')} | {
        # Never store Modelfile: it may disclose local weight paths.
        'parameters': detail.get('parameters'), 'model_info': detail.get('model_info'),
        'template_sha256': hashlib.sha256(detail.get('template', '').encode()).hexdigest(),
    }


def image_info(cfg):
    raw = command(['docker', 'image', 'inspect', cfg['DOCKER_IMAGE']])
    return json.loads(raw)[0] if raw else None


def doctor(cfg):
    failures = 0
    def check(ok, label, warning=False):
        nonlocal failures
        print(f"[{'OK' if ok else 'WARN' if warning else 'FAIL'}] {label}")
        failures += int(not ok and not warning)
    check(platform.system() == 'Darwin', 'macOS')
    check(platform.machine() == 'arm64', 'Apple Silicon (native arm64 Python)')
    for exe in ('git', 'docker', 'ollama', 'python3'):
        check(bool(shutil.which(exe)), exe)
    check(command(['docker', 'info', '--format', '{{.ServerVersion}}']) is not None, 'Docker daemon')
    try:
        api(cfg, '/api/version')
        check(True, 'Ollama API')
        if cfg['MODEL_NAME']:
            model_info(cfg)
            check(True, 'Model installed and digest available')
        else:
            check(False, 'MODEL_NAME is empty', warning=True)
    except (OSError, ValueError):
        check(False, 'Ollama API / model availability')
    for name, pin in pins().items():
        info = git_info(DEPS / name)
        check(info['commit'] == pin['commit'] and info['dirty'] is False,
              f'{name}: clean checkout at pinned commit (make setup)')
    check((DEPS / 'aider/benchmark/benchmark.py').is_file(), 'Aider benchmark harness')
    check(bool(list((DEPS / 'polyglot-benchmark').glob('*/exercises/practice/*/.meta/config.json'))),
          'Polyglot exercises')
    img = image_info(cfg)
    check(bool(img and img.get('Config', {}).get('Labels', {}).get('benchmark.aider.commit') ==
               pins()['aider']['commit']), 'Pinned Docker image (make build-image)')
    check(bool(img and img.get('Architecture') == 'arm64'), 'Docker image architecture: arm64')
    for part in ('results/raw', 'results/summary', 'metadata/runs', 'logs'):
        try:
            path = ROOT / part
            path.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=path):
                pass
            check(True, f'Writable {part}')
        except OSError:
            check(False, f'Writable {part}')
    return int(failures > 0)


def setup():
    for exe in ('git', 'python3', 'docker', 'ollama'):
        print(f"[{'OK' if shutil.which(exe) else 'WARN'}] {exe}")
    if not shutil.which('git'):
        raise ValueError('Install Git before setup')
    for part in ('.deps', 'results/raw', 'results/summary', 'logs', 'metadata/runs'):
        (ROOT / part).mkdir(parents=True, exist_ok=True)
    for name, pin in pins().items():
        path = DEPS / name
        if not path.exists():
            print(f"Cloning source dependency {name} at {pin['commit']}", flush=True)
            subprocess.run(['git', 'clone', '--no-checkout', pin['url'], str(path)], check=True)
            subprocess.run(['git', '-C', str(path), 'checkout', '--detach', pin['commit']], check=True)
        info = git_info(path)
        if info['commit'] != pin['commit'] or info['dirty'] is not False:
            raise ValueError(f'{name} is not a clean pinned checkout; inspect it manually')
    print('Source setup complete. Configure configs/benchmark.env, start Docker and Ollama,')
    print('then explicitly run make build-image (large download/build) and make doctor.')
    print('No models were downloaded; no benchmark was started.')


def build_image(cfg):
    info = git_info(DEPS / 'aider')
    sha = pins()['aider']['commit']
    if info['commit'] != sha or info['dirty'] is not False:
        raise ValueError('Run make setup first; image requires a clean pinned Aider checkout')
    print('Building upstream language toolchains and Aider dependencies; this can be large.', flush=True)
    subprocess.run(['docker', 'build', '--platform', 'linux/arm64', '--label',
                    f'benchmark.aider.commit={sha}', '-t', cfg['DOCKER_IMAGE'],
                    '-f', str(DEPS / 'aider/benchmark/Dockerfile'), str(DEPS / 'aider')], check=True)


def stats_sample():
    row = dict.fromkeys(STATS_FIELDS)
    row['timestamp'] = now()
    row['load_1m'] = os.getloadavg()[0]
    if platform.system() != 'Darwin':
        return row
    vm = command(['vm_stat'], timeout=5) or ''
    page_match = re.search(r'page size of (\d+) bytes', vm)
    pages = {k.strip(): int(v) for k, v in re.findall(r'^([^:\n]+):\s+(\d+)\.', vm, re.M)}
    needed = ('Pages active', 'Pages inactive', 'Pages wired down', 'Pages occupied by compressor')
    if page_match and all(k in pages for k in needed):
        row['memory_used_mb'] = sum(pages[k] for k in needed) * int(page_match[1]) / 2**20
    swap = command(['sysctl', '-n', 'vm.swapusage'], timeout=5) or ''
    match = re.search(r'used\s*=\s*([\d.]+)([KMG])', swap)
    if match:
        row['swap_used_mb'] = float(match[1]) * {'K': 1/1024, 'M': 1, 'G': 1024}[match[2]]
    top = command(['top', '-l', '1', '-n', '0'], timeout=5) or ''
    match = re.search(r'CPU usage:.*?([\d.]+)% idle', top)
    if match:
        row['cpu_percent'] = 100 - float(match[1])
    battery = command(['pmset', '-g', 'batt'], timeout=5) or ''
    match = re.search(r'(\d+)%;\s*([^;\n]+)', battery)
    if match:
        row['battery_percent'], row['battery_state'] = int(match[1]), match[2].strip()
    match = re.search(r"Now drawing from '([^']+)'", battery)
    if match:
        row['power_source'] = match[1]
    return row


def collect_stats(path, interval, stop=None):
    stop = stop or threading.Event()
    with Path(path).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=STATS_FIELDS)
        writer.writeheader()
        while not stop.is_set():
            writer.writerow(stats_sample())
            f.flush()
            stop.wait(interval)


def select_tasks(cfg):
    available = sorted(str(p.parent.parent.relative_to(DEPS / 'polyglot-benchmark'))
                       for p in (DEPS / 'polyglot-benchmark').glob('*/exercises/practice/*/.meta/config.json'))
    count = int(cfg['BENCHMARK_TEST_COUNT'])
    if cfg['TASK_MANIFEST']:
        path = Path(cfg['TASK_MANIFEST'])
        tasks = json.loads((path if path.is_absolute() else ROOT / path).read_text())
        if (not isinstance(tasks, list) or not all(isinstance(t, str) for t in tasks) or
                len(tasks) != count or len(set(tasks)) != count or not set(tasks).issubset(available)):
            raise ValueError('TASK_MANIFEST must contain exactly TEST_COUNT unique available task paths')
        return tasks
    if count > len(available):
        raise ValueError(f'Requested {count} tasks, but only {len(available)} are available')
    random.Random(int(cfg['BENCHMARK_SEED'])).shuffle(available)
    return available[:count]


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def analyze(raw, meta):
    """Score only explicit boolean test outcomes; missing/exception records are unknown."""
    tasks = json.loads((raw / 'tasks.json').read_text())
    rows = []
    for task in tasks:
        record = {}
        path = raw / 'aider' / task / '.aider.results.json'
        try:
            record = json.loads(path.read_text())
            if not isinstance(record, dict):
                record = {}
        except (OSError, ValueError):
            pass
        outcomes = record.get('tests_outcomes')
        valid = (isinstance(outcomes, list) and bool(outcomes) and
                 all(type(x) is bool for x in outcomes) and not record.get('exception'))
        duration = None
        try:
            duration = json.loads((path.parent / '.benchmark.timing.json').read_text()).get('wall_time_sec')
        except (OSError, ValueError, AttributeError):
            pass
        aider_duration = record.get('duration')
        rows.append({'task': task, 'language': task.split('/')[0],
                     'passed': outcomes[-1] if valid else None,
                     'duration_sec': duration if number(duration) and duration >= 0 else None,
                     'aider_duration_sec': aider_duration if number(aider_duration) and aider_duration >= 0 else None})
    passed = sum(r['passed'] is True for r in rows)
    failed = sum(r['passed'] is False for r in rows)
    completed = passed + failed
    durations = [r['duration_sec'] for r in rows if r['duration_sec'] is not None]
    samples = []
    if (raw / 'stats.csv').exists():
        with (raw / 'stats.csv').open() as f:
            samples = list(csv.DictReader(f))
    def peak(field):
        values = []
        for r in samples:
            try:
                val = float(r[field])
                if math.isfinite(val):
                    values.append(val)
            except (KeyError, TypeError, ValueError):
                pass
        return max(values) if values else None
    before = meta.get('observations', {}).get('before', {})
    after = meta.get('observations', {}).get('after', {})
    start, end = before.get('battery_percent'), after.get('battery_percent')
    battery_only = (before.get('power_source') == after.get('power_source') == 'Battery Power'
                    and all(s.get('power_source') == 'Battery Power' for s in samples))
    by_language = {}
    for language in sorted({r['language'] for r in rows}):
        subset = [r for r in rows if r['language'] == language]
        done = [r for r in subset if r['passed'] is not None]
        wins = sum(r['passed'] is True for r in done)
        by_language[language] = {'task_count': len(subset), 'completed': len(done),
                                 'passed': wins, 'failed': len(done) - wins,
                                 'pass_rate': wins / len(subset) if len(done) == len(subset) else None}
    result = {
        'task_count': len(tasks), 'passed': passed, 'failed': failed,
        'completed_tasks': completed, 'unknown_tasks': len(tasks) - completed,
        'pass_rate': passed / len(tasks) if tasks and completed == len(tasks) else None,
        'total_time_sec': meta.get('result', {}).get('total_time_sec'),
        'avg_time_sec': sum(durations) / len(rows) if rows and len(durations) == len(rows) else None,
        'peak_memory_mb': peak('memory_used_mb'), 'peak_swap_mb': peak('swap_used_mb'),
        'battery_start': start, 'battery_end': end,
        'battery_drop': start - end if battery_only and number(start) and number(end) else None,
        'per_language': by_language, 'tasks': rows,
        'tokens_per_sec': None, 'temperature_celsius': None, 'power_watts': None,
    }
    return result


def summarize():
    out = ROOT / 'results/summary'
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted((ROOT / 'metadata/runs').glob('*.json')):
        meta = json.loads(path.read_text())
        if meta.get('schema_version') != 1 or meta.get('benchmark', {}).get('name') != 'aider-polyglot':
            print(f'[WARN] Unsupported schema/benchmark: {path.name}', file=sys.stderr)
            continue
        run_id = meta['run_id']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', run_id):
            raise ValueError('Invalid run ID in metadata')
        raw = ROOT / 'results/raw' / run_id
        result = analyze(raw, meta)
        write_json(out / f'{run_id}.json', result)
        row = {key: result.get(key) for key in SUMMARY_FIELDS}
        row.update(run_id=run_id, timestamp=meta['timestamp'], model=meta['model'].get('name'),
                   benchmark='aider-polyglot', status=meta['result'].get('status'))
        rows.append(row)
    with (out / 'results.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Summarized {len(rows)} recorded runs into results/summary/results.csv')


def run(cfg):
    if doctor(cfg):
        raise ValueError('Preflight failed; resolve [FAIL] checks before running')
    if not cfg['MODEL_NAME']:
        raise ValueError('Set MODEL_NAME to an installed Ollama identifier')
    model = model_info(cfg)
    cfg = dict(cfg, MODEL_NAME=model['name'])
    tasks = select_tasks(cfg)
    machine = system_info()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + cfg['RUN_LABEL'] + '-' + uuid.uuid4().hex[:8]
    raw = ROOT / 'results/raw' / run_id
    raw.mkdir(parents=True, exist_ok=False)
    # Upstream copies exercises only if the destination does not yet exist.
    for filename in ('stdout.log', 'stderr.log'):
        (raw / filename).touch()
    write_json(raw / 'tasks.json', tasks)
    saved_cfg = dict(cfg, TASK_MANIFEST='tasks.json')
    write_json(raw / 'configuration.json', saved_cfg)
    settings = [{'name': 'ollama_chat/' + model['name'], 'weak_model_name': 'ollama_chat/' + model['name'],
                 'use_repo_map': False, 'extra_params': {'temperature': 0, 'num_ctx': int(cfg['MODEL_NUM_CTX'])}}]
    # JSON is a YAML subset accepted by upstream's YAML model-settings loader.
    write_json(raw / 'model-settings.yml', settings)
    image = image_info(cfg)
    meta = {'schema_version': 1, 'run_id': run_id, 'timestamp': now(), 'machine': machine,
            'runtime': {'name': 'ollama', 'version': api(cfg, '/api/version').get('version'),
                        'docker_image_id': image['Id'], 'docker_image_digests': image.get('RepoDigests'),
                        'docker_architecture': image.get('Architecture'),
                        'docker_vm': command(['docker', 'info', '--format', '{{json .}}'])},
            'model': model, 'benchmark': {'name': 'aider-polyglot', 'dependencies': pins()},
            'configuration': saved_cfg, 'observations': {}, 'result': {'status': 'preparing'},
            'unsupported_metrics': ['tokens_per_sec', 'temperature_celsius', 'power_watts']}
    # Docker info contains machine names/paths: retain only resource allocation.
    docker_vm = json.loads(meta['runtime']['docker_vm'] or '{}')
    meta['runtime']['docker_vm'] = {k: docker_vm.get(k) for k in ('NCPU', 'MemTotal', 'ServerVersion', 'Architecture')}
    meta['benchmark']['adapter_sha256'] = hashlib.sha256((ROOT / 'scripts/container-entry.py').read_bytes()).hexdigest()
    shutil.copyfile(ROOT / 'scripts/container-entry.py', raw / 'container-entry.py')
    metadata_path = ROOT / 'metadata/runs' / (run_id + '.json')
    write_json(metadata_path, meta)
    container = 'llm-bench-' + uuid.uuid4().hex[:12]
    args = ['docker', 'run', '--rm', '--name', container, '--platform', 'linux/arm64',
            '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=512',
            '--memory=' + cfg['DOCKER_MEMORY'], '--memory-swap=' + cfg['DOCKER_MEMORY'],
            '--cpus=' + cfg['DOCKER_CPUS'], '--add-host=host.docker.internal:host-gateway',
            '--mount', f'type=bind,source={raw},target=/run-data',
            '--mount', f'type=bind,source={raw / "tasks.json"},target=/run-data/tasks.json,readonly',
            '--mount', f'type=bind,source={raw / "model-settings.yml"},target=/run-data/model-settings.yml,readonly',
            '--mount', f'type=bind,source={raw / "container-entry.py"},target=/run-data/container-entry.py,readonly',
            '--mount', f'type=bind,source={DEPS / "polyglot-benchmark"},target=/exercises,readonly',
            '-e', 'AIDER_DOCKER=1', '-e', 'AIDER_BENCHMARK_DIR=/run-data',
            '-e', 'OLLAMA_API_BASE=' + cfg['OLLAMA_DOCKER_BASE_URL'],
            '-e', 'AIDER_ANALYTICS=false', '-e', 'PYTHONUNBUFFERED=1', '-e', 'NO_COLOR=1',
            image['Id'], 'python3', '/run-data/container-entry.py', '/run-data/aider',
            '--model', 'ollama_chat/' + model['name'], '--exercises-dir', '/exercises',
            '--num-tests', cfg['BENCHMARK_TEST_COUNT'], '--threads', cfg['BENCHMARK_THREADS'],
            '--tries', cfg['BENCHMARK_TRIES'], '--edit-format', cfg['EDIT_FORMAT'],
            '--read-model-settings', '/run-data/model-settings.yml']
    # Store command without host paths; environment allowlist only.
    write_json(raw / 'command.json', [a.replace(str(raw), '<RUN_DIR>').replace(str(DEPS), '<DEPS_DIR>') for a in args])
    print(f'Run: {run_id}; {len(tasks)} tasks. Logs: results/raw/{run_id}/', flush=True)
    stop = threading.Event()
    sampler = threading.Thread(target=collect_stats, args=(raw / 'stats.csv', float(cfg['STATS_INTERVAL_SEC']), stop), daemon=True)
    code = 1
    started = None
    old_handlers = {}
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            old_handlers[sig] = signal.signal(sig, interrupted)
        # Inspect endpoint from the same container network, without generating tokens.
        probe = ('import json,urllib.request; '
                 'd=json.load(urllib.request.urlopen(' + repr(cfg['OLLAMA_DOCKER_BASE_URL'] + '/api/tags') + ',timeout=10)); '
                 'assert any(m.get("digest")==' + repr(model['digest']) + ' for m in d["models"])')
        with (raw / 'stderr.log').open('a') as probe_log:
            subprocess.run(['docker', 'run', '--rm', '--add-host=host.docker.internal:host-gateway',
                            image['Id'], 'python3', '-c', probe], check=True, timeout=30,
                           stdout=subprocess.DEVNULL, stderr=probe_log)
        inventory = command(['docker', 'run', '--rm', image['Id'], 'python3', '-m', 'pip', 'freeze'], timeout=60)
        (raw / 'python-packages.txt').write_text(inventory or 'unsupported\n')
        meta['observations']['before'] = stats_sample()
        meta['result']['status'] = 'running'
        write_json(metadata_path, meta)
        sampler.start()
        started = time.monotonic()
        with (raw / 'stdout.log').open('w') as stdout, (raw / 'stderr.log').open('w') as stderr:
            code = subprocess.call(args, stdout=stdout, stderr=stderr)
    except KeyboardInterrupt:
        code = 130
        meta['result']['status'] = 'interrupted'
    except (OSError, subprocess.SubprocessError):
        meta['result']['status'] = 'error'
        print('[FAIL] Container preflight/launch failed; check Docker-to-Ollama connectivity.', file=sys.stderr)
    finally:
        elapsed = time.monotonic() - started if started is not None else None
        for sig in old_handlers:
            signal.signal(sig, signal.SIG_IGN)
        if code != 0:
            command(['docker', 'stop', '--time', '5', container], timeout=15)
        stop.set()
        if sampler.ident:
            sampler.join(timeout=45)
        meta['observations']['after'] = stats_sample()
        meta['result'].update(exit_code=code, total_time_sec=elapsed, finished_at=now())
        result = analyze(raw, meta)
        meta['result'].update(result)
        if meta['result']['status'] not in ('interrupted', 'error'):
            meta['result']['status'] = 'completed' if code == 0 and result['unknown_tasks'] == 0 else 'incomplete'
        try:
            meta['model']['digest_after'] = model_info(cfg)['digest']
            if meta['model']['digest_after'] != model['digest']:
                meta['result']['status'] = 'model_changed'
        except (OSError, ValueError):
            meta['model']['digest_after'] = None
            meta['result']['status'] = 'unverified_model'
        write_json(metadata_path, meta)
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
    summarize()
    print(f"Finished: {meta['result']['status']}")
    return code if code else (0 if meta['result']['status'] == 'completed' else 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'doctor', 'system-info', 'build-image', 'run', 'collect-stats', 'summarize'])
    parser.add_argument('--output', help='CSV path for collect-stats (required)')
    parser.add_argument('--interval', type=float, default=5)
    args = parser.parse_args(argv)
    try:
        if args.action == 'system-info':
            print(json.dumps(system_info(), indent=2))
        elif args.action == 'setup':
            setup()
        elif args.action == 'summarize':
            summarize()
        elif args.action == 'collect-stats':
            if not args.output or not math.isfinite(args.interval) or args.interval <= 0:
                parser.error('collect-stats requires --output PATH and a positive --interval')
            collect_stats(args.output, args.interval)
        else:
            cfg = config()
            return {'doctor': doctor, 'build-image': build_image, 'run': run}[args.action](cfg) or 0
        return 0
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f'[FAIL] {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
