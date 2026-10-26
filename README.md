# MÔ PHỎNG VÀ ĐIỀU KHIỂN DÒNG GIAO THÔNG VỚI SUMO (NGÃ TƯ HÀNG XANH)

Dự án mô phỏng và tối ưu hóa dòng giao thông khu vực Ngã tư Hàng Xanh (Bình Thạnh, TP.HCM) sử dụng **Eclipse SUMO** (Simulation of Urban MObility) và **Python** (TraCI / sumolib).

---

## 📁 Cấu trúc thư mục dự án

```text
sumo_traffic_project/
├── configs/                     # Chứa các kịch bản mô phỏng (.sumocfg) và góc nhìn GUI (.view.xml)
│   ├── scenario_baseline.sumocfg       # Kịch bản tiêu chuẩn / cơ sở (2.500 xe/h)
│   ├── scenario_offpeak.sumocfg        # Kịch bản giờ thấp điểm (1.200 xe/h)
│   ├── scenario_peak.sumocfg           # Kịch bản giờ cao điểm (4.500 xe/h)
│   ├── scenario_congestion.sumocfg     # Kịch bản ùn tắc quá tải (6.000 xe/h)
│   ├── scenario_tls_optimized.sumocfg  # Kịch bản tối ưu chu kỳ đèn cố định
│   ├── scenario_tls_actuated.sumocfg   # Kịch bản đèn cảm ứng thông minh
│   └── view.xml                        # Cấu hình màu sắc xe & tiêu cự camera Ngã tư Hàng Xanh
├── networks/                    # Mạng lưới đường và tệp điều khiển đèn tín hiệu
│   ├── hangxanh.net.xml         # Mạng lưới giao thông Hàng Xanh chuẩn hóa
│   ├── hangxanh.osm             # Dữ liệu OpenStreetMap gốc
│   ├── tls_optimized.add.xml    # Kích hoạt chu kỳ đèn tối ưu (WAUT)
│   └── tls_actuated.add.xml     # Kích hoạt đèn cảm ứng thông minh (WAUT)
├── routes/                      # Dữ liệu phương tiện và lộ trình di chuyển
│   ├── vtypes.add.xml           # Đặc tính xe Việt Nam (Xe máy 75%, Ô tô 18%, Bus 4%, Tải 3%)
│   ├── routes_baseline.rou.xml  # Lộ trình kịch bản tiêu chuẩn
│   ├── routes_offpeak.rou.xml   # Lộ trình kịch bản giờ thấp điểm
│   ├── routes_peak.rou.xml      # Lộ trình kịch bản giờ cao điểm
│   ├── routes_congestion.rou.xml# Lộ trình kịch bản ùn tắc
│   └── route.rou.xml            # Tệp lộ trình mẫu gốc
├── scripts/                     # Mã nguồn Python điều khiển và tự động hóa
│   ├── run_all_scenarios.py     # Script chạy tự động và so sánh KPI các kịch bản
│   ├── generate_scenario_routes.py # Script sinh dữ liệu luồng xe theo tỉ lệ đô thị VN
│   └── test_connection.py      # Kiểm tra kết nối SUMO_HOME và TraCI
├── data/                        # Dữ liệu đầu ra trích xuất từ mô phỏng (Task 5)
│   ├── summary_*.xml            # Thống kê tổng quan mạng lưới theo từng giây
│   ├── tripinfo_*.xml           # Chi tiết từng chuyến đi (vận tốc, độ trễ, thời gian chờ)
│   └── queue_*.xml              # Thống kê chiều dài hàng đợi tại các làn đường
├── notebooks/                   # Jupyter Notebook phân tích & vẽ đồ thị (Task 6)
├── .gitignore                   # Cấu hình bỏ qua venv, cache, file tạm cho Git
├── requirements.txt             # Danh sách thư viện Python cần thiết
└── README.md                    # Tài liệu hướng dẫn dự án
```

---

## 🚦 Chi tiết các Kịch bản Mô phỏng (Task 4.3)

| Kịch bản | Tệp `.sumocfg` | Lưu lượng | Đặc điểm kịch bản |
| :--- | :--- | :--- | :--- |
| **1. Thấp điểm** | `scenario_offpeak.sumocfg` | ~1.200 xe/h | Xe lưu thông tự do, thời gian chờ đèn thấp (~9s), vận tốc trung bình cao. |
| **2. Tiêu chuẩn** | `scenario_baseline.sumocfg` | ~2.500 xe/h | Trạng thái giao thông bình thường làm mốc đối chứng (Benchmark). |
| **3. Cao điểm** | `scenario_peak.sumocfg` | ~4.500 xe/h | Mật độ xe máy và ô tô tăng vọt, xuất hiện hàng đợi dài tại Điện Biên Phủ và Xô Viết Nghệ Tĩnh. |
| **4. Ùn tắc** | `scenario_congestion.sumocfg` | ~6.000 xe/h | Quá tải năng lực thông hành, vận tốc sụt giảm mạnh, tổn thất thời gian tăng vọt. |
| **5. Tối ưu đèn** | `scenario_tls_optimized.sumocfg` | ~4.500 xe/h | Kéo dài thời gian đèn xanh trục Điện Biên Phủ lên 72s nhằm tăng khả năng giải tỏa dòng xe. |
| **6. Đèn thông minh**| `scenario_tls_actuated.sumocfg` | ~4.500 xe/h | Đèn tín hiệu tự động co giãn thời gian pha xanh dựa theo cảm biến mật độ dòng xe thực tế. |

---

## 🚀 Hướng dẫn Chạy Mô phỏng

### 1. Chạy Tự động & So sánh KPI (Khuyên dùng)
Chạy tất cả 6 kịch bản trên terminal để in bảng so sánh hiệu năng:
```powershell
python scripts/run_all_scenarios.py --steps 300
```

Nếu muốn quan sát trực quan trên giao diện **SUMO-GUI**:
```powershell
python scripts/run_all_scenarios.py --scenario peak --gui
```

### 2. Mở trực tiếp từng Kịch bản bằng SUMO-GUI
Từ thư mục `configs/`:
```powershell
cd configs
sumo-gui -c scenario_peak.sumocfg
```

---

## 📊 Liên kết với các Nhiệm vụ tiếp theo của Nhóm
- **Task 5 (Thiết lập thu thập dữ liệu)**: Dữ liệu mô phỏng tự động ghi vào thư mục `data/` với 3 định dạng: `summary_*.xml`, `tripinfo_*.xml`, `queue_*.xml`.
- **Task 6 (Phân tích dòng giao thông)**: Sử dụng Jupyter Notebook trong thư mục `notebooks/` nạp dữ liệu từ `data/` để trực quan hóa đồ thị so sánh giữa các kịch bản.
- **Phân hệ TraCI / AI**: Kết nối điều khiển động thời gian thực với các kịch bản cao điểm và ùn tắc.
