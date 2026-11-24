"""
plot_results.py
Tự động đọc dữ liệu XML và CSV từ thư mục data/ để vẽ các biểu đồ phân tích:
1. Biểu đồ cơ sở dòng giao thông (Fundamental Diagram: Lưu lượng - Mật độ - Vận tốc) - Task 8.1
2. So sánh Vận tốc trung bình giữa các kịch bản.
3. So sánh Thời gian chờ trung bình & Tổn thất thời gian.
4. Diễn biến số lượng phương tiện theo thời gian (Time-series).
5. Phân bố thời gian chờ theo loại phương tiện (Boxplot).
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET

# Thiết lập thư mục cache Matplotlib tránh cảnh báo trên Windows
os.environ.setdefault('MPLCONFIGDIR', os.path.join(tempfile.gettempdir(), 'matplotlib_cache'))

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Cấu hình phong cách biểu đồ
sns.set_theme(style="whitegrid")
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Segoe UI']
plt.rcParams['axes.unicode_minus'] = False

SCENARIOS = [
    ('offpeak', '1. Thấp điểm', '#2ecc71'),
    ('baseline', '2. Tiêu chuẩn', '#3498db'),
    ('peak', '3. Cao điểm', '#e67e22'),
    ('congestion', '4. Ùn tắc', '#e74c3c'),
    ('tls_optimized', '5. Tối ưu đèn', '#9b59b6'),
    ('tls_actuated', '6. Đèn thông minh', '#1abc9c'),
]

def load_data(data_dir):
    summary_dfs = {}
    tripinfo_dfs = {}
    kpi_records = []
    
    for key, label, color in SCENARIOS:
        sum_path = os.path.join(data_dir, f'summary_{key}.xml')
        trip_path = os.path.join(data_dir, f'tripinfo_{key}.xml')
        
        # Đọc summary_*.xml
        if os.path.exists(sum_path) and os.path.getsize(sum_path) > 100:
            try:
                with open(sum_path, 'r', encoding='utf-8') as f:
                    xml_str = f.read()
                if not xml_str.strip().endswith('</summary>'):
                    xml_str += '\n</summary>'
                root = ET.fromstring(xml_str)
                steps = [s.attrib for s in root.findall('step')]
                df_s = pd.DataFrame(steps)
                for col in ['time', 'running', 'halting', 'meanSpeed', 'meanWaitingTime']:
                    if col in df_s.columns:
                        df_s[col] = pd.to_numeric(df_s[col], errors='coerce')
                df_s['meanSpeedKmh'] = df_s['meanSpeed'].apply(lambda x: x * 3.6 if x >= 0 else None)
                summary_dfs[key] = df_s
            except Exception as e:
                print(f"Lỗi đọc {sum_path}: {e}")
                
        # Đọc tripinfo_*.xml
        if os.path.exists(trip_path) and os.path.getsize(trip_path) > 100:
            try:
                with open(trip_path, 'r', encoding='utf-8') as f:
                    xml_str = f.read()
                if not xml_str.strip().endswith('</tripinfos>'):
                    xml_str += '\n</tripinfos>'
                root = ET.fromstring(xml_str)
                trips = [t.attrib for t in root.findall('tripinfo')]
                df_t = pd.DataFrame(trips)
                for col in ['duration', 'routeLength', 'waitingTime', 'timeLoss']:
                    if col in df_t.columns:
                        df_t[col] = pd.to_numeric(df_t[col], errors='coerce')
                df_t['scenario'] = label
                df_t['speedKmh'] = (df_t['routeLength'] / df_t['duration']) * 3.6
                tripinfo_dfs[key] = df_t
                
                kpi_records.append({
                    'key': key,
                    'scenario': label,
                    'color': color,
                    'completed': len(df_t),
                    'avg_speed': df_t['speedKmh'].mean() if len(df_t) > 0 else 0,
                    'avg_wait': df_t['waitingTime'].mean() if len(df_t) > 0 else 0,
                    'avg_timeloss': df_t['timeLoss'].mean() if len(df_t) > 0 else 0,
                })
            except Exception as e:
                print(f"Lỗi đọc {trip_path}: {e}")
                
    return summary_dfs, tripinfo_dfs, pd.DataFrame(kpi_records)

DETECTOR_PERIOD_S = 900  # freq="900.0" trong routes/detectors.add.xml


def load_detector_points(data_dir):
    """Đọc detector E1 của mọi (kịch bản, seed) trong data/raw/<kịch_bản>/seed_<n>/detector.xml.
    Nếu chưa có data/raw thì dùng data/detector_output_cleaned.csv (1 lần chạy, 1 kịch bản)."""
    raw = os.path.join(data_dir, 'raw')
    rows = []
    for key, _, _ in SCENARIOS:
        sc_dir = os.path.join(raw, key)
        if not os.path.isdir(sc_dir):
            continue
        for sd in sorted(os.listdir(sc_dir)):
            p = os.path.join(sc_dir, sd, 'detector.xml')
            if sd.startswith('seed_') and os.path.exists(p):
                for _, el in ET.iterparse(p):
                    if el.tag == 'interval':
                        rows.append({'scenario': key, 'seed': int(sd[5:]), 'id': el.get('id'),
                                     'begin': float(el.get('begin')), 'end': float(el.get('end')),
                                     'nVehContrib': int(el.get('nVehContrib')), 'speed': float(el.get('speed'))})
                        el.clear()
    if rows:
        df = pd.DataFrame(rows)
        n_runs = df[['scenario', 'seed']].drop_duplicates().shape[0]
        return df, f'Nguồn: data/raw/*/seed_*/detector.xml — {df["scenario"].nunique()} kịch bản, {n_runs} lần chạy, 12 detector E1, chu kỳ 900 s'
    csv_path = os.path.join(data_dir, 'detector_output_cleaned.csv')
    if not os.path.exists(csv_path):
        return pd.DataFrame(), ''
    df = pd.read_csv(csv_path)
    df['scenario'] = 'tls_actuated'  # detector_output.xml bị ghi đè mỗi lần chạy; bản hiện có là tls_actuated
    return df, 'Nguồn: data/detector_output_cleaned.csv — CHỈ 1 lần chạy (tls_actuated), 12 detector E1, chu kỳ 900 s'


def plot_fundamental_diagram(data_dir):
    """Vẽ biểu đồ Fundamental Diagram (Task 8.1) từ detector E1 (chu kỳ 900 s)."""
    df, source = load_detector_points(data_dir)
    if df.empty:
        print("Chưa có dữ liệu detector (data/raw/ hoặc detector_output_cleaned.csv). Bỏ qua Fundamental Diagram.")
        return

    # q (xe/h) = N × 3600 / Δt, Δt = 900 s  ->  q = nVehContrib × 4
    df['flow'] = df['nVehContrib'] * 3600 / DETECTOR_PERIOD_S
    assert (df['flow'] == df['nVehContrib'] * 4).all(), 'flow phải bằng nVehContrib × 4'
    # Bỏ khung không có xe (speed = -1 hoặc 0) vì không xác định được mật độ k = q / v
    df = df[(df['speed'] > 0) & (df['nVehContrib'] > 0)].copy()
    df['speed_kmh'] = df['speed'] * 3.6
    df['density'] = df['flow'] / df['speed_kmh']

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.4))
    fig.suptitle('PHÂN TÍCH QUAN HỆ LƯU LƯỢNG - MẬT ĐỘ - VẬN TỐC (TASK 8.1)', fontsize=15, fontweight='bold', y=0.99)
    fig.text(0.5, 0.925, f'{source}. q = nVehContrib × 4 (xe/h), k = q / v', ha='center', fontsize=10, style='italic')

    for key, label, color in SCENARIOS:
        d = df[df['scenario'] == key]
        if d.empty:
            continue
        axes[0].scatter(d['density'], d['flow'], color=color, alpha=0.6, edgecolors='k', linewidths=0.4, label=label)
        axes[1].scatter(d['density'], d['speed_kmh'], color=color, alpha=0.6, edgecolors='k', linewidths=0.4, label=label)

    axes[0].set_title('Quan hệ Lưu lượng - Mật độ (Flow vs Density)', fontsize=13, fontweight='bold')
    axes[0].set_ylabel('Lưu lượng (xe/h)', fontsize=11)
    axes[1].set_title('Quan hệ Vận tốc - Mật độ (Speed vs Density)', fontsize=13, fontweight='bold')
    axes[1].set_ylabel('Vận tốc trung bình thời gian (km/h)', fontsize=11)
    for ax in axes:
        ax.set_xlabel('Mật độ (xe/km)', fontsize=11)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))

    output_path = os.path.join(data_dir, 'traffic_fundamental_diagram.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"-> Đã lưu biểu đồ Fundamental Diagram (Task 8.1) tại: {output_path}")

def apply_multi_seed_kpi(data_dir, df_kpi):
    """Panel 1-2: thay KPI 1 lần chạy bằng trung bình ± độ lệch chuẩn các seed trong
    data/analysis/kpi_per_seed.csv (cùng công thức với reliability.csv). Thiếu file thì giữ nguyên."""
    p = os.path.join(data_dir, 'analysis', 'kpi_per_seed.csv')
    if df_kpi.empty or not os.path.exists(p):
        return df_kpi, 'data/tripinfo_*.xml (1 lần chạy, seed mặc định)'
    cols = {'avg_speed': 'van_toc_tb_kmh', 'avg_wait': 'tg_cho_tb_s', 'avg_timeloss': 'tg_mat_mat_tb_s'}
    g = pd.read_csv(p, encoding='utf-8-sig').groupby('scenario')[list(cols.values())]
    mean, std = g.mean(), g.std()
    df_kpi = df_kpi[df_kpi['key'].isin(mean.index)].copy()
    for new, old in cols.items():
        df_kpi[new] = df_kpi['key'].map(mean[old])
        df_kpi[new + '_std'] = df_kpi['key'].map(std[old])
    return df_kpi, f'data/analysis/kpi_per_seed.csv (TB ± độ lệch chuẩn {g.size().min()} seed)'


def plot_dashboard(summary_dfs, tripinfo_dfs, df_kpi, output_dir, kpi_src=''):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('HỆ THỐNG MÔ PHỎNG & SO SÁNH CÁC KỊCH BẢN GIAO THÔNG (NGÃ TƯ HÀNG XANH)', fontsize=16, fontweight='bold', y=0.995)
    fig.text(0.5, 0.962, va='top', s=f'Panel 1-2: {kpi_src}  |  Panel 3-4: data/summary_*.xml, data/tripinfo_*.xml (1 lần chạy mỗi kịch bản)',
             ha='center', fontsize=10, style='italic')

    # 1. Biểu đồ Vận tốc trung bình
    ax1 = axes[0, 0]
    if not df_kpi.empty:
        bars = ax1.bar(df_kpi['scenario'], df_kpi['avg_speed'], yerr=df_kpi.get('avg_speed_std'), capsize=4,
                       color=df_kpi['color'], edgecolor='black', alpha=0.85)
        ax1.set_title('1. Vận tốc Trung bình qua Nút giao (km/h)', fontsize=13, fontweight='bold')
        ax1.set_ylabel('Vận tốc (km/h)', fontsize=11)
        ax1.tick_params(axis='x', rotation=25)
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height:.1f}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3), textcoords="offset points",
                         ha='center', va='bottom', fontweight='bold')
    
    # 2. Biểu đồ Thời gian chờ và Tổn thất thời gian
    ax2 = axes[0, 1]
    if not df_kpi.empty:
        x = range(len(df_kpi))
        width = 0.35
        ax2.bar([i - width/2 for i in x], df_kpi['avg_wait'], width=width, yerr=df_kpi.get('avg_wait_std'), capsize=3,
                label='Thời gian chờ', color='#e74c3c', alpha=0.85)
        ax2.bar([i + width/2 for i in x], df_kpi['avg_timeloss'], width=width, yerr=df_kpi.get('avg_timeloss_std'), capsize=3,
                label='Tổn thất độ trễ', color='#f39c12', alpha=0.85)
        ax2.set_title('2. Thời gian Dừng chờ & Tổn thất Độ trễ Trung bình (s)', fontsize=13, fontweight='bold')
        ax2.set_ylabel('Thời gian (giây)', fontsize=11)
        ax2.set_xticks(list(x))
        ax2.set_xticklabels(df_kpi['scenario'], rotation=25)
        ax2.legend()
        
    # 3. Biểu đồ diễn biến dòng xe theo thời gian
    ax3 = axes[1, 0]
    for key, label, color in SCENARIOS:
        if key in summary_dfs:
            df_s = summary_dfs[key]
            df_sub = df_s.iloc[::5]
            ax3.plot(df_sub['time'], df_sub['running'], label=label, color=color, linewidth=2)
    ax3.set_title('3. Diễn biến Số lượng Phương tiện theo Thời gian', fontsize=13, fontweight='bold')
    ax3.set_xlabel('Thời gian mô phỏng (giây)', fontsize=11)
    ax3.set_ylabel('Số lượng xe đang chạy', fontsize=11)
    ax3.legend()
    
    # 4. Biểu đồ phân bố thời gian chờ theo loại phương tiện
    ax4 = axes[1, 1]
    peak_df = tripinfo_dfs.get('peak')
    if peak_df is not None and not peak_df.empty:
        vtype_names = {'moped': 'Xe máy', 'passenger': 'Ô tô con', 'bus': 'Xe buýt', 'truck': 'Xe tải'}
        peak_df = peak_df.copy()
        peak_df['vtype_vn'] = peak_df['vType'].map(vtype_names).fillna(peak_df['vType'])
        palette = {'Xe máy': '#e74c3c', 'Ô tô con': '#2ecc71', 'Xe buýt': '#3498db', 'Xe tải': '#f1c40f'}
        sns.boxplot(data=peak_df, x='vtype_vn', y='waitingTime', hue='vtype_vn', palette=palette, legend=False, ax=ax4)
        ax4.set_title('4. Phân bố Thời gian Chờ theo Loại Xe (Giờ cao điểm)', fontsize=13, fontweight='bold')
        ax4.set_xlabel('Loại phương tiện', fontsize=11)
        ax4.set_ylabel('Thời gian chờ (giây)', fontsize=11)
    else:
        ax4.text(0.5, 0.5, 'Chưa có đủ dữ liệu tripinfo', ha='center', va='center')
        
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    output_path = os.path.join(output_dir, 'traffic_comparison_dashboard.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"-> Đã lưu biểu đồ tổng hợp chất lượng cao tại: {output_path}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    print("Đang đọc dữ liệu kết quả từ thư mục data/...")
    
    # Chạy vẽ Fundamental Diagram cho Task 8.1 trước
    plot_fundamental_diagram(data_dir)
    
    # Chạy vẽ Dashboard so sánh các kịch bản
    summary_dfs, tripinfo_dfs, df_kpi = load_data(data_dir)
    if not df_kpi.empty:
        df_kpi, kpi_src = apply_multi_seed_kpi(data_dir, df_kpi)
        plot_dashboard(summary_dfs, tripinfo_dfs, df_kpi, data_dir, kpi_src)
    else:
        print("Cảnh báo: Chưa tìm thấy dữ liệu kịch bản trong data/ cho dashboard tổng hợp.")

if __name__ == '__main__':
    main()