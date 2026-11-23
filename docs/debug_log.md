# Nhật ký Gỡ lỗi & Hiệu chỉnh Mô hình Mô phỏng SUMO (Task 6.1)

Tài liệu này ghi nhận các lỗi kỹ thuật phát hiện khi chạy thử nghiệm toàn bộ 6 kịch bản (`configs/scenario_*.sumocfg`) trên Eclipse SUMO 1.28.0, phương án xử lý bằng `scripts/fix_network.py` và kết quả đối chiếu trước/sau hiệu chỉnh qua 5 hạt giống (`42–46`).

---

## 1. Các Lỗi Kỹ thuật Phát hiện và Cách Khắc phục

### Lỗi 1: Kịch bản `tls_optimized` và `tls_actuated` hoàn toàn vô hiệu (kết quả trùng khớp 100% với `peak`)
- **Triệu chứng:** Toàn bộ KPI (số xe, vận tốc, thời gian chờ, `616,8` teleport trung bình) của `tls_optimized` và `tls_actuated` giống hệt `peak` ở cả 5 seed. Trong `sumo_error.log` xuất hiện cảnh báo:
  - `Warning: Traffic light 'joinedS_4066386148_9415490893_9415490903_#3more' does not control any links`
  - `Warning: At actuated tlLogic 'joinedS_4066386148_9415490893_9415490903_#3more', actuated phase 0/2 has no controlling detector.`
- **Nguyên nhân gốc rễ:**
  1. Sai mã nút đèn (*typo*): trong `networks/hangxanh.net.xml`, `networks/tls_optimized.add.xml` và `networks/tls_actuated.add.xml`, thẻ `<tlLogic>` bị thiếu đoạn `_9415490897_` so với ID nút đèn thật điều khiển 24 kết nối là `joinedS_4066386148_9415490893_9415490897_9415490903_#3more`.
  2. Thiếu tối ưu các nút đèn trọng yếu khác: hai nút có lưu lượng lớn là vòng xoay `1497276515` (`1.611 xe/h`) và nút Bạch Đằng – Đinh Bộ Lĩnh `cluster_10118771782_10118771783_12313165808_12313165809_#2more` (`988 xe/h`) chưa được cấu hình chương trình tối ưu/cảm ứng.
- **Cách sửa:** Xóa 2 khối `<tlLogic>` sai ID qua `scripts/fix_network.py`; viết lại trực tiếp `networks/tls_optimized.add.xml` (`type="static"`, `programID="optimized"`) và `networks/tls_actuated.add.xml` (`type="actuated"`, `programID="actuated"`, `max-gap="3.0"`, `detector-gap="2.5"`) với ID chính xác cho cả hai nút đèn `joinedS_4066386148_9415490893_9415490897_9415490903_#3more` và `cluster_10118771782_10118771783_12313165808_12313165809_#2more`. Kết quả kiểm tra lại có **0 cảnh báo TLS/detector**.

### Lỗi 2: Đèn tín hiệu `1497276515` chặn dòng xe đang ở bên trong vòng xoay gây kẹt dây chuyền
- **Triệu chứng:** Ngay ở kịch bản `baseline` (`2.500 xe/h`), seed `42` và `44` đã phát sinh `26` và `17` lượt teleport; ở `peak` (`4.500 xe/h`), mạng lưới kẹt cứng (`2,33 km/h`, `616,8` teleport TB).
- **Nguyên nhân gốc rễ:** Trong `hangxanh.net.xml`, nút đèn `1497276515` nằm trực tiếp trên thân vòng xoay Hàng Xanh, giữ pha đỏ tới `42 s` (`42/3/42/3` lặp đôi với `programID="1"`) đối với nhánh `971692798` dài chỉ `2,84 m` trong lòng vòng xoay. Xe dừng nối đuôi chỉ 2–3 chiếc là tràn ngược ra `1265700924` (`4,69 m`) và `971692797` (`10,28 m`), làm khóa chặt toàn bộ vòng xoay.
- **Cách sửa:** Xóa `programID="1"` trùng lặp và chuyển pha đèn `1497276515` sang chế độ ưu tiên vòng xoay liên tục `<phase duration="60" state="gggGGGG"/>` (dòng xe đang lưu thông trong vòng xoay luôn xanh `G`, nhánh nhập từ Xô Viết Nghệ Tĩnh vào vòng xoay tuân thủ nhường đường `g`).

### Lỗi 3: Cổ chai thoát vòng xoay 1 làn (`L0`) và làn cụt `192512365#3_5`
- **Triệu chứng:** Cả 4 nhánh thoát chính khỏi vòng xoay (`1265700924 → 231982479#0`, `977346734 → 1278461430`, `1265471308 → 977523911#0`, `1265700913 → 192512353#0`) chỉ cho phép đi từ làn ngoài cùng `L0` của vòng xoay 4 làn, khiến xe ở các làn trong bị dồn ép khi cắt ngang ở cự ly `4,69–13,75 m`. Ngoài ra làn `192512365#3_5` không có kết nối đi tiếp (`dead-end lane`).
- **Cách sửa:** Áp dụng bản vá kết nối qua `netconvert` trong `scripts/fix_network.py` để mở thoát đa làn tương ứng tại cả 4 cửa ra vòng xoay và bổ sung kết nối `192512365#3_5 → 192512383#0_3` (vẫn bảo toàn `12/12` làn đặt vòng cảm ứng E1 trong `routes/detectors.add.xml`).

### Lỗi 4: Thuộc tính khởi hành, `minGap`/`impatience` chưa hợp lý và kẹt chéo cục bộ
- **Triệu chứng:** Xe mặc định sinh ở làn `0` với vận tốc `0` (`departLane` mặc định); xe máy (`length=1.80 m`) dùng `minGap` mặc định `2.50 m` và `impatience=0.0`, dẫn đến kẹt `yield` quá `300 s` ở các nút nhánh ngắn. Ngoài ra `scripts/generate_scenario_routes.py` dùng `list(set(...))` làm thứ tự tuyến phụ thuộc vào `PYTHONHASHSEED`.
- **Cách sửa:**
  1. Bổ sung `departLane="best" departSpeed="max"` và sắp xếp cố định `sorted(unique_routes)` trong `scripts/generate_scenario_routes.py`.
  2. Cập nhật `routes/vtypes.add.xml`: `minGap="1.00"` (xe máy), `"1.50"` (ô tô con), `"2.00"` (buýt/tải); giữ an toàn `tau="1.0"`/`"1.2"` (`≥ step-length`); đặt `impatience="0.10"` cho xe máy/ô tô con.
  3. Thêm `<ignore-junction-blocker value="15"/>` trong thẻ `<processing>` của cả 6 tệp `configs/scenario_*.sumocfg` để giải tỏa xe kẹt ngang giao lộ ngắn sau `15 s`.

---

## 2. Các Phương án Thử nghiệm Đã Loại bỏ

| Thử nghiệm | Kết quả quan sát (seed 42) | Lý do loại bỏ |
| :--- | :--- | :--- |
| Bật chế độ sublane `--lateral-resolution 0.8` | Phát sinh `5–17` vụ va chạm (`collisions`), thời gian chạy tăng ~3–4× | Dễ gây va chạm ngang trên các đoạn ghép `0,2–6,4 m` nhập từ OSM |
| Hạ thời gian phản ứng `tau = 0.7` (`< step-length = 1.0`) | Phát sinh `195` va chạm ngay ở kịch bản `offpeak` | Vi phạm điều kiện ổn định rời rạc `tau ≥ Δt` của mô hình Krauss trong SUMO |
| Đặt đèn đỏ `14–22 s` tại `1497276515` trong lòng vòng xoay | Tái diễn hiện tượng phân nhánh bất ổn định giữa các hạt giống (`6,2` vs `24,1 km/h`) | Đoạn chờ `971692798` chỉ dài `2,84 m`, không đủ chứa hàng đợi |

---

## 3. Bảng So sánh Hiệu năng Trước và Sau Hiệu chỉnh (Trung bình 5 hạt giống `42–46`)

| Kịch bản | Trước: Vận tốc TB (km/h) | Sau: Vận tốc TB (km/h) | Trước: TG chờ TB (s) | Sau: TG chờ TB (s) | Trước: Teleports TB | Sau: Teleports TB | Va chạm (Sau) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `offpeak` | 34,93 | **36,91** | 13,33 | **8,84** | 0,0 | **0,0** | 0 |
| `baseline` | 29,14 | **34,83** | 32,70 | **12,51** | 8,8 | **0,0** | 0 |
| `peak` | 2,33 | **24,71** | 927,64 | **43,97** | 616,8 | **3,2** | 0 |
| `congestion` | 1,59 | **4,37** | 1227,64 | **510,88** | 845,6 | **289,2** | 0 |
| `tls_optimized` | 2,33 *(vô hiệu)* | **30,07** *(+21,7% so với peak)* | 927,64 | **22,40** *(-49,1%)* | 616,8 | **1,8** | 0 |
| `tls_actuated` | 2,33 *(vô hiệu)* | **29,98** *(+21,3% so với peak)* | 927,64 | **22,69** *(-48,4%)* | 616,8 | **3,6** | 0 |

---

## 4. Tài liệu Tham khảo
1. Văn Hồng Tấn (2006). *Giáo trình Hệ thống Giao thông Thông minh (ITS)*. Chương 4 (Mục 4.1.3: Quy trình xây dựng và kiểm chứng mô hình mô phỏng) và Chương 5 (Sóng xung kích ùn tắc giao thông, công thức 5.1).
2. Krauß, S. (1998). *Microscopic Modeling of Traffic Flow: Investigation of Collision Free Vehicle Dynamics*. DLR-Forschungsbericht 98-08.
3. Lopez, P. A. et al. (2018). *Microscopic Traffic Simulation using SUMO*. IEEE ITSC.
