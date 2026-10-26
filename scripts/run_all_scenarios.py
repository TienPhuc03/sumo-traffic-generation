"""
run_all_scenarios.py
Tự động hóa chạy và so sánh kết quả các kịch bản mô phỏng SUMO tại Ngã tư Hàng Xanh.

Cách sử dụng:
    python run_all_scenarios.py                 # Chạy tất cả kịch bản (mặc định headless sumo)
    python run_all_scenarios.py --gui           # Chạy có giao diện trực quan SUMO-GUI
    python run_all_scenarios.py --steps 300     # Chạy 300 giây mô phỏng (mặc định 3600s)
    python run_all_scenarios.py --scenario peak # Chỉ chạy kịch bản giờ cao điểm
"""

import os
import sys
import argparse
import subprocess
import xml.etree.ElementTree as ET

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCENARIOS = {
    'offpeak': {
        'name': '1. Giờ thấp điểm (Off-peak)',
        'cfg': 'scenario_offpeak.sumocfg',
        'tripinfo': 'tripinfo_offpeak.xml',
        'summary': 'summary_offpeak.xml'
    },
    'baseline': {
        'name': '2. Tiêu chuẩn / Cơ sở (Baseline)',
        'cfg': 'scenario_baseline.sumocfg',
        'tripinfo': 'tripinfo_baseline.xml',
        'summary': 'summary_baseline.xml'
    },
    'peak': {
        'name': '3. Giờ cao điểm (Peak Hours)',
        'cfg': 'scenario_peak.sumocfg',
        'tripinfo': 'tripinfo_peak.xml',
        'summary': 'summary_peak.xml'
    },
    'congestion': {
        'name': '4. Ùn tắc nghiêm trọng (Congestion)',
        'cfg': 'scenario_congestion.sumocfg',
        'tripinfo': 'tripinfo_congestion.xml',
        'summary': 'summary_congestion.xml'
    },
    'tls_optimized': {
        'name': '5. Tối ưu chu kỳ đèn (TLS Optimized)',
        'cfg': 'scenario_tls_optimized.sumocfg',
        'tripinfo': 'tripinfo_tls_optimized.xml',
        'summary': 'summary_tls_optimized.xml'
    },
    'tls_actuated': {
        'name': '6. Đèn thông minh cảm ứng (TLS Actuated)',
        'cfg': 'scenario_tls_actuated.sumocfg',
        'tripinfo': 'tripinfo_tls_actuated.xml',
        'summary': 'summary_tls_actuated.xml'
    }
}

def parse_metrics(data_dir, scenario_info):
    tripinfo_path = os.path.join(data_dir, scenario_info['tripinfo'])
    summary_path = os.path.join(data_dir, scenario_info['summary'])
    
    metrics = {
        'completed': 0,
        'avg_duration': 0.0,
        'avg_waiting_time': 0.0,
        'avg_time_loss': 0.0,
        'avg_speed_kmh': 0.0,
    }
    
    # 1. Phân tích tripinfo.xml
    if os.path.exists(tripinfo_path) and os.path.getsize(tripinfo_path) > 100:
        durations = []
        waiting_times = []
        time_losses = []
        routes_length = []
        
        try:
            for event, elem in ET.iterparse(tripinfo_path):
                if elem.tag == 'tripinfo':
                    dur = float(elem.get('duration', 0))
                    wait = float(elem.get('waitingTime', 0))
                    loss = float(elem.get('timeLoss', 0))
                    length = float(elem.get('routeLength', 0))
                    
                    durations.append(dur)
                    waiting_times.append(wait)
                    time_losses.append(loss)
                    routes_length.append(length)
                elem.clear()
                
            n = len(durations)
            if n > 0:
                metrics['completed'] = n
                metrics['avg_duration'] = sum(durations) / n
                metrics['avg_waiting_time'] = sum(waiting_times) / n
                metrics['avg_time_loss'] = sum(time_losses) / n
                total_dist = sum(routes_length)
                total_dur = sum(durations)
                if total_dur > 0:
                    metrics['avg_speed_kmh'] = (total_dist / total_dur) * 3.6
        except Exception as e:
            pass
            
    return metrics

def run_scenario(cfg_path, use_gui=False, steps=None):
    binary = 'sumo-gui' if use_gui else 'sumo'
    cmd = [binary, '-c', cfg_path]
    if steps is not None:
        cmd.extend(['--end', str(steps)])
    cmd.extend(['--no-warnings', 'true'])
    
    print(f"-> Đang thực thi: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Lỗi khi chạy {cfg_path}:\n{result.stderr}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Chạy tự động bộ kịch bản SUMO Ngã tư Hàng Xanh")
    parser.add_argument('--gui', action='store_true', help="Khởi chạy giao diện SUMO-GUI trực quan")
    parser.add_argument('--steps', type=int, default=None, help="Số bước mô phỏng (giây). Mặc định lấy theo file cfg (3600s)")
    parser.add_argument('--scenario', type=str, default='all', choices=['all'] + list(SCENARIOS.keys()), help="Chọn kịch bản cụ thể để chạy")
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    configs_dir = os.path.join(base_dir, 'configs')
    data_dir = os.path.join(base_dir, 'data')
    
    targets = SCENARIOS.keys() if args.scenario == 'all' else [args.scenario]
    
    print("=" * 80)
    print(" HỆ THỐNG MÔ PHỎNG VÀ ĐÁNH GIÁ CÁC KỊCH BẢN GIAO THÔNG (NGÃ TƯ HÀNG XANH)")
    print("=" * 80)
    
    results = {}
    for key in targets:
        info = SCENARIOS[key]
        cfg_path = os.path.join(configs_dir, info['cfg'])
        print(f"\n[BẮT ĐẦU] {info['name']}")
        
        # Chuyển working directory sang configs để nạp đúng relative paths
        cwd = os.getcwd()
        os.chdir(configs_dir)
        success = run_scenario(info['cfg'], use_gui=args.gui, steps=args.steps)
        os.chdir(cwd)
        
        if success:
            metrics = parse_metrics(data_dir, info)
            results[key] = metrics
            print(f"  + Hoàn thành! Xe thoát nút: {metrics['completed']} | Vận tốc TB: {metrics['avg_speed_kmh']:.2f} km/h | Thời gian chờ TB: {metrics['avg_waiting_time']:.2f} s")
        else:
            print("  - Thất bại!")
            
    # In bảng tổng hợp
    print("\n" + "=" * 80)
    print(" BẢNG TỔNG HỢP SO SÁNH HIỆU NĂNG CÁC KỊCH BẢN (KPIs)")
    print("=" * 80)
    header = f"{'Kịch bản':<36} | {'Xe xong':<8} | {'Vận tốc TB (km/h)':<18} | {'Thời gian chờ (s)':<18} | {'Tổn thất TG (s)':<15}"
    print(header)
    print("-" * 80)
    for key in targets:
        if key in results:
            m = results[key]
            name = SCENARIOS[key]['name']
            row = f"{name:<36} | {m['completed']:<8} | {m['avg_speed_kmh']:<18.2f} | {m['avg_waiting_time']:<18.2f} | {m['avg_time_loss']:<15.2f}"
            print(row)
    print("=" * 80)
    print(f"\nDữ liệu chi tiết đã được xuất vào thư mục: {data_dir}")

if __name__ == '__main__':
    main()
