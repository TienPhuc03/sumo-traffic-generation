# Hướng dẫn chụp ảnh SUMO-GUI (Task 6.3)

Mục tiêu: có ít nhất 4 ảnh trong `docs/figures/`, đặt tên `<kịch_bản>_t<giây>.png`:

| Ảnh | Kịch bản | Thời điểm |
|---|---|---|
| `peak_t600.png` | Cao điểm | 600 s |
| `peak_t1800.png` | Cao điểm | 1800 s |
| `tls_optimized_t600.png` | Tối ưu đèn | 600 s |
| `tls_optimized_t1800.png` | Tối ưu đèn | 1800 s |

> **Cảnh báo:** nếu mở thẳng `sumo-gui -c scenario_peak.sumocfg`, SUMO sẽ **ghi đè** `data/tripinfo_peak.xml`, `data/summary_peak.xml`, … và `data/detector_output.xml`. Nếu đóng cửa sổ giữa chừng, các file này bị cắt cụt. Cả hai cách dưới đây đều chuyển đầu ra sang thư mục tạm.

---

## Cách 1 — Tự động (khuyên dùng)

Mở PowerShell **trên máy có màn hình** (không dùng SSH hay terminal headless):

```powershell
cd D:\Workspace\ITS\sumo34\sumo_traffic_project
.\venv\Scripts\Activate.ps1
python scripts\capture_gui.py
```

Script sẽ:
1. Mở SUMO-GUI cho `peak`, chạy tới 600 s và chụp, chạy tiếp tới 1800 s và chụp, rồi tự đóng.
2. Làm lại các bước trên cho `tls_optimized`.
3. In ra mỗi ảnh một dòng, ví dụ `[peak] t=600s, 812 xe trên mạng -> ...\docs\figures\peak_t600.png`.

Mỗi kịch bản mất khoảng 30–90 giây, tùy tốc độ máy. **Không bấm vào cửa sổ SUMO-GUI trong lúc script chạy.**

Tùy chọn:

```powershell
python scripts\capture_gui.py --scenarios peak congestion tls_optimized tls_actuated --times 600 1200 1800
```

```powershell
python scripts\capture_gui.py --zoom 900 --size 1920 1080
```

`--zoom` tính theo %. Mặc định lấy từ `configs/view.xml` (650, tâm nút Hàng Xanh). Số càng lớn thì ảnh càng gần. Trước mỗi lần chụp, script đặt lại tâm và zoom, nên mọi ảnh có cùng khung và cùng tỉ lệ. Ở zoom 650, thước tỉ lệ 10 m dài khoảng 50 px và khung ngang rộng khoảng 320 m. Nếu ảnh lệch tỉ lệ này, hãy chụp lại.

Nếu ảnh bị đen hoặc trắng: chạy lại và để cửa sổ SUMO-GUI hiện trên cùng (không thu nhỏ).

### Ảnh cận cảnh hàng đợi nhánh tây nam

Theo `data/csv/queue.csv`, nhánh tây nam (edge `192512365#1` → cửa vào vòng xoay) có hàng đợi dài nhất ở kịch bản cao điểm. Lệnh dưới đây chụp cận cảnh vùng này: tâm (985, 740), zoom 1200, khung khoảng 174 × 108 m.

```powershell
python scripts\capture_gui.py --zoom 1200 --center 985 740 --tag can_canh_tn
```

Kết quả gồm 4 ảnh mới (`peak_t600_can_canh_tn.png`, `peak_t1800_can_canh_tn.png`, `tls_optimized_t600_can_canh_tn.png`, `tls_optimized_t1800_can_canh_tn.png`); 4 ảnh tổng quan giữ nguyên. Khi đổi `--zoom` hoặc `--center`, bắt buộc phải có `--tag`, để không ghi đè ảnh tổng quan. Ở zoom 1200, thước 10 m dài khoảng 92 px.

---

## Cách 2 — Chụp tay

### Bước 1. Mở SUMO-GUI, dừng tự động tại 600 s và 1800 s

```powershell
cd D:\Workspace\ITS\sumo34\sumo_traffic_project\configs
New-Item -ItemType Directory -Force "$env:TEMP\sumo_gui" | Out-Null
```

Kịch bản cao điểm:

```powershell
sumo-gui -c scenario_peak.sumocfg --breakpoints 600,1800 --additional-files ../routes/vtypes.add.xml --tripinfo-output "$env:TEMP\sumo_gui\tripinfo.xml" --summary-output "$env:TEMP\sumo_gui\summary.xml" --queue-output "$env:TEMP\sumo_gui\queue.xml" --edgedata-output "$env:TEMP\sumo_gui\edgedata.xml" --emission-output "$env:TEMP\sumo_gui\emission.xml"
```

Kịch bản tối ưu đèn (khác ở `-c` và `--additional-files`):

```powershell
sumo-gui -c scenario_tls_optimized.sumocfg --breakpoints 600,1800 --additional-files ../routes/vtypes.add.xml,../networks/tls_optimized.add.xml --tripinfo-output "$env:TEMP\sumo_gui\tripinfo.xml" --summary-output "$env:TEMP\sumo_gui\summary.xml" --queue-output "$env:TEMP\sumo_gui\queue.xml" --edgedata-output "$env:TEMP\sumo_gui\edgedata.xml" --emission-output "$env:TEMP\sumo_gui\emission.xml"
```

- `--breakpoints 600,1800`: mô phỏng tự tạm dừng tại 600 s và 1800 s.
- `--additional-files` bỏ `detectors.add.xml` để không ghi đè `data/detector_output.xml`.
- Cấu hình có `start=true` nên mô phỏng chạy ngay khi mở. Nếu muốn chạy chậm hơn để quan sát, tăng ô **Delay (ms)** trên thanh công cụ.

### Bước 2. Chụp tại 600 s

1. Đợi mô phỏng tự dừng. Đồng hồ thời gian trên thanh công cụ hiện `600`.
2. Giữ nguyên góc nhìn mặc định (đã đặt trong `configs/view.xml`) để các ảnh so sánh được với nhau. Nếu lỡ kéo hay zoom, mở lại SUMO-GUI.
3. Bấm nút **chụp ảnh** (biểu tượng máy ảnh) trên thanh công cụ của khung nhìn. Lưu vào `D:\Workspace\ITS\sumo34\sumo_traffic_project\docs\figures\peak_t600.png`. Tạo thư mục `figures` nếu chưa có.
   - Nếu không tìm thấy nút này: dùng `Win + Shift + S` để chụp vùng bản đồ, rồi lưu đúng tên file ở trên.

### Bước 3. Chụp tại 1800 s

1. Bấm **Run** (nút ▶ màu xanh) để chạy tiếp. Mô phỏng sẽ dừng tại 1800 s.
2. Chụp như bước 2, đặt tên `peak_t1800.png`.
3. Đóng SUMO-GUI.

### Bước 4. Lặp lại cho `tls_optimized`

Chạy lệnh thứ hai ở bước 1. Lưu ảnh thành `tls_optimized_t600.png` và `tls_optimized_t1800.png`.

---

## Gắn nhãn trước khi đưa vào báo cáo

Sau mỗi lần chụp thêm ảnh, chạy:

```powershell
python scripts\annotate_figures.py
```

Script tạo `docs/figures/annotated/<cùng tên>.png`, thêm một dải phía trên ảnh (không che bản đồ) gồm:
- Tên kịch bản (kèm lưu lượng), thời điểm t, và nhãn cận cảnh nếu có.
- Số xe đang chạy và đang dừng của **toàn mạng** tại t, lấy từ `data/summary_<kịch_bản>.xml` (không lấy từ terminal), kèm ghi chú "1 lần chạy, seed mặc định".
- Chú giải màu xe theo `routes/vtypes.add.xml`: đỏ xe máy, xanh lá ô tô con, xanh dương xe buýt, vàng xe tải.

Ảnh gốc trong `docs/figures/` giữ nguyên. Chỉ chụp ở mốc chia hết cho 60 s (vì `summary_*.xml` ghi mỗi 60 s); mốc khác sẽ bị báo lỗi, không tự điền số.

Caption mẫu trong báo cáo: *"Hình X. Kịch bản Cao điểm tại t = 1800 s (SUMO-GUI, 1 lần chạy, seed mặc định). Toàn mạng: 187 xe đang chạy, 40 xe đang dừng. Ảnh mang tính minh họa; so sánh định lượng xem Bảng KPI (5 seed)."*

## Kiểm tra

```powershell
Get-ChildItem D:\Workspace\ITS\sumo34\sumo_traffic_project\docs\figures
```

Phải có ít nhất 4 file `.png` đúng tên như bảng ở đầu tài liệu. Khi đưa ảnh vào báo cáo, ghi chú thích theo mẫu: *"Kịch bản Cao điểm tại t = 600 s (SUMO-GUI, seed mặc định)"*.
