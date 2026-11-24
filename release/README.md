# Bộ dữ liệu mô phỏng SUMO — Ngã tư Hàng Xanh (Đề tài 34)

## 1. Mục đích và phạm vi

Bộ dữ liệu dạng bảng (CSV, UTF-8) từ mô phỏng vi mô Eclipse SUMO 1.28.0 tại nút giao Hàng Xanh (Bình Thạnh, TP.HCM), dùng cho phân tích dòng giao thông và so sánh phương án điều khiển đèn.

- **6 kịch bản:** `offpeak` (~1.200 xe/h), `baseline` (~2.500 xe/h), `peak` (~4.500 xe/h), `congestion` (~6.000 xe/h), `tls_optimized` (đèn cố định tối ưu, demand peak), `tls_actuated` (đèn cảm ứng, demand peak).
- **5 seed** SUMO cho mỗi kịch bản: `42`, `43`, `44`, `45`, `46`, tổng cộng 30 lần chạy.
- **1 giờ mô phỏng** mỗi lần chạy (`0–3600 s`), bước `1 s`.
- Mọi bảng có cột `scenario` (tên kịch bản) và `seed` (số nguyên).

Danh sách file, dung lượng, số dòng, số cột và mã `sha256` nằm trong [`manifest.csv`](manifest.csv). Kiểm tra tính toàn vẹn:

```powershell
certutil -hashfile release\tripinfo.csv SHA256
```

Nếu CSV quá lớn để đưa lên Git, repo chỉ lưu `README.md` và `manifest.csv`. Khi đó, tái tạo CSV theo mục 4, rồi so sánh `sha256` với manifest.

## 2. Danh sách file

| File | Nguồn SUMO | Đơn vị một dòng | Chu kỳ lấy mẫu |
|---|---|---|---|
| `tripinfo.csv` | `tripinfo-output` (+ `emissions` của từng chuyến) | 1 chuyến xe | theo chuyến, kể cả xe chưa đến đích (`write-unfinished`) |
| `summary.csv` | `summary-output` | 1 mốc thời gian, toàn mạng | 30 s |
| `queue.csv` | `queue-output` | 1 làn có hàng đợi tại 1 mốc | 30 s |
| `edgedata.csv` | `edgedata-output` | 1 đoạn đường (edge) | 1 khoảng `0–3600 s` |
| `emission.csv` | `emission-output` (HBEFA4) | 1 xe tại 1 mốc | 30 s |
| `detector.csv` | 12 vòng cảm ứng E1 (`routes/detectors.add.xml`) | 1 detector trong 1 khung | 900 s (4 khung 15 phút) |
| `aggregated_30s.csv` | Gộp từ `summary`, `tripinfo`, `emission`, `queue` | 1 khoảng 30 s (toàn mạng) hoặc 1 làn trong 1 khoảng | 30 s |
| `detector_peak_s42_clean.csv` | `detector.xml` của `peak`/seed 42, qua `clean_data.py` (Task 7.2) | 1 detector trong 1 khung | 900 s |

Chu kỳ 30 s là chu kỳ của `data/raw/`, do `run_multi_seed.py` ghi đè. Các file `data/*_<kịch_bản>.xml` (1 lần chạy) dùng 60 s theo `configs/*.sumocfg`.

## 3. Từ điển dữ liệu

Đơn vị lấy theo `docs/parameters.md` (mục 2.1–2.7).

### 3.1. `tripinfo.csv`

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `scenario`, `seed` | chuỗi, số nguyên | Kịch bản và seed |
| `id`, `vType` | chuỗi | Mã xe và loại xe (`moped`, `passenger`, `bus`, `truck`) |
| `depart`, `arrival` | s | Thời điểm xuất phát thực tế và thời điểm kết thúc (`-1` nếu chưa đến đích lúc `t = 3600 s`) |
| `departLane`, `arrivalLane` | chuỗi | Làn xuất phát và làn kết thúc |
| `departPos`, `arrivalPos` | m | Vị trí trên làn lúc xuất phát và lúc kết thúc |
| `departSpeed`, `arrivalSpeed` | m/s | Vận tốc lúc xuất phát và lúc kết thúc |
| `departDelay` | s | Thời gian chờ được đưa vào mạng so với lịch |
| `duration` | s | Thời gian di chuyển (tính tới cuối mô phỏng nếu chưa đến đích) |
| `routeLength` | m | Quãng đường đã đi |
| `waitingTime` | s | Tổng thời gian đứng chờ (`v ≤ 0.1 m/s`) |
| `waitingCount` | lần | Số lần dừng chờ |
| `stopTime` | s | Thời gian dừng tại điểm dừng khai báo |
| `timeLoss` | s | Tổn thất thời gian so với chạy ở vận tốc mong muốn |
| `rerouteNo` | lần | Số lần tái định tuyến |
| `speedFactor` | hệ số | Hệ số vận tốc riêng của xe |
| `vaporized` | chuỗi | Lý do xe bị loại sớm (trống nếu bình thường) |
| `CO_abs`, `CO2_abs`, `HC_abs`, `PMx_abs`, `NOx_abs` | mg | Khối lượng phát thải tích lũy cả chuyến |
| `fuel_abs` | mg | Nhiên liệu tiêu thụ cả chuyến |
| `electricity_abs` | Wh | Điện năng tiêu thụ cả chuyến |

### 3.2. `summary.csv`

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `scenario`, `seed` | chuỗi, số nguyên | Kịch bản và seed |
| `time` | s | Mốc lấy mẫu (`0, 30, …, 3570`) |
| `loaded`, `inserted`, `running`, `waiting` | xe | Đã nạp, đã vào mạng, đang chạy, đang chờ vào mạng |
| `ended`, `arrived`, `discarded` | xe | Đã kết thúc, đã tới đích, bị loại |
| `collisions`, `teleports` | lượt | Va chạm và teleport tích lũy tới `time` |
| `halting`, `stopped` | xe | Đang đứng (`v ≤ 0.1 m/s`) và đang dừng có chủ đích |
| `meanWaitingTime` | s | Thời gian chờ TB tại mốc `time` (`-1` khi chưa có xe) |
| `meanTravelTime` | s | Thời gian chuyến TB của xe đã tới đích (`-1` khi chưa có) |
| `meanSpeed` | m/s | Vận tốc TB toàn mạng (`-1` khi không có xe) |
| `meanSpeedRelative` | hệ số | Vận tốc TB so với tốc độ giới hạn |
| `duration` | ms | Thời gian CPU của bước mô phỏng (không phải đại lượng giao thông) |

### 3.3. `queue.csv`

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `scenario`, `seed` | chuỗi, số nguyên | Kịch bản và seed |
| `timestep` | s | Mốc lấy mẫu |
| `id` | chuỗi | Mã làn `<edge>_<chỉ_số_làn>` (chỉ ghi làn có hàng đợi) |
| `queueing_time` | s | Thời gian chờ của xe đầu hàng |
| `queueing_length` | m | Chiều dài hàng đợi từ vạch dừng tới xe cuối |
| `queueing_length_experimental` | m | Chiều dài hàng đợi theo thuật toán thử nghiệm của SUMO |

### 3.4. `edgedata.csv`

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `scenario`, `seed` | chuỗi, số nguyên | Kịch bản và seed |
| `begin`, `end` | s | Khoảng thống kê (`0–3600`) |
| `id` | chuỗi | Mã edge |
| `sampledSeconds` | xe·s | Tổng thời gian có mặt của mọi xe trên edge |
| `traveltime`, `overlapTraveltime` | s | Thời gian đi hết edge TB (chuẩn và có chồng lấp) |
| `density`, `overlapDensity` | xe/km | Mật độ TB (chuẩn và có chồng lấp) |
| `laneDensity` | xe/km/làn | Mật độ TB trên mỗi làn |
| `occupancy` | % | Độ chiếm dụng TB |
| `waitingTime`, `timeLoss` | s | Tổng thời gian chờ và tổng tổn thất của xe trên edge |
| `speed` | m/s | Vận tốc TB không gian |
| `speedRelative` | hệ số | Vận tốc TB so với tốc độ giới hạn |
| `departed`, `arrived`, `entered`, `left` | xe | Xuất phát, tới đích, đi vào, đi ra khỏi edge |
| `laneChangedFrom`, `laneChangedTo` | lượt | Chuyển làn ra khỏi / vào edge |
| `teleported` | xe | Số xe bị teleport khỏi edge (do kẹt quá `time-to-teleport = 300 s`) |
| `flow` | xe/h | Lưu lượng quy đổi theo giờ |
| `distance` | m | Tổng quãng đường xe đi trên edge |

### 3.5. `emission.csv`

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `scenario`, `seed` | chuỗi, số nguyên | Kịch bản và seed |
| `time` | s | Mốc lấy mẫu |
| `id`, `type`, `eclass` | chuỗi | Mã xe, loại xe, lớp phát thải (`HBEFA4/*`) |
| `CO2`, `CO`, `HC`, `NOx`, `PMx` | mg/s | **Tốc độ** phát thải tức thời. Khối lượng ≈ Σ giá trị × 30 s |
| `fuel` | mg/s | Tốc độ tiêu thụ nhiên liệu |
| `electricity` | Wh/s | Tốc độ tiêu thụ điện |
| `noise` | dBA | Mức ồn tại vị trí xe |
| `route`, `lane` | chuỗi | Tuyến và làn hiện tại |
| `waiting` | s | Thời gian đứng chờ tích lũy hiện tại |
| `speed` | m/s | Vận tốc tức thời |
| `angle` | độ | Góc hướng |
| `pos` | m | Vị trí trên làn |
| `x`, `y` | m | Tọa độ phẳng |

### 3.6. `detector.csv`

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `scenario`, `seed` | chuỗi, số nguyên | Kịch bản và seed |
| `begin`, `end` | s | Khung 15 phút (`0–900`, …, `2700–3600`) |
| `id` | chuỗi | Mã detector `e1_<edge>` |
| `nVehContrib`, `nVehEntered` | xe | Số xe đi qua hết và số xe đi vào vùng dò |
| `flow` | xe/h | Lưu lượng quy đổi giờ (`= nVehContrib × 4`) |
| `occupancy` | % | Tỉ lệ thời gian vùng dò bị chiếm |
| `speed`, `harmonicMeanSpeed` | m/s | Vận tốc TB thời gian và TB điều hòa (`-1` nếu không có xe) |
| `length` | m | Chiều dài TB của xe đi qua (`-1` nếu không có xe) |

### 3.7. `aggregated_30s.csv` (Task 7.3)

Khoảng nửa mở `[t_start, t_end)`, 120 khoảng cho mỗi lần chạy. Bảng có hai loại dòng:
- **Dòng toàn mạng** (`lane` rỗng): đủ mọi cột.
- **Dòng theo làn** (`lane` = mã làn): chỉ có cho làn có hàng đợi trong khoảng, chỉ có `queue_max_m`; các cột còn lại để trống. Khi cộng số liệu toàn mạng, lọc `lane` rỗng để tránh cộng trùng.

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `scenario`, `seed` | chuỗi, số nguyên | Kịch bản và seed |
| `t_start`, `t_end` | s | Đầu và cuối khoảng |
| `lane` | chuỗi | Mã làn, rỗng ở dòng toàn mạng |
| `running_mean`, `halting_mean` | xe | TB `running` và `halting` của các mẫu summary trong khoảng |
| `speed_mean_kmh` | km/h | TB `meanSpeed` (bỏ `-1`) × 3.6. Trống khi không có xe trên mạng (khoảng đầu tiên) |
| `departed` | xe | Số xe có `depart` trong khoảng |
| `arrived` | xe | Số xe có `arrival` trong khoảng (bỏ xe chưa đến đích) |
| `duration_mean`, `waiting_mean`, `timeloss_mean` | s | TB của xe **kết thúc** trong khoảng. Trống khi `arrived = 0` |
| `co2_g` | g | Σ `CO2` (mg/s) × 30 s / 1000 của các mẫu trong khoảng |
| `queue_max_m` | m | Max `queueing_length`. Dòng toàn mạng: max mọi làn, `0` nếu không có hàng đợi |

### 3.8. `detector_peak_s42_clean.csv` (Task 7.2)

Mẫu đầu ra của bước làm sạch detector, chỉ gồm 1 lần chạy (`peak`, seed 42). File không có cột `scenario` và `seed`.

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `time` | s | Đầu khung 900 s (`begin` của detector) |
| `id` | chuỗi | Mã detector |
| `nVehContrib` | xe | Số xe đi qua hết vùng dò trong khung |
| `speed` | m/s | Vận tốc TB thời gian. `-1` (không có xe) được thay bằng `0` |

Bảo toàn số xe đã được kiểm tra cho mọi lần chạy: Σ `departed` = số xe xuất phát trong `tripinfo`; Σ `arrived` + số xe chưa đến đích = số dòng `tripinfo`.

## 4. Cách tái tạo

Từ thư mục gốc project, với SUMO 1.28.0 và `venv` cài từ `requirements.txt`:

```powershell
.\venv\Scripts\Activate.ps1
python scripts\test_connection.py
python scripts\run_multi_seed.py --steps 300      # chạy thử nhanh (xóa data\raw\run_log.csv sau đó)
python scripts\run_multi_seed.py                  # 6 kịch bản × 5 seed (42–46) -> data\raw\
python scripts\xml_to_csv.py                      # -> data\csv\{tripinfo,summary,queue,edgedata,emission,detector}.csv
python scripts\aggregate_intervals.py --selftest  # kiểm tra trên peak/seed_42
python scripts\aggregate_intervals.py             # -> data\csv\aggregated_30s.csv
python scripts\reliability_analysis.py            # -> data\analysis\ (KPI theo seed, độ tin cậy)
python scripts\plot_results.py                    # -> data\traffic_fundamental_diagram.png, data\traffic_comparison_dashboard.png
python scripts\package_data.py                    # -> release\*.csv, release\manifest.csv
```

`run_multi_seed.py` **append** vào `data\raw\run_log.csv`. Khi chạy lại từ đầu, xóa file này trước để tránh trùng dòng. Mô phỏng là tất định theo seed, nên chạy lại cho ra cùng số liệu.

## 5. Giới hạn

1. **Demand cố định:** mọi seed dùng cùng `routes/routes_*.rou.xml`. Độ phân tán giữa các seed chỉ phản ánh phần ngẫu nhiên nội tại của SUMO (hành vi lái, chèn xe), không phản ánh biến động nhu cầu đi lại.
2. **Không có đỉnh giờ:** thời điểm xuất phát rải đều trong 1 giờ. "Giờ cao điểm" chỉ là mật độ cao hơn, không có hình dạng đỉnh.
3. **Chưa hiệu chuẩn** với số liệu đếm xe thực tế (project không có số liệu đếm).
4. **Đường đi** sinh từ `randomTrips` + `duarouter`, không lấy từ ma trận OD thật.
5. **Phát thải** dùng mô hình HBEFA4 của SUMO, không đo thực tế. CO2 tích phân từ `emission.csv` (lấy mẫu 30 s) lệch vài phần trăm so với `CO2_abs` (tích lũy từng bước 1 s).
6. **Notebook** `notebooks/traffic_analysis.ipynb` và các file `data/*_<kịch_bản>.xml` là **1 lần chạy** mỗi kịch bản (seed mặc định của SUMO), không phải trung bình 5 seed của bộ dữ liệu này.
7. `detector.csv` chỉ có 4 khung 900 s mỗi detector, nên Fundamental Diagram có ít điểm cho mỗi lần chạy.
