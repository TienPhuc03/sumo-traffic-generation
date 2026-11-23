"""
reliability_analysis.py (Task 8.3)
Đánh giá độ ổn định của dữ liệu mô phỏng giữa các seed từ data/csv/*.csv.

Đầu ra:
    data/analysis/kpi_per_seed.csv     KPI của từng (kịch bản, seed)
    data/analysis/reliability.csv      mean, std, CV%, min, max, khoảng tin cậy 95% theo kịch bản
    data/analysis/reliability_boxplot.png
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, 'data', 'csv')
OUT = os.path.join(ROOT, 'data', 'analysis')
ORDER = ['offpeak', 'baseline', 'peak', 'congestion', 'tls_optimized', 'tls_actuated']
LABELS = {
    'offpeak': 'Thấp điểm',
    'baseline': 'Tiêu chuẩn',
    'peak': 'Cao điểm',
    'congestion': 'Ùn tắc',
    'tls_optimized': 'Tối ưu đèn',
    'tls_actuated': 'Đèn cảm ứng',
}

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Segoe UI']
plt.rcParams['axes.unicode_minus'] = False

# Hệ số t hai phía 95% theo bậc tự do (n-1)
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}


def main():
    trip = pd.read_csv(os.path.join(CSV, 'tripinfo.csv'))
    summ = pd.read_csv(os.path.join(CSV, 'summary.csv'))
    queue = pd.read_csv(os.path.join(CSV, 'queue.csv'))
    os.makedirs(OUT, exist_ok=True)
    key = ['scenario', 'seed']

    g = trip.groupby(key)
    k = pd.DataFrame({
        'so_xe_hoan_thanh': g['id'].count(),
        'tg_di_chuyen_tb_s': g['duration'].mean(),
        'tg_cho_tb_s': g['waitingTime'].mean(),
        'tg_mat_mat_tb_s': g['timeLoss'].mean(),
        'van_toc_tb_kmh': (g['routeLength'].sum() / g['duration'].sum()) * 3.6,
        'co2_tb_mg_chuyen': g['CO2_abs'].mean(),
    })
    s = summ[summ['time'] > 0]
    gs = s.groupby(key)
    k['van_toc_mang_kmh'] = gs['meanSpeed'].apply(lambda x: x[x >= 0].mean()) * 3.6
    k['xe_dung_halting_tb'] = gs['halting'].mean()
    k = k.reset_index()
    # Teleport/collision lấy từ log SUMO (run_log.csv do run_multi_seed.py ghi), vì
    # summary.xml chỉ lấy mẫu 60s nên không phản ánh tổng số.
    rl = pd.read_csv(os.path.join(ROOT, 'data', 'raw', 'run_log.csv'))
    rl = rl.drop_duplicates(key, keep='last')[key + ['teleports', 'collisions']]
    k = k.merge(rl, on=key, how='left').set_index(key)
    if len(queue):
        q = queue.groupby(key)['queueing_length'].max()
        k['hang_doi_max_m'] = q
    k = k.reset_index()
    k.to_csv(os.path.join(OUT, 'kpi_per_seed.csv'), index=False, encoding='utf-8-sig')

    metrics = [c for c in k.columns if c not in key]
    rows = []
    for sc in ORDER:
        d = k[k['scenario'] == sc]
        if d.empty:
            continue
        n = len(d)
        for m in metrics:
            v = d[m].astype(float)
            mean, std = v.mean(), v.std(ddof=1) if n > 1 else 0.0
            ci = T95.get(n - 1, 1.96) * std / np.sqrt(n) if n > 1 else 0.0
            rows.append({'scenario': sc, 'metric': m, 'n_seeds': n, 'mean': mean, 'std': std,
                         'cv_percent': (std / mean * 100) if mean else np.nan,
                         'min': v.min(), 'max': v.max(), 'ci95_half_width': ci})
    rel = pd.DataFrame(rows)
    rel.to_csv(os.path.join(OUT, 'reliability.csv'), index=False, encoding='utf-8-sig')

    show = ['van_toc_tb_kmh', 'tg_cho_tb_s', 'tg_mat_mat_tb_s', 'so_xe_hoan_thanh']
    titles = {
        'van_toc_tb_kmh': ('Vận tốc trung bình (km/h)', 'km/h'),
        'tg_cho_tb_s': ('Thời gian chờ TB (s)', 'giây'),
        'tg_mat_mat_tb_s': ('Tổn thất thời gian TB (s)', 'giây'),
        'so_xe_hoan_thanh': ('Số xe hoàn thành', 'xe'),
    }
    present = [sc for sc in ORDER if sc in set(k['scenario'])]
    xlabels = [LABELS.get(sc, sc) for sc in present]
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
    for ax, m in zip(axes, show):
        data = [k[k['scenario'] == sc][m].values for sc in present]
        ax.boxplot(data, tick_labels=xlabels)
        t, yl = titles[m]
        ax.set_title(t, fontweight='bold')
        ax.set_ylabel(yl)
        ax.tick_params(axis='x', rotation=30)
        ax.grid(alpha=.3)
    fig.suptitle('Độ phân tán các chỉ số KPI giữa 5 hạt giống (seed 42–46) theo kịch bản', fontsize=13, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'reliability_boxplot.png'), dpi=150)

    pd.set_option('display.width', 200)
    print(rel[rel['metric'].isin(show)].round(2).to_string(index=False))


if __name__ == '__main__':
    main()
