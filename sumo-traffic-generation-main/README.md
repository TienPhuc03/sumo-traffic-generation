# MÔ PHỎNG VÀ ĐIỀU KHIỂN DÒNG GIAO THÔNG VỚI SUMO

Dự án mô phỏng giao thông sử dụng Eclipse SUMO (Simulation of Urban MObility) và Python (TraCI / sumolib).

---

## 📁 Cấu trúc thư mục dự án

```text
sumo_traffic_project/
├── configs/          # Chứa file cấu hình mô phỏng (.sumocfg, .view.xml)
├── networks/         # Chứa file mạng lưới đường (OSM, .net.xml)
├── routes/           # Chứa file lịch trình và lộ trình xe (.rou.xml, trips.xml)
├── scripts/          # Code Python điều khiển mô phỏng qua TraCI và trích xuất dữ liệu
├── data/             # Dữ liệu xuất ra từ mô phỏng (.csv, .xml)
├── notebooks/        # Jupyter Notebook phân tích thông số dòng giao thông và trực quan hóa
├── .gitignore        # Các tệp và thư mục loại trừ khi đẩy lên Git
├── requirements.txt  # Danh sách thư viện Python cần thiết
└── README.md         # Tài liệu hướng dẫn dự án
```

---

## 📖 Mô tả chi tiết các thư mục

| Thư mục / Tệp tin | Chức năng | Định dạng tệp chính |
| :--- | :--- | :--- |
| **`configs/`** | Cấu hình chạy mô phỏng chính của SUMO | `.sumocfg`, `.view.xml` |
| **`networks/`** | Mạng lưới giao thông, nút giao cắt, làn đường | `.osm`, `.net.xml` |
| **`routes/`** | Định nghĩa phương tiện, lưu lượng dòng xe, lộ trình di chuyển | `.rou.xml`, `trips.xml` |
| **`scripts/`** | Mã nguồn Python kết nối TraCI để điều khiển đèn tín hiệu, xe, trích xuất dữ liệu | `.py` |
| **`data/`** | Kết quả thu thập được sau khi chạy mô phỏng (vận tốc, mật độ, thời gian chờ...) | `.csv`, `.xml` |
| **`notebooks/`** | Notebook phục vụ vẽ đồ thị, xử lý số liệu và phân tích giao thông | `.ipynb` |
| **`requirements.txt`** | Danh sách thư viện Python (`traci`, `sumolib`, `pandas`, `matplotlib`,...) | `.txt` |

---

## 🚀 Hướng dẫn bắt đầu

### 1. Kích hoạt môi trường ảo Python
Nếu đã có môi trường ảo `venv` trong thư mục dự án:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Cài đặt các thư viện phụ thuộc
```powershell
pip install -r requirements.txt
```

### 3. Kiểm tra biến môi trường SUMO_HOME
Đảm bảo biến môi trường `SUMO_HOME` đã được trỏ đến thư mục cài đặt SUMO trên máy:
```powershell
$env:SUMO_HOME
```
