"""
xml_to_csv.py (Task 7.1)
Chuyển các file XML đầu ra của SUMO (data/raw/<kịch_bản>/seed_<n>/*.xml) thành
các bảng CSV dạng "dài", mỗi loại một file, có thêm cột `scenario` và `seed`:

    data/csv/tripinfo.csv      (mỗi hàng = 1 chuyến xe, kèm khí thải cả chuyến)
    data/csv/summary.csv       (mỗi hàng = 1 bước 60s toàn mạng)
    data/csv/queue.csv         (mỗi hàng = 1 làn tại 1 thời điểm có hàng đợi)
    data/csv/edgedata.csv      (mỗi hàng = 1 edge, thống kê cả mô phỏng)
    data/csv/emission.csv      (mỗi hàng = 1 xe tại 1 thời điểm lấy mẫu 60s)
    data/csv/detector.csv      (mỗi hàng = 1 vòng cảm ứng E1 / 900s)

Cách dùng:
    python scripts/xml_to_csv.py
    python scripts/xml_to_csv.py --raw data/raw --out data/csv
"""
import argparse
import csv
import os
import sys
import xml.etree.ElementTree as ET

for _s in (sys.stdout, sys.stderr):
    if _s.encoding != 'utf-8':
        try:
            _s.reconfigure(encoding='utf-8')
        except Exception:
            pass

ROOT =os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS = ['offpeak', 'baseline', 'peak', 'congestion', 'tls_optimized', 'tls_actuated']


def rows_tripinfo(path):
    for _, el in ET.iterparse(path, events=('end',)):
        if el.tag == 'tripinfo':
            r = dict(el.attrib)
            em = el.find('emissions')
            if em is not None:
                r.update(em.attrib)
            r.pop('devices', None)
            yield r
            el.clear()


def rows_summary(path):
    for _, el in ET.iterparse(path, events=('end',)):
        if el.tag == 'step':
            yield dict(el.attrib)
            el.clear()


def rows_queue(path):
    for _, data in ET.iterparse(path, events=('end',)):
        if data.tag == 'data':
            t = data.get('timestep')
            for lane in data.iter('lane'):
                r = {'timestep': t}
                r.update(lane.attrib)
                yield r
            data.clear()


def rows_edgedata(path):
    for _, itv in ET.iterparse(path, events=('end',)):
        if itv.tag == 'interval':
            for e in itv.iter('edge'):
                r = {'begin': itv.get('begin'), 'end': itv.get('end')}
                r.update(e.attrib)
                yield r
            itv.clear()


def rows_emission(path):
    for _, ts in ET.iterparse(path, events=('end',)):
        if ts.tag == 'timestep':
            t = ts.get('time')
            for v in ts.iter('vehicle'):
                r = {'time': t}
                r.update(v.attrib)
                yield r
            ts.clear()


def rows_detector(path):
    for _, el in ET.iterparse(path, events=('end',)):
        if el.tag == 'interval':
            yield dict(el.attrib)
            el.clear()


KINDS = {
    'tripinfo': ('tripinfo.xml', rows_tripinfo),
    'summary': ('summary.xml', rows_summary),
    'queue': ('queue.xml', rows_queue),
    'edgedata': ('edgedata.xml', rows_edgedata),
    'emission': ('emission.xml', rows_emission),
    'detector': ('detector.xml', rows_detector),
}


def convert_kind(kind, raw_dir, out_dir):
    fname, fn = KINDS[kind]
    rows = []
    cols = ['scenario', 'seed']
    for sc in SCENARIOS:
        sc_dir = os.path.join(raw_dir, sc)
        if not os.path.isdir(sc_dir):
            continue
        for sd in sorted(os.listdir(sc_dir)):
            p = os.path.join(sc_dir, sd, fname)
            if not (sd.startswith('seed_') and os.path.exists(p)):
                continue
            seed = int(sd.split('_')[1])
            for r in fn(p):
                r = {'scenario': sc, 'seed': seed, **r}
                for k in r:
                    if k not in cols:
                        cols.append(k)
                rows.append(r)
    out = os.path.join(out_dir, f'{kind}.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, restval='')
        w.writeheader()
        w.writerows(rows)
    print(f'{kind:<9} -> {out}  ({len(rows)} hàng, {len(cols)} cột)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', default=os.path.join(ROOT, 'data', 'raw'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'data', 'csv'))
    a = ap.parse_args()
    if not os.path.isdir(a.raw):
        sys.exit(f'Không thấy thư mục dữ liệu thô: {a.raw} (chạy run_multi_seed.py trước)')
    os.makedirs(a.out, exist_ok=True)
    for kind in KINDS:
        convert_kind(kind, a.raw, a.out)


if __name__ == '__main__':
    main()
