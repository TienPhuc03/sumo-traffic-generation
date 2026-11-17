import pandas as pd
import os

def create_mock_cleaned_data(output_csv):
    print("Đang tạo dữ liệu mẫu chuẩn cho detector...")
    data = {
        'time': [300, 360, 420, 480, 540, 600, 660, 720, 780, 840],
        'id': ['det_1']*10,
        'nVehContrib': [12, 18, 25, 30, 22, 15, 10, 8, 5, 3],
        'speed': [11.5, 10.2, 8.5, 6.2, 7.8, 10.1, 12.0, 12.5, 13.0, 13.5]
    }
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Đã tạo xong file CSV tại: {output_csv} (Tổng số dòng: {len(df)})")

# ĐOẠN NÀY LÀ QUAN TRỌNG ĐỂ KÍCH HOẠT CODE CHẠY:
if __name__ == "__main__":
    create_mock_cleaned_data("data/detector_output_cleaned.csv")