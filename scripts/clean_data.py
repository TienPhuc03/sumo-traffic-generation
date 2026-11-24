import argparse
import os
import sys
import xml.etree.ElementTree as ET
import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s.encoding != 'utf-8':
        try:
            _s.reconfigure(encoding='utf-8')
        except Exception:
            pass


def _ensure_parent_dir(file_path):
    """Tạo thư mục cha nếu đường dẫn có chứa thư mục."""
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)


def create_mock_cleaned_data(output_csv="data/detector_output_cleaned.csv"):
    """
    Tạo dữ liệu mẫu chuẩn cho detector (phục vụ kiểm thử Task 8.1 - Fundamental Diagram).
    """
    print("Đang tạo dữ liệu mẫu chuẩn cho detector...")
    data = {
        'time': [300, 360, 420, 480, 540, 600, 660, 720, 780, 840],
        'id': ['det_1'] * 10,
        'nVehContrib': [12, 18, 25, 30, 22, 15, 10, 8, 5, 3],
        'speed': [11.5, 10.2, 8.5, 6.2, 7.8, 10.1, 12.0, 12.5, 13.0, 13.5]
    }
    df = pd.DataFrame(data)
    _ensure_parent_dir(output_csv)
    df.to_csv(output_csv, index=False)
    print(f"Đã tạo xong file CSV mẫu tại: {output_csv} (Tổng số dòng: {len(df)})")
    return df


def clean_xml_detector_data(xml_file, output_csv, warm_up_time=0, fallback_to_mock=False):
    """
    Đọc, lọc thời gian khởi động (warm-up) và làm sạch dữ liệu detector từ XML của SUMO (Task 7.2).
    Xuất ra file CSV chuẩn gồm 4 cột: time, id, nVehContrib, speed để tương thích với Task 8.1.
    Thiếu file hoặc file rỗng -> dừng chương trình (không tự sinh dữ liệu giả),
    trừ khi gọi rõ fallback_to_mock=True.
    """
    print(f"Đang đọc và phân tích file XML từ: {xml_file}")

    if not os.path.exists(xml_file):
        if fallback_to_mock:
            print(f"Cảnh báo: Không tìm thấy file {xml_file}. Dùng dữ liệu mẫu theo yêu cầu.")
            return create_mock_cleaned_data(output_csv)
        sys.exit(f"LỖI: Không tìm thấy file detector {xml_file}. Hãy chạy mô phỏng trước "
                 f"(hoặc dùng --mock nếu cố ý muốn dữ liệu mẫu).")

    tree = ET.parse(xml_file)
    root = tree.getroot()

    data_list = []

    # Chỉ quét các thẻ bản ghi dữ liệu thực (interval, timestep), tránh quét nhầm thẻ gốc <detector>
    for elem in root.iter():
        if elem.tag in ['interval', 'timestep']:
            begin = float(elem.get('begin', elem.get('time', 0)))
            if begin >= warm_up_time:
                row_data = {
                    'time': begin,
                    'id': elem.get('id', ''),
                    'nVehContrib': int(float(elem.get('nVehContrib', elem.get('sampledSeconds', 0)))),
                    'speed': float(elem.get('speed', elem.get('meanSpeed', 0.0)))
                }
                data_list.append(row_data)

    # Nếu XML dùng cấu trúc thẻ con khác, thử quét các phần tử con cấp 1
    if not data_list:
        for child in root:
            begin = float(child.get('begin', child.get('time', 0)))
            if begin >= warm_up_time:
                data_list.append({
                    'time': begin,
                    'id': child.get('id', 'unknown'),
                    'nVehContrib': int(float(child.get('nVehContrib', 0))),
                    'speed': float(child.get('speed', 0.0))
                })

    df = pd.DataFrame(data_list)

    if df.empty:
        if fallback_to_mock:
            print("File XML trống. Dùng dữ liệu mẫu theo yêu cầu.")
            return create_mock_cleaned_data(output_csv)
        sys.exit(f"LỖI: File {xml_file} không có bản ghi detector nào (sau warm-up={warm_up_time}s).")

    # Làm sạch giá trị thiếu và tốc độ âm (-1.00 trong SUMO khi không có xe qua detector)
    df = df.fillna(0)
    df.loc[df['speed'] < 0, 'speed'] = 0.0

    _ensure_parent_dir(output_csv)
    df.to_csv(output_csv, index=False)

    print(f"Làm sạch thành công! File lưu tại: {output_csv}")
    print(f"Tổng số dòng dữ liệu sạch: {len(df)}")
    return df


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_xml = os.path.join(base_dir, "data", "detector_output.xml")
    default_csv = os.path.join(base_dir, "data", "detector_output_cleaned.csv")

    parser = argparse.ArgumentParser(description="Làm sạch dữ liệu detector SUMO (Task 7.2) hoặc tạo dữ liệu mẫu (Task 8.1)")
    parser.add_argument("--input", default=default_xml, help="Đường dẫn file detector XML đầu vào")
    parser.add_argument("--output", default=default_csv, help="Đường dẫn file CSV đầu ra")
    parser.add_argument("--warmup", type=float, default=0, help="Thời gian warm-up cần loại bỏ (giây)")
    parser.add_argument("--mock", action="store_true", help="Tạo dữ liệu mẫu (mock) thay vì đọc từ XML")
    args = parser.parse_args()

    if args.mock:
        create_mock_cleaned_data(args.output)
    else:
        clean_xml_detector_data(args.input, args.output, warm_up_time=args.warmup)
