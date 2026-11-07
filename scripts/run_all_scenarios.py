"""
run_all_scenarios.py
Tự động hóa chạy, kiểm tra 5 file đầu ra (Task 5.3) và so sánh kết quả các kịch bản mô phỏng SUMO tại Ngã tư Hàng Xanh.

Cách sử dụng:
    python scripts/run_all_scenarios.py                 # Chạy tất cả kịch bản (mặc định headless sumo)
    python scripts/run_all_scenarios.py --gui           # Chạy có giao diện trực quan SUMO-GUI
    python scripts/run_all_scenarios.py --steps 300     # Chạy 300 giây mô phỏng (mặc định 3600s)
    python scripts/run_all_scenarios.py --scenario peak # Chỉ chạy kịch bản giờ cao điểm
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
        'summary': 'summary_offpeak.xml',
        'queue': 'queue_offpeak.xml',
        'edgedata': 'edgedata_offpeak.xml',
        'emission': 'emission_offpeak.xml',
    },
    'baseline': {
        'name': '2. Tiêu chuẩn / Cơ sở (Baseline)',
        'cfg': 'scenario_baseline.sumocfg',
        'tripinfo': 'tripinfo_baseline.xml',
        'summary': 'summary_baseline.xml',
        'queue': 'queue_baseline.xml',
        'edgedata': 'edgedata_baseline.xml',
        'emission': 'emission_baseline.xml',
    },
    'peak': {
        'name': '3. Giờ cao điểm (Peak Hours)',
        'cfg': 'scenario_peak.sumocfg',
        'tripinfo': 'tripinfo_peak.xml',
        'summary': 'summary_peak.xml',
        'queue': 'queue_peak.xml',
        'edgedata': 'edgedata_peak.xml',
        'emission': 'emission_peak.xml',
    },
    'congestion': {
        'name': '4. Ùn tắc nghiêm trọng (Congestion)',
        'cfg': 'scenario_congestion.sumocfg',
        'tripinfo': 'tripinfo_congestion.xml',
        'summary': 'summary_congestion.xml',
        'queue': 'queue_congestion.xml',
        'edgedata': 'edgedata_congestion.xml',
        'emission': 'emission_congestion.xml',
    },
    'tls_optimized': {
        'name': '5. Tối ưu chu kỳ đèn (TLS Optimized)',
        'cfg': 'scenario_tls_optimized.sumocfg',
        'tripinfo': 'tripinfo_tls_optimized.xml',
        'summary': 'summary_tls_optimized.xml',
        'queue': 'queue_tls_optimized.xml',
        'edgedata': 'edgedata_tls_optimized.xml',
        'emission': 'emission_tls_optimized.xml',
    },
    'tls_actuated': {
        'name': '6. Đèn thông minh cảm ứng (TLS Actuated)',
        'cfg': 'scenario_tls_actuated.sumocfg',
        'tripinfo': 'tripinfo_tls_actuated.xml',
        'summary': 'summary_tls_actuated.xml',
        'queue': 'queue_tls_actuated.xml',
        'edgedata': 'edgedata_tls_actuated.xml',
        'emission': 'emission_tls_actuated.xml',
    }
}

def parse_metrics(data_dir, scenario_info):
    tripinfo_path = os.path.join(data_dir, scenario_info['tripinfo'])
    queue_path = os.path.join(data_dir, scenario_info['queue'])
    emission_path = os.path.join(data_dir, scenario_info['emission'])
    
    metrics = {
        'completed': 0,
        'avg_duration': 0.0,
        'avg_waiting_time': 0.0,
        'avg_time_loss': 0.0,
        'avg_speed_kmh': 0.0,
        'max_queue_m': 0.0,
        'total_co2_g': 0.0,
        'files_ok': 0
    }
    
    # Kiểm tra đủ 5 file đầu ra theo yêu cầu Task 5.3
    for ftype in ['tripinfo', 'summary', 'queue', 'edgedata', 'emission']:
        fpath = os.path.join(data_dir, scenario_info[ftype])
        if os.path.exists(fpath) and os.path.getsize(fpath) > 100:
            metrics['files_ok'] += 1
    
    # 1. Phân tích tripinfo.xml
    if os.path.exists(tripinfo_path) and os.path.getsize(tripinfo_path) > 100:
        durations, waiting_times, time_losses, routes_length = [], [], [], []
        try:
            for event, elem in ET.iterparse(tripinfo_path):
                if elem.tag == 'tripinfo':
                    durations.append(float(elem.get('duration', 0)))
                    waiting_times.append(float(elem.get('waitingTime', 0)))
                    time_losses.append(float(elem.get('timeLoss', 0)))
                    routes_length.append(float(elem.get('routeLength', 0)))
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
        except Exception:
            pass

    # 2. Phân tích queue.xml (chiều dài hàng đợi lớn nhất)
    if os.path.exists(queue_path) and os.path.getsize(queue_path) > 100:
        try:
            max_q = 0.0
            for event, elem in ET.iterparse(queue_path):
                if elem.tag == 'lane':
                    q_len = float(elem.get('queueing_length', 0))
                    if q_len > max_q:
                        max_q = q_len
                elem.clear()
            metrics['max_queue_m'] = max_q
        except Exception:
            pass

    # 3. Phân tích emission.xml (tổng lượng khí thải CO2)
    if os.path.exists(emission_path) and os.path.getsize(emission_path) > 100:
        try:
            co2_mg = 0.0
            for event, elem in ET.iterparse(emission_path):
                if elem.tag == 'vehicle':
                    co2_mg += float(elem.get('CO2', 0))
                elem.clear()
            metrics['total_co2_g'] = co2_mg / 1000.0
        except Exception:
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
    parser = argparse.ArgumentParser(description="Chạy tự động bộ kịch bản SUMO Ngã tư Hàng Xanh và kiểm tra 5 file đầu ra (Task 5.3)")
    parser.add_argument('--gui', action='store_true', help="Khởi chạy giao diện SUMO-GUI trực quan")
    parser.add_argument('--steps', type=int, default=None, help="Số bước mô phỏng (giây). Mặc định lấy theo file cfg (3600s)")
    parser.add_argument('--scenario', type=str, default='all', choices=['all'] + list(SCENARIOS.keys()), help="Chọn kịch bản cụ thể để chạy")
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    configs_dir = os.path.join(base_dir, 'configs')
    data_dir = os.path.join(base_dir, 'data')
    
    targets = SCENARIOS.keys() if args.scenario == 'all' else [args.scenario]
    
    print("=" * 105)
    print(" HỆ THỐNG MÔ PHỎNG & KIỂM TRA CẤU HÌNH ĐẦU RA (TASK 5.3 - NGÃ TƯ HÀNG XANH)")
    print("=" * 105)
    
    results = {}
    for key in targets:
        info = SCENARIOS[key]
        print(f"\n[BẮT ĐẦU] {info['name']}")
        
        cwd = os.getcwd()
        os.chdir(configs_dir)
        success = run_scenario(info['cfg'], use_gui=args.gui, steps=args.steps)
        os.chdir(cwd)
        
        if success:
            metrics = parse_metrics(data_dir, info)
            results[key] = metrics
            print(f"  + Đã xuất đủ {metrics['files_ok']}/5 file XML (tripinfo, summary, queue, edgedata, emission)")
            print(f"  + Tổng xe: {metrics['completed']} | Vận tốc TB: {metrics['avg_speed_kmh']:.2f} km/h | Chờ TB: {metrics['avg_waiting_time']:.2f} s | Hàng đợi Max: {metrics['max_queue_m']:.1f} m")
        else:
            print("  - Thất bại!")
            
    # In bảng tổng hợp
    print("\n" + "=" * 105)
    print(" BẢNG TỔNG HỢP SO SÁNH HIỆU NĂNG & KHÍ THẢI CÁC KỊCH BẢN (TASK 5.3 KPIs)")
    print("=" * 105)
    header = f"{'Kịch bản':<36} | {'Files':<5} | {'Tổng xe':<7} | {'Vận tốc (km/h)':<14} | {'TG Chờ (s)':<10} | {'Hàng đợi Max (m)':<16} | {'CO2 (g)':<10}"
    print(header)
    print("-" * 105)
    for key in targets:
        if key in results:
            m = results[key]
            name = SCENARIOS[key]['name']
            row = f"{name:<36} | {m['files_ok']}/5   | {m['completed']:<7} | {m['avg_speed_kmh']:<14.2f} | {m['avg_waiting_time']:<10.2f} | {m['max_queue_m']:<16.1f} | {m['total_co2_g']:<10.1f}"
            print(row)
    print("=" * 105)
    print(f"\nToàn bộ file đầu ra XML đã được lưu tại: {data_dir}")

if __name__ == '__main__':
    main()
