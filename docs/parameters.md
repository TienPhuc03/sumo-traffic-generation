# Danh mục Thông số Dòng Giao thông cần Thu thập (Task 5.1)

Tài liệu này xác định đầy đủ các thông số, ký hiệu, đơn vị đo, chu kỳ lấy mẫu và định nghĩa trích xuất từ 6 nguồn đầu ra của Eclipse SUMO 1.28.0 tại nút giao Ngã tư Hàng Xanh (cấu hình trong `configs/*.sumocfg` và `routes/detectors.add.xml`, chuyển đổi sang bảng tại `data/csv/*.csv` qua `scripts/xml_to_csv.py`).

## 1. Các thông số cơ sở dòng giao thông (Fundamental Traffic Parameters)

Theo giáo trình *Hệ thống Giao thông Thông minh (ITS)* (Văn Hồng Tấn, 2006, Chương 2, Mục 1 & 3), trạng thái hoạt động của dòng giao thông được đánh giá thông qua 3 thông số cơ bản: **lưu lượng (`q`)**, **mật độ (`k`)** và **vận tốc (`v`)**, liên hệ qua phương trình cơ bản `q = k × v`.

| Nhóm | Thông số (Tiếng Việt) | Trường XML / CSV | Ký hiệu | Đơn vị | Nguồn SUMO | Định nghĩa & Công thức |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Cơ sở | Lưu lượng qua mặt cắt | `flow` | `q` | xe/h | `detector.xml`, `edgedata.xml` | Số xe đi qua điểm quan trắc trong 1 giờ: `q = nVehContrib × 3600 / Δt` |
| Cơ sở | Số xe đóng góp mẫu | `nVehContrib`, `nVehEntered` | `N` | xe | `detector.xml` | Tổng số xe đi qua hết / vừa đi vào vòng cảm ứng E1 trong chu kỳ `900 s` |
| Cơ sở | Mật độ dòng xe trên đoạn đường | `density`, `laneDensity` | `k` | xe/km (và xe/km/làn) | `edgedata.xml` | Số xe trung bình trên `1 km` đoạn đường (`density`) hoặc trên `1 km` của 1 làn (`laneDensity`) |
| Cơ sở | Mật độ có tính chồng lấp | `overlapDensity` | `k_ov` | xe/km | `edgedata.xml` | Mật độ tính cả phần chiều dài xe chiếm chỗ qua ranh giới đoạn |
| Cơ sở | Tỷ lệ chiếm dụng vòng từ | `occupancy` | `Occ` | % | `detector.xml`, `edgedata.xml` | Tỷ lệ phần trăm thời gian vùng dò bị xe choáng chỗ trong chu kỳ `T` (liên hệ `k ∝ Occ / (L_v + L_eff)`, Văn Hồng Tấn, 2006, CT 2.10) |
| Cơ sở | Vận tốc trung bình thời gian | `speed` | `v_t` | m/s | `detector.xml` | Trung bình cộng vận tốc tức thời các xe qua detector E1 (`-1.00` nếu không có xe) |
| Cơ sở | Vận tốc trung bình không gian | `harmonicMeanSpeed`, `speed` | `v_s` | m/s | `detector.xml`, `edgedata.xml` | Trung bình điều hòa tại detector (`harmonicMeanSpeed`) hoặc tỷ số quãng đường/thời gian trên edge (`speed`) |
| Cơ sở | Vận tốc trung bình chuyến đi | `(routeLength / duration) × 3.6` | `v_trip` | km/h | Tính từ `tripinfo.csv` | Vận tốc trung bình không gian toàn chuyến của từng phương tiện |
| Cơ sở | Vận tốc tương đối | `speedRelative`, `meanSpeedRelative` | `v / v_max` | không thứ nguyên | `edgedata.xml`, `summary.xml` | Tỷ số giữa vận tốc thực tế và tốc độ tối đa cho phép của đoạn đường |

---

## 2. Chi tiết thông số theo từng tệp đầu ra (`data/csv/*.csv`)

### 2.1. Dữ liệu từng chuyến xe — `tripinfo.csv` (nguồn `tripinfo.xml`)
Ghi nhận theo từng phương tiện khi kết thúc chuyến hoặc kết thúc mô phỏng (`write-unfinished="true"`, tổng hợp mỗi dòng trong `tripinfo.csv` kèm `scenario`, `seed`).

| Trường CSV | Kiểu / Đơn vị | Ý nghĩa |
| :--- | :--- | :--- |
| `scenario`, `seed` | chuỗi, số nguyên | Tên kịch bản và hạt giống ngẫu nhiên SUMO (`42`–`46`) |
| `id`, `vType` | chuỗi | Mã định danh xe (`veh_*`) và loại xe (`moped`, `passenger`, `bus`, `truck`) |
| `depart`, `arrival` | s | Thời điểm xuất phát thực tế và thời điểm kết thúc chuyến (`-1.00` nếu chưa kết thúc trước `end=3600`) |
| `departLane`, `arrivalLane` | chuỗi | Làn xuất phát và làn kết thúc hành trình |
| `departPos`, `arrivalPos` | m | Vị trí dọc theo làn lúc xuất phát và kết thúc |
| `departSpeed`, `arrivalSpeed` | m/s | Vận tốc lúc xuất phát và kết thúc |
| `departDelay` | s | Thời gian xe phải chờ trước khi được đưa vào mạng lưới so với lịch `depart` |
| `duration` | s | Tổng thời gian di chuyển (`arrival - depart` hoặc tới cuối mô phỏng) |
| `routeLength` | m | Tổng quãng đường phương tiện đi được |
| `waitingTime` | s | Tổng thời gian xe dừng chờ (`v ≤ 0.1 m/s`) trong suốt chuyến |
| `waitingCount` | lần | Số lần xe phải dừng chờ trong chuyến |
| `stopTime` | s | Thời gian dừng tại điểm dừng khai báo sẵn |
| `timeLoss` | s | Tổng tổn thất thời gian do chạy chậm hơn tốc độ mong muốn |
| `rerouteNo`, `speedFactor` | lần, hệ số | Số lần tái định tuyến và hệ số tốc độ cá nhân hóa |
| `vaporized` | chuỗi | Lý do xe bị loại sớm nếu có (trống với xe bình thường) |
| `CO_abs`, `CO2_abs`, `HC_abs`, `PMx_abs`, `NOx_abs` | mg | Tổng khối lượng các chất khí thải tích lũy suốt chuyến (mô hình `HBEFA4`) |
| `fuel_abs`, `electricity_abs` | mg, Wh | Tổng nhiên liệu tiêu thụ (`mg`) và điện năng tiêu thụ (`Wh`) cả chuyến |

### 2.2. Dữ liệu toàn mạng theo thời gian — `summary.csv` (nguồn `summary.xml`)
Chu kỳ lấy mẫu: **`60 s`** (`summary-output.period="60"`), từ `t = 0 s` đến `t = 3600 s`.

| Trường CSV | Đơn vị | Ý nghĩa |
| :--- | :--- | :--- |
| `time` | s | Mốc thời gian mô phỏng |
| `loaded`, `inserted`, `running`, `waiting` | xe | Số xe nạp từ route, đã vào mạng, đang lưu thông trên mạng, và đang chờ ở cửa ngõ |
| `ended`, `arrived`, `discarded` | xe | Số xe đã kết thúc (`ended`), tới đích (`arrived`), và bị loại (`discarded`) |
| `collisions`, `teleports` | lượt | Số vụ va chạm và số lượt teleport tích lũy tới thời điểm `time` |
| `halting`, `stopped` | xe | Số xe đang dừng (`v ≤ 0.1 m/s`) và xe dừng có chủ đích (`stop`) |
| `meanWaitingTime` | s | Thời gian chờ trung bình tại mốc `time` (`-1.00` khi chưa có xe) |
| `meanTravelTime` | s | Thời gian hoàn thành chuyến trung bình của xe đã tới đích |
| `meanSpeed` | m/s | Vận tốc trung bình toàn mạng lưới tại mốc `time` |
| `meanSpeedRelative` | hệ số | Tỷ lệ vận tốc trung bình toàn mạng so với tốc độ giới hạn |
| `duration` | ms | Thời gian CPU xử lý bước mô phỏng |

### 2.3. Dữ liệu hàng đợi tại làn đường — `queue.csv` (nguồn `queue.xml`)
Chu kỳ lấy mẫu: **`60 s`** (`queue-output.period="60"`). Mỗi hàng ghi nhận một làn có hàng đợi khác rỗng tại `timestep`.

| Trường CSV | Đơn vị | Ý nghĩa |
| :--- | :--- | :--- |
| `timestep` | s | Thời điểm lấy mẫu hàng đợi |
| `id` | chuỗi | Mã làn đường (`<edge>_<laneIndex>`) |
| `queueing_time` | s | Thời gian chờ tối đa của xe đứng đầu hàng đợi trên làn |
| `queueing_length` | m | Chiều dài hàng đợi từ vạch dừng tới xe cuối hàng |
| `queueing_length_experimental` | m | Chiều dài hàng đợi tính theo thuật toán thử nghiệm của SUMO |

### 2.4. Dữ liệu theo đoạn đường — `edgedata.csv` (nguồn `edgedata.xml`)
Thống kê tổng hợp trên toàn chu kỳ mô phỏng (`begin = 0.00`, `end = 3600.00 s`) cho từng đoạn đường (`edge`).

| Trường CSV | Đơn vị | Ý nghĩa |
| :--- | :--- | :--- |
| `begin`, `end`, `id` | s, s, chuỗi | Khoảng thời gian tổng hợp và mã đoạn đường (`edge`) |
| `sampledSeconds` | xe·s | Tổng thời gian tích lũy của mọi xe trên đoạn đường |
| `traveltime`, `overlapTraveltime` | s | Thời gian đi hết đoạn đường trung bình (chuẩn và có chồng lấp) |
| `density`, `overlapDensity`, `laneDensity` | xe/km, xe/km/làn | Mật độ trung bình trên đoạn đường và trên mỗi làn |
| `occupancy` | % | Độ chiếm dụng mặt đường trung bình của phương tiện |
| `waitingTime`, `timeLoss` | s | Tổng thời gian dừng chờ và tổng tổn thất thời gian của xe trên đoạn |
| `speed`, `speedRelative` | m/s, hệ số | Vận tốc trung bình không gian và vận tốc tương đối trên đoạn |
| `departed`, `arrived`, `entered`, `left` | xe | Số xe xuất phát, tới đích, đi vào và đi ra khỏi đoạn |
| `laneChangedFrom`, `laneChangedTo` | lượt | Số lượt chuyển làn xuất phát từ đoạn / chuyển sang đoạn |
| `flow`, `distance` | xe/h, m | Lưu lượng quy đổi theo giờ và tổng quãng đường tích lũy trên đoạn |

### 2.5. Dữ liệu vòng cảm ứng từ E1 — `detector.csv` (nguồn `detector.xml` / `detectors.add.xml`)
Gồm **12 vòng cảm ứng E1** đặt tại các nhánh chính quanh vòng xoay Hàng Xanh, chu kỳ lấy mẫu **`900 s`** (`freq="900.0"`, tương ứng 4 khung 15 phút trong 1 giờ mô phỏng).

| Trường CSV | Đơn vị | Ý nghĩa |
| :--- | :--- | :--- |
| `begin`, `end` | s | Thời điểm đầu và cuối chu kỳ 15 phút (`0–900`, `900–1800`, `1800–2700`, `2700–3600`) |
| `id` | chuỗi | Mã vòng cảm ứng (`e1_<edgeID>`) |
| `nVehContrib`, `nVehEntered` | xe | Số xe đi qua hoàn toàn và số xe đi vào vùng dò trong chu kỳ |
| `flow` | xe/h | Lưu lượng quy đổi giờ (`nVehContrib × 4` cho chu kỳ 900 s) |
| `occupancy` | % | Tỷ lệ thời gian vòng cảm ứng bị xe chiếm dụng |
| `speed`, `harmonicMeanSpeed` | m/s | Vận tốc trung bình thời gian và trung bình điều hòa qua mặt cắt detector |
| `length` | m | Chiều dài trung bình của các phương tiện đi qua (`-1.00` nếu không có xe) |

### 2.6. Dữ liệu phát thải tức thời — `emission.csv` (nguồn `emission.xml`)
Chu kỳ lấy mẫu: **`60 s`** (`device.emissions.period="60"`, `device.emissions.probability="1.0"`), theo mô hình phát thải `HBEFA4` của SUMO cho từng xe đang lưu thông.

| Trường CSV | Đơn vị | Ý nghĩa |
| :--- | :--- | :--- |
| `time`, `id`, `type`, `eclass` | s, chuỗi | Thời điểm lấy mẫu, mã xe, loại xe và chuẩn khí thải (`HBEFA4/*`) |
| `CO2`, `CO`, `HC`, `NOx`, `PMx` | mg/s | Tốc độ phát thải tức thời các khí thải và bụi mịn tại thời điểm `time` |
| `fuel`, `electricity` | mg/s, Wh/s | Tốc độ tiêu thụ nhiên liệu (`mg/s`) và điện năng (`Wh/s`) |
| `noise` | dBA | Mức ồn phát sinh tại vị trí phương tiện |
| `waiting`, `speed`, `angle` | s, m/s, độ | Thời gian dừng tích lũy hiện tại, vận tốc tức thời và góc hướng chuyển động |
| `route`, `lane`, `pos`, `x`, `y` | chuỗi, m | Tuyến đi, làn hiện tại, vị trí trên làn và tọa độ phẳng (m) |

---

## 3. Tài liệu tham khảo chính
1. Văn Hồng Tấn (2006). *Giáo trình Hệ thống Giao thông Thông minh (ITS)*. Chương 2: Hệ thống quan trắc giao thông và tính toán xử lý số liệu vòng từ (công thức 2.10, 2.20).
2. Lopez, P. A., Behrisch, M., Bieker-Walz, L., Erdmann, J., Flötteröd, Y.-P., Hilbrich, R., Lücken, L., Rummel, J., Wagner, P., & Wießner, E. (2018). *Microscopic Traffic Simulation using SUMO*. IEEE International Conference on Intelligent Transportation Systems (ITSC).
