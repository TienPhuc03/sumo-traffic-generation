"""
annotate_figures.py (Task 6.3)
Gắn nhãn cho ảnh SUMO-GUI trong docs/figures/: thêm dải thông tin PHÍA TRÊN ảnh (không vẽ đè bản đồ)
gồm tên kịch bản, thời điểm t, số xe toàn mạng lấy từ data/summary_<kịch_bản>.xml, ghi chú seed,
và chú giải màu xe theo routes/vtypes.add.xml. Ảnh gốc giữ nguyên; ảnh có nhãn ghi vào
docs/figures/annotated/ cùng tên.

Tên ảnh phải theo mẫu <kịch_bản>_t<giây>[_<tag>].png (do capture_gui.py tạo). Ảnh khác tên bị bỏ qua.
Số xe là của TOÀN MẠNG tại mốc t trong summary (1 lần chạy, seed mặc định SUMO, chu kỳ 60 s),
không phải số xe nhìn thấy trong khung ảnh.

Cách dùng:
    python scripts/annotate_figures.py
    python scripts/annotate_figures.py --selftest
"""
import argparse
import glob
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

import matplotlib
from PIL import Image, ImageDraw, ImageFont

for _s in (sys.stdout, sys.stderr):
    if _s.encoding != 'utf-8':
        try:
            _s.reconfigure(encoding='utf-8')
        except Exception:
            pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(ROOT, 'docs', 'figures')
OUT_DIR = os.path.join(FIG_DIR, 'annotated')
DATA_DIR = os.path.join(ROOT, 'data')
FONT_DIR = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf')  # DejaVu Sans có đủ dấu tiếng Việt

SCENARIOS = {
    'offpeak': 'Thấp điểm (~1.200 xe/h)',
    'baseline': 'Tiêu chuẩn (~2.500 xe/h)',
    'peak': 'Cao điểm (~4.500 xe/h)',
    'congestion': 'Ùn tắc (~6.000 xe/h)',
    'tls_optimized': 'Tối ưu đèn (demand cao điểm)',
    'tls_actuated': 'Đèn cảm ứng (demand cao điểm)',
}
TAGS = {'can_canh_tn': 'Cận cảnh nhánh tây nam'}
LEGEND = [('Xe máy', (255, 0, 0)), ('Ô tô con', (0, 255, 0)), ('Xe buýt', (0, 0, 255)), ('Xe tải', (255, 255, 0))]
NAME_RE = re.compile(r'^(' + '|'.join(SCENARIOS) + r')_t(\d+)(?:_(.+))?\.png$')


def summary_at(scenario, t):
    """(running, halting) tại time = t trong data/summary_<kịch_bản>.xml."""
    path = os.path.join(DATA_DIR, f'summary_{scenario}.xml')
    for _, el in ET.iterparse(path):
        if el.tag == 'step':
            if float(el.get('time')) == t:
                return int(el.get('running')), int(el.get('halting'))
            el.clear()
    sys.exit(f'LỖI: {path} không có mốc time={t} (summary ghi mỗi 60 s). Chụp lại ở mốc chia hết cho 60.')


def font(size, bold=False):
    return ImageFont.truetype(os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'), size)


def fitted(draw, text, size, max_w, bold=False):
    """Font lớn nhất <= size sao cho text vừa max_w."""
    while size > 8 and draw.textlength(text, font=font(size, bold)) > max_w:
        size -= 1
    return font(size, bold)


def annotate(src, dst):
    m = NAME_RE.match(os.path.basename(src))
    if not m:
        return None
    sc, t, tag = m.group(1), int(m.group(2)), m.group(3)
    running, halting = summary_at(sc, t)
    img = Image.open(src).convert('RGB')
    w, h = img.size
    s = w / 1600
    pad, band = int(20 * s), int(150 * s)
    out = Image.new('RGB', (w, h + band), 'white')
    out.paste(img, (0, band))
    d = ImageDraw.Draw(out)
    max_w = w - 2 * pad

    title = f'{SCENARIOS[sc]}  |  t = {t} s' + (f'  |  {TAGS.get(tag, tag)}' if tag else '')
    info = (f'Toàn mạng: {running} xe đang chạy, {halting} xe đang dừng (data/summary_{sc}.xml)  ·  '
            f'SUMO-GUI, 1 lần chạy, seed mặc định')
    d.text((pad, pad), title, font=fitted(d, title, int(34 * s), max_w, bold=True), fill=(30, 30, 30))
    d.text((pad, pad + int(48 * s)), info, font=fitted(d, info, int(22 * s), max_w), fill=(70, 70, 70))

    f, sw, x, y = font(int(22 * s)), int(22 * s), pad, pad + int(88 * s)
    d.text((x, y), 'Màu xe:', font=f, fill=(70, 70, 70))
    x += int(d.textlength('Màu xe:', font=f)) + int(16 * s)
    for name, color in LEGEND:
        d.rectangle([x, y + 2, x + sw, y + 2 + sw], fill=color, outline=(40, 40, 40))
        x += sw + int(8 * s)
        d.text((x, y), name, font=f, fill=(30, 30, 30))
        x += int(d.textlength(name, font=f)) + int(28 * s)
    d.line([0, band - 1, w, band - 1], fill=(180, 180, 180), width=max(1, int(2 * s)))
    out.save(dst)
    return sc, t, tag, running, halting


def selftest():
    """Kiểm tra parse tên file, tra summary và kích thước ảnh ra."""
    assert NAME_RE.match('tls_optimized_t1800_can_canh_tn.png').groups() == ('tls_optimized', '1800', 'can_canh_tn')
    assert NAME_RE.match('peak_t600.png').groups() == ('peak', '600', None)
    assert NAME_RE.match('ghi_chu.png') is None
    assert summary_at('peak', 600) == (184, 60)
    assert summary_at('tls_optimized', 1800) == (162, 23)
    src = os.path.join(FIG_DIR, 'peak_t600.png')
    if os.path.exists(src):
        dst = os.path.join(tempfile.mkdtemp(), 'peak_t600.png')
        r = annotate(src, dst)
        w, h = Image.open(src).size
        assert r == ('peak', 600, None, 184, 60) and Image.open(dst).size == (w, h + int(150 * w / 1600))
    print('SELFTEST OK')


def main():
    ap = argparse.ArgumentParser(description='Gắn nhãn ảnh SUMO-GUI (Task 6.3)')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    files = sorted(glob.glob(os.path.join(FIG_DIR, '*.png')))
    if not files:
        sys.exit(f'LỖI: không có ảnh trong {FIG_DIR}. Chạy capture_gui.py trước.')
    os.makedirs(OUT_DIR, exist_ok=True)
    for src in files:
        r = annotate(src, os.path.join(OUT_DIR, os.path.basename(src)))
        if r is None:
            print(f'BỎ QUA (tên không theo mẫu <kịch_bản>_t<giây>[_<tag>].png): {os.path.basename(src)}')
        else:
            print(f'{os.path.basename(src):<40} running={r[3]:>4} halting={r[4]:>4}')
    print('-> Ảnh có nhãn tại', OUT_DIR)


if __name__ == '__main__':
    main()
