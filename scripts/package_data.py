"""
package_data.py (Task 7.4)
Đóng gói bộ dữ liệu giao nộp: copy data/csv/*.csv sang release/ và tạo release/manifest.csv
(tên file, dung lượng, sha256, số dòng dữ liệu, số cột). Sau đó kiểm tra mọi cột của từng CSV
đều được mô tả trong release/README.md (dạng `tên_cột`).

Cách dùng:
    python scripts/package_data.py
    python scripts/package_data.py --src data/csv --dst release
"""
import argparse
import csv
import glob
import hashlib
import os
import shutil
import sys

for _s in (sys.stdout, sys.stderr):
    if _s.encoding != 'utf-8':
        try:
            _s.reconfigure(encoding='utf-8')
        except Exception:
            pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def shape(path):
    """(số dòng dữ liệu không tính header, danh sách cột)."""
    with open(path, newline='', encoding='utf-8-sig') as f:
        r = csv.reader(f)
        cols = next(r)
        return sum(1 for _ in r), cols


def main():
    ap = argparse.ArgumentParser(description='Đóng gói CSV + manifest (Task 7.4)')
    ap.add_argument('--src', default=os.path.join(ROOT, 'data', 'csv'))
    ap.add_argument('--dst', default=os.path.join(ROOT, 'release'))
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.src, '*.csv')))
    if not files:
        sys.exit(f'LỖI: không có CSV trong {a.src}. Chạy xml_to_csv.py và aggregate_intervals.py trước.')
    os.makedirs(a.dst, exist_ok=True)

    rows, columns = [], {}
    for src in files:
        name = os.path.basename(src)
        dst = os.path.join(a.dst, name)
        shutil.copy2(src, dst)
        digest = sha256(dst)
        if digest != sha256(src):
            sys.exit(f'LỖI: sha256 bản copy {name} khác bản gốc.')
        n, cols = shape(dst)
        columns[name] = cols
        rows.append({'file': name, 'size_bytes': os.path.getsize(dst), 'sha256': digest, 'rows': n, 'cols': len(cols)})
        print(f'{name:<24} {os.path.getsize(dst) / 1e6:>9.1f} MB  {n:>9} dòng  {len(cols):>3} cột')

    with open(os.path.join(a.dst, 'manifest.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['file', 'size_bytes', 'sha256', 'rows', 'cols'])
        w.writeheader()
        w.writerows(rows)
    print(f'-> {os.path.join(a.dst, "manifest.csv")}')

    readme = os.path.join(a.dst, 'README.md')
    if not os.path.exists(readme):
        print('CẢNH BÁO: chưa có release/README.md để kiểm tra từ điển dữ liệu.')
        return
    text = open(readme, encoding='utf-8').read()
    missing = {n: [c for c in cols if f'`{c}`' not in text] for n, cols in columns.items()}
    missing = {n: m for n, m in missing.items() if m}
    if missing:
        for n, m in missing.items():
            print(f'THIẾU trong README ({n}): {", ".join(m)}')
        sys.exit(1)
    print('README mô tả đủ mọi cột của mọi CSV.')


if __name__ == '__main__':
    main()
