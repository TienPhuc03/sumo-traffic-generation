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
│   ├── hangxanh.sumocfg         # Cấu hình cũ (xem ghi chú bên dưới), không dùng trong pipeline
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
│   ├── run_all_scenarios.py     # Script chạy tự động và so sánh KPI các kịch bản (1 lần chạy, ghi data/*.xml)
│   ├── run_multi_seed.py        # Chạy 6 kịch bản × 5 seed, ghi data/raw/ (Task 6.2)
│   ├── xml_to_csv.py            # data/raw/ -> data/csv/*.csv (Task 7.1)
│   ├── clean_data.py            # Làm sạch detector XML -> CSV (Task 7.2)
│   ├── aggregate_intervals.py   # Gộp theo khoảng thời gian, gán nhãn (Task 7.3)
│   ├── package_data.py          # Đóng gói release/ + manifest sha256 (Task 7.4)
│   ├── reliability_analysis.py  # KPI theo seed và độ tin cậy (Task 8.3)
│   ├── plot_results.py          # Fundamental Diagram + dashboard (Task 8.1, 8.2)
│   ├── capture_gui.py           # Chụp ảnh SUMO-GUI tự động qua TraCI (Task 6.3)
│   ├── annotate_figures.py      # Gắn nhãn + chú giải màu xe lên ảnh -> docs/figures/annotated/
│   ├── generate_scenario_routes.py # Script sinh dữ liệu luồng xe theo tỉ lệ đô thị VN
│   ├── fix_network.py           # ĐÃ CHẠY XONG, KHÔNG chạy lại (ghi đè hangxanh.net.xml)
│   └── test_connection.py      # Kiểm tra kết nối SUMO_HOME và TraCI
├── data/                        # Dữ liệu đầu ra trích xuất từ mô phỏng (Task 5.2 & 5.3)
│   ├── tripinfo_*.xml           # Chi tiết từng chuyến đi (vận tốc, độ trễ, thời gian chờ)
│   ├── summary_*.xml            # Thống kê tổng quan mạng lưới (chu kỳ lấy mẫu 60s)
│   ├── queue_*.xml              # Chiều dài hàng đợi tại các làn đường (chu kỳ lấy mẫu 60s)
│   ├── edgedata_*.xml           # Thống kê mật độ, lưu lượng trên từng đoạn đường (edge)
│   ├── emission_*.xml           # Thông số khí thải CO2, CO, NOx, nhiên liệu (chu kỳ 60s)
│   └── detector_output.xml      # Dữ liệu thu thập từ 12 vòng cảm ứng từ E1 (Task 5.2)
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
| **5. Tối ưu đèn** | `scenario_tls_optimized.sumocfg` | ~4.500 xe/h | Chương trình đèn cố định `optimized` (`networks/tls_optimized.add.xml`) tại 2 nút: nút `joinedS_…` chu kỳ 82 s (xanh 50 s và 26 s, vàng 3 s mỗi pha); nút `cluster_…` chu kỳ 85 s (xanh 14 s, 26 s, 36 s, vàng 3 s mỗi pha). |
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

## 📊 Cấu hình Đầu ra & Chu kỳ Lấy mẫu (Task 5.3)

Tất cả 6 tệp kịch bản `.sumocfg` trong thư mục `configs/` đã được cấu hình đồng bộ 5 loại tệp dữ liệu đầu ra chuẩn XML cùng với hệ thống cảm biến `detectors.add.xml` (Task 5.2):

| Loại Output | Thẻ cấu hình trong `.sumocfg` | Tệp xuất ra (`data/`) | Chu kỳ lấy mẫu | Ý nghĩa thông số |
| :--- | :--- | :--- | :--- | :--- |
| **1. Tripinfo** | `<tripinfo-output>` | `tripinfo_<kịch_bản>.xml` | Theo từng chuyến xe (`write-unfinished="true"`) | Thời gian di chuyển (`duration`), thời gian chờ (`waitingTime`), độ trễ (`timeLoss`), quãng đường (`routeLength`). |
| **2. Summary** | `<summary-output>` | `summary_<kịch_bản>.xml` | **60 giây** (`summary-output.period="60"`) | Tổng số xe đang chạy (`running`), số xe dừng chờ (`halting`), vận tốc trung bình toàn mạng lưới (`meanSpeed`). |
| **3. Queue** | `<queue-output>` | `queue_<kịch_bản>.xml` | **60 giây** (`queue-output.period="60"`) | Chiều dài hàng đợi (`queueing_length`) và thời gian xếp hàng (`queueing_time`) trước các nút giao đèn tín hiệu. |
| **4. EdgeData** | `<edgedata-output>` | `edgedata_<kịch_bản>.xml` | Toàn chu kỳ / 900s (`detectors.add.xml`) | Mật độ (`density`), hệ số chiếm dụng (`occupancy`), lưu lượng (`flow`) và tốc độ trên từng đoạn đường. |
| **5. Emission** | `<emission-output>` | `emission_<kịch_bản>.xml` | **60 giây** (`device.emissions.period="60"`) | Khí thải môi trường (`CO2`, `CO`, `HC`, `NOx`, `PMx`), mức tiêu hao nhiên liệu (`fuel`) và tiếng ồn (`noise`). |

Lưu ý về `detector_output.xml` và `edgedata_output.xml`: đường dẫn hai file này cố định trong `routes/detectors.add.xml`, nên **mỗi lần chạy SUMO đều ghi đè** chúng. Bản trong `data/` chỉ là lần chạy gần nhất. Bản theo từng seed nằm ở `data/raw/<kịch_bản>/seed_<n>/detector.xml` và `edgedata_detector.xml`, do `run_multi_seed.py` copy sang.

---

## 📦 Bộ dữ liệu nhiều seed (Task 6.2, 7.x, 8.x)

Lệnh tái tạo đầy đủ và từ điển dữ liệu: xem [`release/README.md`](release/README.md). Tóm tắt:

```powershell
python scripts\run_multi_seed.py          # data/raw/  (6 kịch bản × 5 seed, summary/queue/emission mỗi 30 s)
python scripts\xml_to_csv.py              # data/csv/*.csv
python scripts\aggregate_intervals.py     # data/csv/aggregated_30s.csv
python scripts\reliability_analysis.py    # data/analysis/
python scripts\plot_results.py            # data/traffic_fundamental_diagram.png, data/traffic_comparison_dashboard.png
python scripts\package_data.py            # release/*.csv + manifest.csv
```

Số liệu trong `notebooks/traffic_analysis.ipynb` là **1 lần chạy mỗi kịch bản** (`data/*.xml`, seed mặc định của SUMO), không phải trung bình 5 seed.

## 🗂️ Ghi chú `networks/hangxanh.sumocfg`

Đây là cấu hình cũ trước khi tách 6 kịch bản. File dùng `routes/route.rou.xml` (3.600 xe, toàn bộ `r_passenger`, không có tỉ lệ xe máy/bus/tải) và ghi `data/*_output.xml`. Không script nào trong project gọi tới file này. Nhận định: **không cần cho pipeline**. File được giữ nguyên theo yêu cầu. Không nên chạy file này, vì nó cũng ghi đè `data/detector_output.xml` và `data/edgedata_output.xml`.

---

## 🔗 Liên kết với các Nhiệm vụ tiếp theo của Nhóm
- **Task 6 (Chạy mô phỏng & Phân tích dòng giao thông)**: Chạy `python scripts/run_all_scenarios.py` và mở Jupyter Notebook `notebooks/traffic_analysis.ipynb` hoặc chạy `python scripts/plot_results.py` để trực quan hóa đồ thị so sánh giữa các kịch bản.
- **Phân hệ TraCI / AI**: Kết nối điều khiển động thời gian thực với các kịch bản cao điểm và ùn tắc.
