#!/usr/bin/env python3
"""Run six sequential end-to-end measurements; reruns replace the same month's outputs."""
import csv
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parents[1]
evidence = root / 'docs/evidence'
evidence.mkdir(exist_ok=True)
with (evidence / 'performance.csv').open('w', newline='') as output:
    writer = csv.writer(output)
    writer.writerow(['started_utc', 'master', 'run', 'elapsed_seconds', 'exit_code'])
    # Alternate configurations to reduce ordering bias. No concurrent ETL writers.
    for trial in range(1, 4):
        for threads in (2, 4):
            master = f'local[{threads}]'
            started = datetime.now(timezone.utc).isoformat()
            before = time.perf_counter()
            with (evidence / f'etl-local{threads}-{trial}.txt').open('w') as log:
                result = subprocess.run([
                    'docker', 'compose', 'run', '--rm', 'etl', 'python', '-m',
                    'src.etl', '--month', '2024-01', '--spark-master', master,
                ], cwd=root, stdout=log, stderr=subprocess.STDOUT)
            elapsed = time.perf_counter() - before
            writer.writerow([started, master, trial, f'{elapsed:.3f}', result.returncode])
            output.flush()
            print(f'{master} run {trial}: {elapsed:.3f}s exit={result.returncode}', flush=True)
            if result.returncode:
                raise SystemExit(result.returncode)
