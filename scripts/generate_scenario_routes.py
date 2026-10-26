"""
generate_scenario_routes.py
Tạo các tệp kịch bản lộ trình (routes) cho mô phỏng Ngã tư Hàng Xanh
Phân bổ theo tỉ lệ phương tiện đặc trưng Việt Nam:
- Xe máy (moped): 75%
- Ô tô con (passenger): 18%
- Xe buýt (bus): 4%
- Xe tải (truck): 3%
"""

import os
import sys
import random
import xml.etree.ElementTree as ET

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def extract_unique_routes(source_file):
    print(f"Đang đọc lộ trình mẫu từ {source_file}...")
    unique_routes = set()
    for event, elem in ET.iterparse(source_file):
        if elem.tag == 'vehicle':
            r = elem.find('route')
            if r is not None and r.get('edges'):
                unique_routes.add(r.get('edges'))
            elem.clear()
    routes_list = list(unique_routes)
    print(f"-> Thu thập được {len(routes_list)} lộ trình duy nhất hợp lệ qua mạng lưới.")
    return routes_list

def generate_route_file(output_file, routes_pool, total_vehicles, sim_duration=3600, seed=42):
    random.seed(seed)
    
    # Tỉ lệ phân bổ phương tiện tại đô thị Việt Nam
    vtypes = ['moped', 'passenger', 'bus', 'truck']
    weights = [0.75, 0.18, 0.04, 0.03]
    
    # Sinh thời điểm xuất phát (depart times)
    # Phân bố đều ngẫu nhiên trong khoảng [0, sim_duration]
    depart_times = sorted([round(random.uniform(0.0, sim_duration - 1.0), 2) for _ in range(total_vehicles)])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!-- Generated for ITS SUMO Project - Hàng Xanh Junction -->\n')
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        
        for i, depart in enumerate(depart_times):
            v_type = random.choices(vtypes, weights=weights)[0]
            edge_path = random.choice(routes_pool)
            f.write(f'    <vehicle id="veh_{i}" type="{v_type}" depart="{depart:.2f}">\n')
            f.write(f'        <route edges="{edge_path}"/>\n')
            f.write(f'    </vehicle>\n')
            
        f.write('</routes>\n')
    print(f"-> Đã tạo {output_file} ({total_vehicles} xe, thời lượng {sim_duration}s)")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_route_file = os.path.join(base_dir, 'routes', 'route.rou.xml')
    routes_dir = os.path.join(base_dir, 'routes')
    
    routes_pool = extract_unique_routes(source_route_file)
    
    scenarios = [
        ('routes_offpeak.rou.xml', 1200, 101),       # Giờ thấp điểm: 1200 xe/h
        ('routes_baseline.rou.xml', 2500, 202),      # Tiêu chuẩn / Baseline: 2500 xe/h
        ('routes_peak.rou.xml', 4500, 303),          # Giờ cao điểm: 4500 xe/h
        ('routes_congestion.rou.xml', 6000, 404),    # Ùn tắc quá tải: 6000 xe/h
    ]
    
    for filename, count, seed in scenarios:
        out_path = os.path.join(routes_dir, filename)
        generate_route_file(out_path, routes_pool, total_vehicles=count, sim_duration=3600, seed=seed)

if __name__ == '__main__':
    main()
