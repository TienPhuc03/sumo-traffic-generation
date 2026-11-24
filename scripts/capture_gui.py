"""
capture_gui.py (Task 6.3)
Mở SUMO-GUI qua TraCI, chạy tới các mốc thời gian và chụp khung nhìn vào
docs/figures/<kịch_bản>_t<giây>.png (vd. peak_t600.png).

Không ghi đè data/: mọi file đầu ra mô phỏng ghi vào thư mục tạm (xóa sau khi chụp), và bỏ
routes/detectors.add.xml vì file này ghi cố định vào data/detector_output.xml. Detector E1 chỉ đo,
không ảnh hưởng chuyển động xe (đèn cảm ứng của tls_actuated tự tạo detector riêng).
Cần màn hình (SUMO-GUI mở cửa sổ), không chạy được ở chế độ headless.

Cách dùng:
    python scripts/capture_gui.py                                       # peak + tls_optimized, t = 600 s và 1800 s
    python scripts/capture_gui.py --scenarios peak congestion --times 600 1200 1800
    python scripts/capture_gui.py --zoom 1200 --center 985 740 --tag can_canh_tn   # cận cảnh nhánh tây nam
"""
import argparse
import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

import traci

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DIR = os.path.join(ROOT, 'configs')
FIG_DIR = os.path.join(ROOT, 'docs', 'figures')
SCENARIOS = ['offpeak', 'baseline', 'peak', 'congestion', 'tls_optimized', 'tls_actuated']


def find_sumo_gui():
    exe = shutil.which('sumo-gui')
    if exe:
        return exe
    home = os.environ.get('SUMO_HOME')
    for c in ([os.path.join(home, 'bin', 'sumo-gui.exe')] if home else []) + [r'C:\Program Files (x86)\SUMO\bin\sumo-gui.exe']:
        if os.path.exists(c):
            return c
    sys.exit('LỖI: không tìm thấy sumo-gui. Đặt SUMO_HOME hoặc thêm SUMO\\bin vào PATH.')


def additional_without_detectors(cfg_path):
    """additional-files của cfg (đường dẫn tuyệt đối), bỏ detectors.add.xml."""
    v = ET.parse(cfg_path).getroot().find('input/additional-files').get('value')
    return ','.join(os.path.normpath(os.path.join(CFG_DIR, p)) for p in v.split(',') if 'detectors.add.xml' not in p)


def view_xml_viewport():
    """(x, y, zoom) của <viewport> trong configs/view.xml."""
    v = ET.parse(os.path.join(CFG_DIR, 'view.xml')).getroot().find('viewport')
    return float(v.get('x')), float(v.get('y')), float(v.get('zoom'))


def capture(gui, scenario, times, zoom, size, center=None, tag=''):
    cfg = os.path.join(CFG_DIR, f'scenario_{scenario}.sumocfg')
    tmp = tempfile.mkdtemp(prefix='sumo_gui_')
    cmd = [gui, '-c', cfg, '--start', '--quit-on-end', '--delay', '0', '--no-warnings', 'true',
           '--additional-files', additional_without_detectors(cfg), '--end', str(max(times) + 1),
           '--window-size', f'{size[0]},{size[1]}']
    for kind in ('tripinfo', 'summary', 'queue', 'edgedata', 'emission'):
        cmd += [f'--{kind}-output', os.path.join(tmp, f'{kind}.xml')]
    traci.start(cmd)
    try:
        view = traci.gui.DEFAULT_VIEW
        x, y, z = view_xml_viewport()
        if center:
            x, y = center
        for t in sorted(times):
            traci.simulationStep(t)
            # Đặt lại tâm + zoom trước mỗi ảnh để mọi kịch bản cùng khung (GUI có thể tự đổi góc nhìn)
            traci.gui.setOffset(view, x, y)
            traci.gui.setZoom(view, zoom or z)
            out = os.path.join(FIG_DIR, f'{scenario}_t{t}{"_" + tag if tag else ""}.png')
            traci.gui.screenshot(view, out, size[0], size[1])
            traci.simulationStep()  # SUMO ghi ảnh ở cuối bước kế tiếp
            print(f'[{scenario}] t={t}s, {traci.vehicle.getIDCount()} xe trên mạng -> {out}', flush=True)
    finally:
        traci.close()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description='Chụp ảnh SUMO-GUI tự động (Task 6.3)')
    ap.add_argument('--scenarios', nargs='+', default=['peak', 'tls_optimized'], choices=SCENARIOS)
    ap.add_argument('--times', nargs='+', type=int, default=[600, 1800], help='Mốc thời gian (s), < 3600')
    ap.add_argument('--zoom', type=float, default=None, help='Zoom (%%). Mặc định lấy từ configs/view.xml (650)')
    ap.add_argument('--size', nargs=2, type=int, default=[1600, 1000], metavar=('W', 'H'))
    ap.add_argument('--center', nargs=2, type=float, default=None, metavar=('X', 'Y'),
                    help='Tâm khung nhìn (m, tọa độ mạng). Mặc định lấy từ configs/view.xml (1070 800)')
    ap.add_argument('--tag', default='', help='Hậu tố tên file, vd. can_canh_tn -> peak_t600_can_canh_tn.png')
    a = ap.parse_args()
    if not all(0 < t < 3600 for t in a.times):
        sys.exit('LỖI: --times phải nằm trong (0, 3600).')
    if (a.zoom or a.center) and not a.tag:
        sys.exit('LỖI: đổi --zoom/--center thì phải có --tag, để không ghi đè ảnh tổng quan cùng tên.')
    os.makedirs(FIG_DIR, exist_ok=True)
    gui = find_sumo_gui()
    for sc in a.scenarios:
        capture(gui, sc, a.times, a.zoom, a.size, a.center, a.tag)
    print('Xong. Ảnh tại', FIG_DIR)


if __name__ == '__main__':
    main()
