"""
plot_results.py
Tự động đọc dữ liệu XML từ thư mục data/ và vẽ các biểu đồ phân tích thông số dòng giao thông:
1. Biểu đồ cột: So sánh Vận tốc trung bình giữa các kịch bản.
2. Biểu đồ cột: So sánh Thời gian chờ trung bình (Waiting Time) & Độ trễ (Time Loss).
3. Biểu đồ đường (Time-series): Diễn biến số lượng phương tiện lưu thông theo thời gian.
4. Biểu đồ hộp (Boxplot): Phân bố thời gian chờ theo từng loại phương tiện (Xe máy, Ô tô, Bus, Xe tải).

Cách dùng:
    python scripts/plot_results.py
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
                
                # Tính KPI tổng hợp
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

def plot_dashboard(summary_dfs, tripinfo_dfs, df_kpi, output_dir):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('HỆ THỐNG MÔ PHỎNG & SO SÁNH CÁC KỊCH BẢN GIAO THÔNG (NGÃ TƯ HÀNG XANH)', fontsize=16, fontweight='bold', y=0.98)
    
    # 1. Biểu đồ Vận tốc trung bình (Bar chart)
    ax1 = axes[0, 0]
    if not df_kpi.empty:
        bars = ax1.bar(df_kpi['scenario'], df_kpi['avg_speed'], color=df_kpi['color'], edgecolor='black', alpha=0.85)
        ax1.set_title('1. Vận tốc Trung bình qua Nút giao (km/h)', fontsize=13, fontweight='bold')
        ax1.set_ylabel('Vận tốc (km/h)', fontsize=11)
        ax1.tick_params(axis='x', rotation=25)
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height:.1f}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3), textcoords="offset points",
                         ha='center', va='bottom', fontweight='bold')
    
    # 2. Biểu đồ Thời gian chờ và Tổn thất thời gian (Grouped Bar chart)
    ax2 = axes[0, 1]
    if not df_kpi.empty:
        x = range(len(df_kpi))
        width = 0.35
        ax2.bar([i - width/2 for i in x], df_kpi['avg_wait'], width=width, label='Thời gian chờ (Waiting Time)', color='#e74c3c', alpha=0.85)
        ax2.bar([i + width/2 for i in x], df_kpi['avg_timeloss'], width=width, label='Tổn thất thời gian (Time Loss)', color='#f39c12', alpha=0.85)
        ax2.set_title('2. Thời gian Dừng chờ & Tổn thất Độ trễ Trung bình (s)', fontsize=13, fontweight='bold')
        ax2.set_ylabel('Thời gian (giây)', fontsize=11)
        ax2.set_xticks(list(x))
        ax2.set_xticklabels(df_kpi['scenario'], rotation=25)
        ax2.legend()
        
    # 3. Biểu đồ diễn biến dòng xe theo thời gian (Time-series)
    ax3 = axes[1, 0]
    for key, label, color in SCENARIOS:
        if key in summary_dfs:
            df_s = summary_dfs[key]
            # Lấy mẫu mỗi 5 bước để đồ thị mượt mà
            df_sub = df_s.iloc[::5]
            ax3.plot(df_sub['time'], df_sub['running'], label=label, color=color, linewidth=2)
    ax3.set_title('3. Diễn biến Số lượng Phương tiện trên Mạng lưới theo Thời gian', fontsize=13, fontweight='bold')
    ax3.set_xlabel('Thời gian mô phỏng (giây)', fontsize=11)
    ax3.set_ylabel('Số lượng xe đang chạy (running)', fontsize=11)
    ax3.legend()
    
    # 4. Biểu đồ phân bố thời gian chờ theo loại phương tiện trong giờ cao điểm (Boxplot)
    ax4 = axes[1, 1]
    peak_df = tripinfo_dfs.get('peak')
    if peak_df is not None and not peak_df.empty:
        # Đổi tên loại xe cho thân thiện
        vtype_names = {'moped': 'Xe máy', 'passenger': 'Ô tô con', 'bus': 'Xe buýt', 'truck': 'Xe tải'}
        peak_df = peak_df.copy()
        peak_df['vtype_vn'] = peak_df['vType'].map(vtype_names).fillna(peak_df['vType'])
        palette = {'Xe máy': '#e74c3c', 'Ô tô con': '#2ecc71', 'Xe buýt': '#3498db', 'Xe tải': '#f1c40f'}
        sns.boxplot(data=peak_df, x='vtype_vn', y='waitingTime', palette=palette, ax=ax4)
        ax4.set_title('4. Phân bố Thời gian Chờ theo Loại Xe (Kịch bản Giờ cao điểm)', fontsize=13, fontweight='bold')
        ax4.set_xlabel('Loại phương tiện', fontsize=11)
        ax4.set_ylabel('Thời gian chờ (giây)', fontsize=11)
    else:
        ax4.text(0.5, 0.5, 'Chưa có đủ dữ liệu tripinfo', ha='center', va='center')
        
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'traffic_comparison_dashboard.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n-> Đã lưu biểu đồ tổng hợp chất lượng cao tại: {output_path}")
    
    # Hiển thị cửa sổ trực quan nếu chạy môi trường có desktop
    try:
        plt.show()
    except Exception:
        pass

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    print("Đang đọc dữ liệu kết quả từ thư mục data/...")
    summary_dfs, tripinfo_dfs, df_kpi = load_data(data_dir)
    
    if df_kpi.empty:
        print("Cảnh báo: Chưa tìm thấy dữ liệu trong data/. Vui lòng chạy mô phỏng trước (ví dụ: python scripts/run_all_scenarios.py --steps 300).")
        return
        
    print(f"-> Đã nạp dữ liệu của {len(df_kpi)} kịch bản.")
    plot_dashboard(summary_dfs, tripinfo_dfs, df_kpi, data_dir)

if __name__ == '__main__':
    main()
