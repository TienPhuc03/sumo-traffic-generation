"""
aggregate_intervals.py (Task 7.3)
Gộp dữ liệu thô data/raw/<kịch_bản>/seed_<n>/ theo khoảng thời gian cố định và gán nhãn
kịch bản, seed, làn. Ghi ra data/csv/aggregated_<interval>s.csv.

Cấu trúc bảng (khoảng nửa mở [t_start, t_end)):
  * Dòng toàn mạng  (lane = rỗng): 1 dòng / (kịch bản, seed, khoảng). Đủ mọi cột.
  * Dòng theo làn   (lane = mã làn): 1 dòng / (kịch bản, seed, khoảng, làn) chỉ cho làn CÓ
    hàng đợi trong khoảng đó (queue.xml chỉ ghi làn có hàng đợi). Chỉ có cột queue_max_m;
    các cột toàn mạng để trống. Lọc `lane == ''` khi cần số liệu toàn mạng, để không cộng trùng.

Cột:
  running_mean, halting_mean  TB `running`, `halting` của các mẫu summary.xml trong khoảng (xe)
  speed_mean_kmh              TB `meanSpeed` (bỏ -1) × 3.6. Trống nếu không có xe trên mạng.
  departed, arrived           Số xe có `depart` / `arrival` trong khoảng (bỏ arrival = -1)
  duration_mean, waiting_mean, timeloss_mean
                              TB theo xe KẾT THÚC trong khoảng (s). Trống nếu arrived = 0.
                              Xe chưa đến đích (arrival = -1) không tính vào các cột này.
  co2_g                       Σ CO2 (mg/s) × chu kỳ lấy mẫu emission / 1000 (g)
  queue_max_m                 Max `queueing_length` (m). Dòng toàn mạng: max mọi làn, 0 nếu không có hàng đợi.

Chu kỳ lấy mẫu đọc từ dữ liệu (run_multi_seed.py ghi 30 s); khoảng gộp phải là bội số của nó.

Cách dùng:
    python scripts/aggregate_intervals.py                # khoảng 30 s
    python scripts/aggregate_intervals.py --interval 60
    python scripts/aggregate_intervals.py --selftest     # kiểm tra trên 1 seed (peak, seed_42)
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

from xml_to_csv import SCENARIOS, rows_emission, rows_queue, rows_summary, rows_tripinfo

for _s in (sys.stdout, sys.stderr):
    if _s.encoding != 'utf-8':
        try:
            _s.reconfigure(encoding='utf-8')
        except Exception:
            pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'data', 'csv')
NET_COLS = ['running_mean', 'halting_mean', 'speed_mean_kmh', 'departed', 'arrived',
            'duration_mean', 'waiting_mean', 'timeloss_mean', 'co2_g', 'queue_max_m']
COLS = ['scenario', 'seed', 't_start', 't_end', 'lane'] + NET_COLS


def aggregate_run(run_dir, interval):
    """Gộp 1 lần chạy. Trả về DataFrame (dòng toàn mạng + dòng theo làn), chưa có scenario/seed."""
    s = pd.DataFrame(rows_summary(os.path.join(run_dir, 'summary.xml')))
    s = s[['time', 'running', 'halting', 'meanSpeed']].astype(float)
    period = float(s['time'].diff().mode()[0])
    if interval % period:
        sys.exit(f'LỖI: --interval {interval} không phải bội số chu kỳ lấy mẫu {period:g} s ({run_dir})')
    t_end = s['time'].max() + period
    n = int(np.ceil(t_end / interval))
    idx = range(n)

    def b(t):  # chỉ số khoảng của thời điểm t
        return (t // interval).astype(int).clip(upper=n - 1)

    tr = pd.DataFrame(rows_tripinfo(os.path.join(run_dir, 'tripinfo.xml')))
    tr = tr[['depart', 'arrival', 'duration', 'waitingTime', 'timeLoss']].astype(float)
    em = pd.DataFrame(({'time': r['time'], 'CO2': r['CO2']} for r in rows_emission(os.path.join(run_dir, 'emission.xml'))),
                      columns=['time', 'CO2']).astype(float)
    q = pd.DataFrame(({'time': r['timestep'], 'lane': r['id'], 'q': r['queueing_length']}
                      for r in rows_queue(os.path.join(run_dir, 'queue.xml'))), columns=['time', 'lane', 'q'])
    q[['time', 'q']] = q[['time', 'q']].astype(float)

    dep = tr[tr['depart'] >= 0]
    fin = tr[tr['arrival'] >= 0]
    sg = s.groupby(b(s['time']))
    fg = fin.groupby(b(fin['arrival']))
    net = pd.DataFrame({
        't_start': [i * interval for i in idx],
        't_end': [min((i + 1) * interval, t_end) for i in idx],
        'lane': '',
        'running_mean': sg['running'].mean().reindex(idx),
        'halting_mean': sg['halting'].mean().reindex(idx),
        'speed_mean_kmh': s[s['meanSpeed'] >= 0].groupby(b(s['time']))['meanSpeed'].mean().reindex(idx) * 3.6,
        'departed': dep.groupby(b(dep['depart'])).size().reindex(idx, fill_value=0),
        'arrived': fg.size().reindex(idx, fill_value=0),
        'duration_mean': fg['duration'].mean().reindex(idx),
        'waiting_mean': fg['waitingTime'].mean().reindex(idx),
        'timeloss_mean': fg['timeLoss'].mean().reindex(idx),
        'co2_g': (em.groupby(b(em['time']))['CO2'].sum() * period / 1000).reindex(idx, fill_value=0.0),
        'queue_max_m': q.groupby(b(q['time']))['q'].max().reindex(idx, fill_value=0.0),
    }, index=idx)

    # Kiểm tra bảo toàn số xe (Acceptance T1)
    assert net['departed'].sum() == len(dep), f'departed lệch tripinfo ({run_dir})'
    assert net['arrived'].sum() + (tr['arrival'] < 0).sum() == len(tr), f'arrived + unfinished lệch tripinfo ({run_dir})'

    lanes = q.groupby([b(q['time']), 'lane'])['q'].max().rename('queue_max_m').reset_index(level='lane')
    lanes['t_start'] = lanes.index * interval
    lanes['t_end'] = np.minimum((lanes.index + 1) * interval, t_end)
    out = pd.concat([net, lanes], ignore_index=True)
    out['departed'] = out['departed'].astype('Int64')
    out['arrived'] = out['arrived'].astype('Int64')
    return out, tr, em, period


def iter_runs(raw):
    for sc in SCENARIOS:
        d = os.path.join(raw, sc)
        if not os.path.isdir(d):
            continue
        for sd in sorted(os.listdir(d)):
            if sd.startswith('seed_') and os.path.exists(os.path.join(d, sd, 'summary.xml')):
                yield sc, int(sd[5:]), os.path.join(d, sd)


def selftest(raw, interval):
    """Kiểm tra trên 1 seed: bảo toàn số xe, CO2, NaN chỉ ở chỗ được phép."""
    run_dir = os.path.join(raw, 'peak', 'seed_42')
    if not os.path.isdir(run_dir):
        sys.exit(f'LỖI: thiếu {run_dir}. Chạy run_multi_seed.py trước.')
    out, tr, em, period = aggregate_run(run_dir, interval)
    net = out[out['lane'] == '']
    lane = out[out['lane'] != '']
    assert net['t_start'].tolist() == [i * interval for i in range(len(net))], 'khoảng không liên tục'
    assert net[['running_mean', 'halting_mean', 'departed', 'arrived', 'co2_g', 'queue_max_m']].notna().all().all()
    assert net.loc[net['arrived'] == 0, 'duration_mean'].isna().all()
    assert net.loc[net['arrived'] > 0, ['duration_mean', 'waiting_mean', 'timeloss_mean']].notna().all().all()
    assert net.loc[net['running_mean'] > 0, 'speed_mean_kmh'].notna().all(), 'thiếu vận tốc khi có xe'
    assert abs(net['co2_g'].sum() - em['CO2'].sum() * period / 1000) < 1e-6
    assert lane['queue_max_m'].notna().all() and (lane['queue_max_m'] > 0).any()
    assert (net['queue_max_m'].values >= lane.groupby('t_start')['queue_max_m'].max().reindex(net['t_start'], fill_value=0).values).all()
    print(f'SELFTEST OK: peak/seed_42, {len(net)} khoảng × {interval} s, {len(lane)} dòng làn, '
          f'departed={net["departed"].sum()}, arrived={net["arrived"].sum()}, unfinished={(tr["arrival"] < 0).sum()}')


def main():
    ap = argparse.ArgumentParser(description='Gộp dữ liệu SUMO theo khoảng thời gian (Task 7.3)')
    ap.add_argument('--interval', type=int, default=30, help='Độ dài khoảng gộp (s), mặc định 30')
    ap.add_argument('--raw', default=RAW)
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if not os.path.isdir(a.raw):
        sys.exit(f'LỖI: không thấy {a.raw}. Chạy run_multi_seed.py trước.')
    if a.selftest:
        return selftest(a.raw, a.interval)

    parts = []
    for sc, seed, run_dir in iter_runs(a.raw):
        df, _, _, _ = aggregate_run(run_dir, a.interval)
        df.insert(0, 'seed', seed)
        df.insert(0, 'scenario', sc)
        parts.append(df)
        print(f'[{sc:<14}] seed={seed}: {(df["lane"] == "").sum()} khoảng, {(df["lane"] != "").sum()} dòng làn')
    if not parts:
        sys.exit(f'LỖI: không có lần chạy nào trong {a.raw}.')
    out = pd.concat(parts, ignore_index=True)[COLS].sort_values(['scenario', 'seed', 't_start', 'lane'], kind='stable')
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f'aggregated_{a.interval}s.csv')
    out.to_csv(path, index=False, encoding='utf-8')
    print(f'-> {path} ({len(out)} dòng, {len(parts)} lần chạy)')


if __name__ == '__main__':
    main()
