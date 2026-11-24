"""
run_multi_seed.py (Task 6.2)
Chạy các kịch bản SUMO với nhiều seed ngẫu nhiên và lưu kết quả có tổ chức:

    data/raw/<kịch_bản>/seed_<n>/{tripinfo,summary,queue,edgedata,emission,detector,edgedata_detector}.xml

Cách dùng:
    python scripts/run_multi_seed.py                         # 6 kịch bản x 5 seed (42..46)
    python scripts/run_multi_seed.py --seeds 5 --first-seed 42
    python scripts/run_multi_seed.py --scenario peak --seeds 2
    python scripts/run_multi_seed.py --steps 300             # chạy ngắn để thử
"""
import argparse
import csv
import os
import shutil
import subprocess
import sys
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DIR = os.path.join(ROOT, 'configs')
DATA_DIR = os.path.join(ROOT, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
SCENARIOS = ['offpeak', 'baseline', 'peak', 'congestion', 'tls_optimized', 'tls_actuated']
# Chu kỳ ghi summary/queue/emission cho data/raw (cfg gốc là 60 s). 30 s để gộp được
# theo khoảng 30 s ở aggregate_intervals.py; không ảnh hưởng động học mô phỏng.
SAMPLE_PERIOD = 30


def find_sumo():
    exe = shutil.which('sumo')
    if exe:
        return exe
    home = os.environ.get('SUMO_HOME')
    cands = [os.path.join(home, 'bin', 'sumo.exe')] if home else []
    cands.append(r'C:\Program Files (x86)\SUMO\bin\sumo.exe')
    for c in cands:
        if os.path.exists(c):
            return c
    sys.exit('Không tìm thấy sumo. Hãy đặt SUMO_HOME hoặc thêm sumo vào PATH.')


def run_one(sumo, scenario, seed, steps):
    out = os.path.join(RAW_DIR, scenario, f'seed_{seed}')
    os.makedirs(out, exist_ok=True)
    cmd = [
        sumo, '-c', f'scenario_{scenario}.sumocfg',
        '--seed', str(seed),
        '--tripinfo-output', os.path.join(out, 'tripinfo.xml'),
        '--summary-output', os.path.join(out, 'summary.xml'),
        '--queue-output', os.path.join(out, 'queue.xml'),
        '--edgedata-output', os.path.join(out, 'edgedata.xml'),
        '--emission-output', os.path.join(out, 'emission.xml'),
        '--summary-output.period', str(SAMPLE_PERIOD),
        '--queue-output.period', str(SAMPLE_PERIOD),
        '--device.emissions.period', str(SAMPLE_PERIOD),
        '--no-warnings', 'true',
        '--log', os.path.join(out, 'sumo.log'),
        '--error-log', os.path.join(out, 'sumo_error.log'),
    ]
    if steps:
        cmd += ['--end', str(steps)]
    t0 = time.time()
    res = subprocess.run(cmd, cwd=CFG_DIR, capture_output=True, text=True)
    # Detector/edgeData khai báo trong detectors.add.xml ghi cố định vào data/
    for src, dst in (('detector_output.xml', 'detector.xml'),
                     ('edgedata_output.xml', 'edgedata_detector.xml')):
        p = os.path.join(DATA_DIR, src)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(out, dst))
    return res.returncode, time.time() - t0, out


def count_events(log_path):
    """Đếm teleport/collision trong log SUMO (phục vụ Task 6.1 và 8.3)."""
    tp = col = 0
    if os.path.exists(log_path):
        with open(log_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                low = line.lower()
                if 'teleports:' in low:
                    try:
                        tp = int(low.split('teleports:')[1].split()[0])
                    except Exception:
                        pass
                if 'collisions:' in low:
                    try:
                        col = int(low.split('collisions:')[1].split()[0])
                    except Exception:
                        pass
    return tp, col


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', default='all', choices=['all'] + SCENARIOS)
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--first-seed', type=int, default=42)
    ap.add_argument('--steps', type=int, default=None)
    a = ap.parse_args()

    sumo = find_sumo()
    targets = SCENARIOS if a.scenario == 'all' else [a.scenario]
    seeds = range(a.first_seed, a.first_seed + a.seeds)
    os.makedirs(RAW_DIR, exist_ok=True)
    rows = []
    for sc in targets:
        for sd in seeds:
            code, dt, out = run_one(sumo, sc, sd, a.steps)
            tp, col = count_events(os.path.join(out, 'sumo.log'))
            print(f'[{sc:<14}] seed={sd} exit={code} {dt:6.1f}s teleports={tp} collisions={col}', flush=True)
            rows.append([sc, sd, code, round(dt, 1), tp, col])
    log = os.path.join(RAW_DIR, 'run_log.csv')
    new = not os.path.exists(log)
    with open(log, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['scenario', 'seed', 'exit_code', 'seconds', 'teleports', 'collisions'])
        w.writerows(rows)
    print('Hoàn tất. Dữ liệu tại', RAW_DIR)


if __name__ == '__main__':
    main()
