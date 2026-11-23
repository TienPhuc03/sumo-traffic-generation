"""
fix_network.py (Task 6.1)
Sửa lỗi mạng lưới networks/hangxanh.net.xml:
1. Loại bỏ 2 khối <tlLogic> sai ID (thiếu '_9415490897_') và programID='1' trùng lặp tại 1497276515.
2. Chuyển nút 1497276515 trên vòng xoay sang chế độ ưu tiên vòng xoay liên tục (gggGGGG: dòng trong
   vòng xoay luôn đi thẳng, nhánh Xô Viết Nghệ Tĩnh nhập vòng theo quy tắc nhường đường).
3. Vá kết nối qua netconvert: mở thoát đa làn cho 4 nhánh ra vòng xoay và nối làn cụt 192512365#3_5.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET_PATH = os.path.join(ROOT, 'networks', 'hangxanh.net.xml')
DET_PATH = os.path.join(ROOT, 'routes', 'detectors.add.xml')

CON_PATCH = """<connections>
    <delete from="1265700924" to="231982479#0" fromLane="0" toLane="1"/>
    <connection from="1265700924" to="231982479#0" fromLane="1" toLane="1"/>

    <delete from="977346734" to="1278461430" fromLane="0" toLane="2"/>
    <delete from="977346734" to="1278461430" fromLane="0" toLane="3"/>
    <delete from="977346734" to="1278461430" fromLane="0" toLane="4"/>
    <connection from="977346734" to="1278461430" fromLane="1" toLane="2"/>
    <connection from="977346734" to="1278461430" fromLane="2" toLane="3"/>
    <connection from="977346734" to="1278461430" fromLane="3" toLane="4"/>

    <delete from="1265471308" to="977523911#0" fromLane="0" toLane="1"/>
    <connection from="1265471308" to="977523911#0" fromLane="1" toLane="1"/>

    <delete from="1265700913" to="192512353#0" fromLane="0" toLane="1"/>
    <delete from="1265700913" to="192512353#0" fromLane="0" toLane="2"/>
    <delete from="1265700913" to="192512353#0" fromLane="0" toLane="3"/>
    <connection from="1265700913" to="192512353#0" fromLane="1" toLane="1"/>
    <connection from="1265700913" to="192512353#0" fromLane="2" toLane="2"/>
    <connection from="1265700913" to="192512353#0" fromLane="3" toLane="3"/>

    <!-- Nối làn 5 của 192512365#3 (tránh cụt làn gây kẹt) -->
    <connection from="192512365#3" to="192512383#0" fromLane="5" toLane="3"/>
</connections>
"""


def find_netconvert():
    exe = shutil.which('netconvert')
    if exe:
        return exe
    home = os.environ.get('SUMO_HOME')
    cands = [os.path.join(home, 'bin', 'netconvert.exe')] if home else []
    cands.append(r'C:\Program Files (x86)\SUMO\bin\netconvert.exe')
    for c in cands:
        if os.path.exists(c):
            return c
    sys.exit('Không tìm thấy netconvert.')


def main():
    netconvert = find_netconvert()
    tmp = tempfile.mkdtemp(prefix='hx_netfix_')
    try:
        tree = ET.parse(NET_PATH)
        root = tree.getroot()
        for tl in list(root.findall('tlLogic')):
            if tl.get('id') == 'joinedS_4066386148_9415490893_9415490903_#3more':
                root.remove(tl)
            elif tl.get('id') == '1497276515' and tl.get('programID') == '1':
                root.remove(tl)
            elif tl.get('id') == '1497276515' and tl.get('programID') == '0':
                for ph in list(tl.findall('phase')):
                    tl.remove(ph)
                ET.SubElement(tl, 'phase', {'duration': '60', 'state': 'gggGGGG'})

        clean_net = os.path.join(tmp, 'clean.net.xml')
        con_file = os.path.join(tmp, 'fix.con.xml')
        tree.write(clean_net, encoding='utf-8', xml_declaration=True)
        with open(con_file, 'w', encoding='utf-8') as f:
            f.write(CON_PATCH)

        res = subprocess.run([netconvert, '-s', clean_net, '-x', con_file, '-o', NET_PATH],
                             capture_output=True, text=True)
        if res.returncode != 0:
            print(res.stderr)
            sys.exit(res.returncode)

        # Kiểm tra sau hiệu chỉnh
        fixed = ET.parse(NET_PATH).getroot()
        lanes = {l.get('id') for l in fixed.iter('lane')}
        det = ET.parse(DET_PATH).getroot()
        det_lanes = [d.get('lane') for d in det.findall('inductionLoop')]
        missing = [l for l in det_lanes if l not in lanes]
        if missing:
            sys.exit(f'Thiếu làn detector sau netconvert: {missing}')

        tls_list = [(t.get('id'), t.get('programID'),
                     [(p.get('duration'), p.get('state')) for p in t.findall('phase')])
                    for t in fixed.findall('tlLogic')]
        print(f'netconvert exit=0 | Kiểm tra {len(det_lanes)}/{len(det_lanes)} làn detector OK')
        for tid, pid, phs in tls_list:
            print(f'  TLS {tid} (programID={pid}): phases={phs}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
