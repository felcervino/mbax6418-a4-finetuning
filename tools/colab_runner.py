"""Colab harness for the dry run (DEC-09). Not part of the submitted notebook.

Usage in one Colab cell:  exec(open('/content/colab_runner.py').read())
Then: run_cell(i) runs notebook code cell i; run_cell(i, bg=True) runs it in a thread; tail(i) shows its log; status().
Logs go to /content/dry_logs/cell<i>.log. Notebook file: /content/a4_finetune.ipynb (uploaded).
"""
import hashlib
import json
import os
import sys
import threading
import time
import traceback

import glob
NBP = max(glob.glob('/content/a4_finetune*.ipynb'), key=os.path.getmtime)
NB = json.load(open(NBP))
CODE = [''.join(c['source']) for c in NB['cells'] if c['cell_type'] == 'code']
LOGD = '/content/dry_logs'
os.makedirs(LOGD, exist_ok=True)
G = globals()
THREADS = {}


class _Router:
    """Routes print output per thread: a background cell writes to its log file, everything else to the notebook."""
    def __init__(self, orig):
        self.orig = orig
        self.files = {}

    def write(self, s):
        f = self.files.get(threading.get_ident())
        return (f or self.orig).write(s)

    def flush(self):
        f = self.files.get(threading.get_ident())
        return (f or self.orig).flush()

    def __getattr__(self, name):
        return getattr(self.orig, name)


if not isinstance(sys.stdout, _Router):
    sys.stdout = _Router(sys.stdout)
    sys.stderr = _Router(sys.stderr)


def run_cell(i, bg=False, n=2500):
    def work():
        buf = open(f'{LOGD}/cell{i}.log', 'w', buffering=1)
        tid = threading.get_ident()
        sys.stdout.files[tid] = buf
        sys.stderr.files[tid] = buf
        t0 = time.time()
        try:
            exec(compile(CODE[i], f'cell{i}', 'exec'), G)
            buf.write(f'\n[[DONE OK in {time.time() - t0:.1f}s]]\n')
        except BaseException:
            buf.write(f'\n[[FAILED after {time.time() - t0:.1f}s]]\n' + traceback.format_exc())
        finally:
            sys.stdout.files.pop(tid, None)
            sys.stderr.files.pop(tid, None)
            buf.close()
    if bg:
        th = threading.Thread(target=work, daemon=True)
        THREADS[i] = th
        th.start()
        print('started cell', i, 'in background')
    else:
        work()
        tail(i, n)


def tail(i, n=2500):
    s = open(f'{LOGD}/cell{i}.log').read()
    print(f'--- cell {i} log, last {n} chars of {len(s)}')
    print(s[-n:])


def status():
    for i, th in THREADS.items():
        print(i, 'alive' if th.is_alive() else 'finished')


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


print(len(CODE), 'code cells; zip sha12:', sha('/content/split_data.zip')[:12] if os.path.exists('/content/split_data.zip') else 'missing')
for i, c in enumerate(CODE):
    print(i, c.split('\n')[0][:60])
