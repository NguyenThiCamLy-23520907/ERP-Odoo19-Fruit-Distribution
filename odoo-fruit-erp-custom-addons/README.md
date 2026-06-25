
# Odoo Fruit ERP Custom Addons

Repository này chứa 2 custom module Odoo được phát triển cho đồ án triển khai ERP trong doanh nghiệp thu mua, phân phối và bán lẻ trái cây tươi.

Các module được xây dựng để mở rộng các luồng nghiệp vụ chuẩn của Odoo, đặc biệt là Inventory, CRM, Sales và Pricing. Mục tiêu chính là hỗ trợ các nghiệp vụ đặc thù của ngành trái cây tươi như quản lý lô hàng, kiểm định chất lượng đầu vào, kiểm soát hàng hư/hàng hao hụt, xuất kho theo FEFO và tạo bảng giá bán hằng ngày dựa trên thông tin thị trường từ CRM.

---

## 1. Bối cảnh dự án

Dự án mô phỏng việc triển khai Odoo ERP cho một doanh nghiệp kinh doanh trái cây tươi.

Doanh nghiệp có các hoạt động chính:

- Thu mua trái cây từ nhà vườn, hợp tác xã và nhà cung cấp.
- Nhập kho và kiểm định chất lượng đầu vào.
- Quản lý tồn kho theo Lot/Batch, hạn sử dụng và vị trí kho.
- Phân phối trái cây cho khách sỉ, siêu thị, cửa hàng bán lẻ và kênh online.
- Theo dõi cơ hội bán hàng trong CRM.
- Tạo báo giá, đơn bán hàng và bảng giá theo ngày.
- Ghi nhận hàng hư, hàng dập, hao hụt.
- Tổng hợp báo cáo vận hành phục vụ quản lý.

Vì trái cây tươi là nhóm hàng có vòng đời ngắn, giá bán biến động nhanh và dễ phát sinh hao hụt, hệ thống ERP cần có thêm các chức năng phù hợp với nghiệp vụ thực tế của ngành này.

---

## 2. Vấn đề nghiệp vụ cần giải quyết

| Vấn đề | Ảnh hưởng đến doanh nghiệp | Hướng xử lý trong module |
|---|---|---|
| Trái cây có hạn sử dụng ngắn | Dễ hư hỏng nếu không xuất kho đúng thứ tự | Quản lý Expiry Date và cảnh báo FEFO |
| Cần truy xuất nguồn gốc theo lô | Khó biết hàng đến từ vườn/nhà cung cấp nào | Mở rộng Lot/Batch với Harvest Date, Source Farm, Grade |
| Hàng nhập cần kiểm định chất lượng | Hàng lỗi có thể bị nhập chung vào kho bán | Tạo QC Check từ Receipt |
| Có hàng đạt một phần, hư một phần | Cần tách hàng đạt và hàng lỗi | Ghi nhận QC Result = Partial |
| Hàng hư/hàng lỗi cần được ghi nhận | Khó tính hao hụt và chi phí vận hành | Tạo Wastage Log |
| Xuất kho cần ưu tiên hàng cận hạn | Nếu không kiểm soát sẽ phát sinh tồn cận date | FEFO Batch Control và FEFO Suggestion |
| Giá bán thay đổi theo ngày | Sales cần bảng giá cập nhật liên tục | Tạo Daily Price Board từ CRM |
| CRM có thông tin thị trường nhưng chưa dùng để định giá | Dữ liệu khách hỏi, giá đối thủ, nhu cầu thị trường bị rời rạc | CRM Market Info và Generate Daily Price Board |

---

## 3. Danh sách module

| Tên kỹ thuật module | Tên hiển thị trên Odoo | Mục đích chính |
|---|---|---|
| `fruit_fresh_operations` | Fruit Fresh Operations | Mở rộng Lot/Batch, tạo QC Check, ghi nhận Wastage Log, kiểm soát FEFO, gợi ý lô xuất kho và tạo Daily Closing Report |
| `fruit_crm_daily_pricing` | Fruit CRM Daily Pricing | Thu thập thông tin thị trường từ CRM và tạo bảng giá trái cây hằng ngày cho Sales |

---

# 4. Module `fruit_fresh_operations`

## 4.1. Mục đích

`fruit_fresh_operations` mở rộng Odoo Inventory để hỗ trợ nghiệp vụ vận hành trái cây tươi.

Module tập trung vào các chức năng:

- Mở rộng thông tin Lot/Batch.
- Ghi nhận ngày thu hoạch, hạn sử dụng, phân hạng chất lượng và trạng thái QC.
- Tạo phiếu QC Check trực tiếp từ phiếu nhập hàng.
- Xử lý kết quả QC dạng `Passed`, `Failed`, `Partial`.
- Tạo Wastage Log cho phần hàng hư, hàng dập hoặc hàng không đạt chuẩn.
- Kiểm soát lô hàng theo nguyên tắc FEFO.
- Gợi ý lô hàng nên xuất trước.
- Tổng hợp báo cáo đóng ngày cho quản lý vận hành.

---

## 4.2. Luồng nghiệp vụ chính

```text
Receipt
→ Create QC Check
→ QC Result: Passed / Failed / Partial
→ Update Lot QC Status
→ Generate Wastage Log for rejected quantity
→ Monitor FEFO Batch Control
→ Use FEFO Suggestion for sales delivery
→ Generate Daily Fruit Closing Report
````

Diễn giải:

```text
Phiếu nhập hàng
→ Tạo phiếu kiểm định chất lượng QC
→ Ghi nhận kết quả QC: Đạt / Không đạt / Đạt một phần
→ Cập nhật trạng thái QC trên Lot/Batch
→ Tạo Wastage Log cho phần hàng bị loại
→ Theo dõi lô hàng cận hạn bằng FEFO Batch Control
→ Dùng FEFO Suggestion để gợi ý lô nên xuất trước
→ Tạo báo cáo đóng ngày Daily Fruit Closing Report
```

---

## 4.3. Mở rộng Lot/Batch

Module mở rộng model chuẩn `stock.lot` của Odoo bằng các trường dữ liệu đặc thù cho trái cây tươi.

| Trường                   | Ý nghĩa                                                |
| ------------------------ | ------------------------------------------------------ |
| `Harvest Date`           | Ngày thu hoạch của lô trái cây                         |
| `Expiry Date`            | Hạn sử dụng của lô hàng                                |
| `Grade`                  | Phân hạng chất lượng, ví dụ: Loại 1, Loại 2, Xuất khẩu |
| `QC Status`              | Trạng thái kiểm định chất lượng                        |
| `Source Farm / Supplier` | Nguồn vườn hoặc nhà cung cấp                           |
| `Days to Expiry`         | Số ngày còn lại đến hạn sử dụng                        |
| `FEFO Alert`             | Cảnh báo FEFO: Green, Yellow, Red, Expired             |
| `QC Note`                | Ghi chú kiểm định                                      |

Các trường này giúp hệ thống:

* Truy xuất nguồn gốc lô hàng.
* Theo dõi hạn sử dụng.
* Ưu tiên xuất kho theo FEFO.
* Theo dõi chất lượng từng lô hàng.
* Phân biệt hàng đạt chuẩn, hàng lỗi, hàng cần xử lý.

---

## 4.4. QC Check từ phiếu nhập kho

Module bổ sung nút `Create QC Check` trên phiếu nhập hàng `Receipt`.

Khi người dùng mở một phiếu nhập hàng, hệ thống cho phép tạo QC Check trực tiếp từ Receipt đó.

QC Check liên kết với:

* Phiếu nhập hàng.
* Nhà cung cấp.
* Sản phẩm.
* Lot/Batch.
* Số lượng nhận.
* Số lượng đạt.
* Số lượng bị loại.
* Kết quả kiểm định.

Ví dụ demo:

```text
Receipt: WH/IN/DEMO-QC-001
Product: Dứa nguyên trái Đà Lạt
Lot: BAT-2605-020
Received Qty: 500 kg
Accepted Qty: 460 kg
Rejected Qty: 40 kg
QC Result: Partial
```

Khi xác nhận QC Check:

* Lot/Batch được cập nhật `QC Status = Partial`.
* Ghi chú QC được lưu lại trên Lot/Batch.
* Hệ thống tạo Wastage Log cho 40 kg hàng lỗi.

---

## 4.5. Wastage Log

Module bổ sung model `fruit.wastage.log` để ghi nhận hàng hư, hàng lỗi, hàng dập, hàng hết hạn hoặc hàng không đạt chuẩn.

| Trường            | Ý nghĩa              |
| ----------------- | -------------------- |
| `Wastage No.`     | Mã log hao hụt       |
| `Date`            | Ngày ghi nhận        |
| `QC Check`        | Phiếu QC liên quan   |
| `Related Receipt` | Phiếu nhập liên quan |
| `Product`         | Sản phẩm             |
| `Lot/Batch`       | Lô hàng              |
| `Wastage Qty`     | Số lượng hao hụt     |
| `Unit Cost`       | Giá vốn đơn vị       |
| `Wastage Amount`  | Giá trị hao hụt      |
| `Reason Type`     | Nguyên nhân hao hụt  |
| `Status`          | Trạng thái xử lý     |

Các nguyên nhân hao hụt có thể gồm:

* Farm Damage
* Transport Damage
* QC Failed
* Storage Damage
* Expired
* Customer Return Damage
* Stock Count Difference

---

## 4.6. FEFO Batch Control

FEFO là viết tắt của `First Expired, First Out`, nghĩa là lô nào hết hạn trước thì cần được ưu tiên xuất trước.

Module tự động tính trạng thái cảnh báo FEFO dựa trên `Expiry Date`.

| Số ngày còn lại đến hạn | FEFO Alert |
| ----------------------: | ---------- |
|              Đã hết hạn | Expired    |
|                0–2 ngày | Red        |
|                3–5 ngày | Yellow     |
|             Trên 5 ngày | Green      |

Màn hình `FEFO Batch Control` giúp nhân viên kho và quản lý nhìn nhanh các lô hàng sắp hết hạn để ưu tiên xử lý.

---

## 4.7. FEFO Suggestion

`FEFO Suggestion` hỗ trợ gợi ý lô hàng nên xuất trước khi giao hàng.

Người dùng nhập:

| Thông tin         | Ý nghĩa           |
| ----------------- | ----------------- |
| `Product`         | Sản phẩm cần xuất |
| `Source Location` | Vị trí kho nguồn  |
| `Required Qty`    | Số lượng cần xuất |

Hệ thống sẽ:

1. Lấy các lô còn tồn trong kho.
2. Loại bỏ lô đã hết hạn hoặc có `QC Status = Failed`.
3. Sắp xếp lô theo hạn sử dụng gần nhất.
4. Gợi ý số lượng nên lấy từ từng lô.

Ví dụ:

```text
Cần xuất: 120 kg Cam xoàn

Lot A: còn 50 kg, hết hạn sau 2 ngày
Lot B: còn 80 kg, hết hạn sau 4 ngày
Lot C: còn 100 kg, hết hạn sau 10 ngày

Gợi ý:
- Lấy 50 kg từ Lot A
- Lấy 70 kg từ Lot B
```

---

## 4.8. Daily Fruit Closing Report

`Daily Fruit Closing Report` là báo cáo đóng ngày cho hoạt động vận hành trái cây.

Báo cáo tổng hợp:

| Chỉ tiêu                 | Ý nghĩa               |
| ------------------------ | --------------------- |
| `Receipt Qty`            | Tổng số lượng nhập    |
| `Delivery Qty`           | Tổng số lượng xuất    |
| `Wastage Qty`            | Tổng số lượng hao hụt |
| `Closing Stock Qty`      | Tồn kho cuối ngày     |
| `Estimated Sales Amount` | Doanh thu ước tính    |
| `Estimated COGS`         | Giá vốn ước tính      |
| `Wastage Amount`         | Giá trị hao hụt       |
| `Gross Profit`           | Lãi gộp ước tính      |
| `Red Lots`               | Số lô cảnh báo đỏ     |
| `Yellow Lots`            | Số lô cảnh báo vàng   |
| `Expired Lots`           | Số lô đã hết hạn      |

Báo cáo này giúp quản lý đánh giá nhanh tình hình nhập, xuất, tồn, hao hụt và hiệu quả vận hành trong ngày.

---

## 4.9. Các model chính của `fruit_fresh_operations`

| Model                          | Vai trò                                         |
| ------------------------------ | ----------------------------------------------- |
| `stock.lot`                    | Được mở rộng để lưu thông tin Lot/Batch đặc thù |
| `stock.picking`                | Được mở rộng để tạo QC Check từ Receipt         |
| `fruit.qc.check`               | Phiếu kiểm định chất lượng                      |
| `fruit.wastage.log`            | Ghi nhận hàng hư/hỏng/hao hụt                   |
| `fruit.fefo.suggestion.wizard` | Wizard gợi ý lô xuất theo FEFO                  |
| `fruit.daily.closing.report`   | Báo cáo đóng ngày                               |

---

# 5. Module `fruit_crm_daily_pricing`

## 5.1. Mục đích

`fruit_crm_daily_pricing` kết nối CRM với hoạt động định giá bán trái cây hằng ngày.

Trong thực tế, giá trái cây có thể thay đổi theo ngày do:

* Giá mua đầu vào thay đổi.
* Nhu cầu khách hàng thay đổi.
* Giá đối thủ thay đổi.
* Lượng tồn kho thay đổi.
* Có lô hàng sắp hết hạn cần đẩy bán nhanh.
* Thị trường biến động theo mùa, khu vực hoặc phân khúc khách hàng.

Module này giúp CRM không chỉ quản lý cơ hội bán hàng, mà còn trở thành nơi thu thập tín hiệu thị trường để hỗ trợ ra quyết định giá bán.

---

## 5.2. Luồng nghiệp vụ chính

```text
CRM Opportunity
→ Add Fruit Market Info
→ Generate Daily Fruit Price Board
→ Review Suggested Price
→ Confirm Price Board
→ Send to Sales Team
→ Apply to Odoo Pricelist
→ Sales uses daily price in Quotation
```

Diễn giải:

```text
Cơ hội bán hàng CRM
→ Nhập thông tin thị trường trái cây
→ Tạo bảng giá trái cây hằng ngày
→ Xem giá đề xuất
→ Quản lý duyệt bảng giá
→ Gửi bảng giá cho đội Sales
→ Tạo Pricelist trong Odoo
→ Sales dùng bảng giá khi lập báo giá
```

---

## 5.3. Fruit Market Info trong CRM

Module mở rộng `crm.lead` bằng tab `Fruit Market Info`.

Trong mỗi Opportunity, nhân viên CRM/Sales có thể ghi nhận thông tin thị trường như:

| Trường                      | Ý nghĩa                         |
| --------------------------- | ------------------------------- |
| `Product`                   | Sản phẩm khách quan tâm         |
| `Grade`                     | Phân hạng chất lượng            |
| `Expected Demand Qty`       | Số lượng khách dự kiến mua      |
| `Customer Target Price`     | Giá khách kỳ vọng               |
| `Competitor / Market Price` | Giá đối thủ hoặc giá thị trường |
| `Market Demand Level`       | Mức cầu thị trường              |
| `Region`                    | Khu vực thị trường              |
| `Expected Delivery Date`    | Ngày giao hàng dự kiến          |
| `Confidence (%)`            | Độ tin cậy của thông tin        |
| `Note`                      | Ghi chú từ nhân viên CRM/Sales  |

Ví dụ:

```text
Khách siêu thị A hỏi Cam xoàn Loại 1.
Số lượng dự kiến: 300 kg.
Giá khách mong muốn: 32,000 VND/kg.
Giá đối thủ: 31,500 VND/kg.
Nhu cầu thị trường: High.
Độ tin cậy: 80%.
```

---

## 5.4. Daily Fruit Price Board

`Daily Fruit Price Board` là bảng giá trái cây theo ngày.

Hệ thống tổng hợp dữ liệu CRM theo:

```text
Product + Grade + Price Date
```

Mỗi dòng bảng giá gồm:

| Trường                      | Ý nghĩa                          |
| --------------------------- | -------------------------------- |
| `Product`                   | Sản phẩm                         |
| `Grade`                     | Phân hạng                        |
| `Total CRM Demand Qty`      | Tổng nhu cầu ghi nhận từ CRM     |
| `Avg Customer Target Price` | Giá kỳ vọng trung bình của khách |
| `Avg Competitor Price`      | Giá đối thủ trung bình           |
| `Current Cost`              | Giá vốn hiện tại                 |
| `Target Margin (%)`         | Biên lợi nhuận mục tiêu          |
| `Demand Adjustment`         | Điều chỉnh giá theo mức cầu      |
| `Suggested Price`           | Giá hệ thống đề xuất             |
| `Final Approved Price`      | Giá cuối cùng quản lý duyệt      |
| `Final Margin (%)`          | Biên lợi nhuận cuối cùng         |
| `CRM Info Count`            | Số lượng bản ghi CRM được dùng   |

---

## 5.5. Công thức giá đề xuất

Module MVP sử dụng công thức đơn giản để phục vụ demo và giải thích trong đồ án:

```text
Suggested Price
= Cost × (1 + Target Margin %)
+ Demand Adjustment
+ Market Reference Adjustment
```

Trong đó:

| Thành phần                    | Ý nghĩa                                          |
| ----------------------------- | ------------------------------------------------ |
| `Cost`                        | Giá vốn hiện tại của sản phẩm                    |
| `Target Margin %`             | Biên lợi nhuận mục tiêu                          |
| `Demand Adjustment`           | Điều chỉnh giá theo tổng nhu cầu CRM             |
| `Market Reference Adjustment` | Điều chỉnh theo giá khách kỳ vọng và giá đối thủ |

Bảng điều chỉnh theo nhu cầu:

| Total CRM Demand Qty | Demand Adjustment |
| -------------------: | ----------------: |
|             Dưới 100 |                 0 |
|              100–299 |              +500 |
|              300–699 |            +1,000 |
|       Từ 700 trở lên |            +2,000 |

Ví dụ:

```text
Product: Cam xoàn Loại 1
Cost: 25,000 VND/kg
Target Margin: 20%
CRM Demand: 300 kg
Demand Adjustment: +1,000
Competitor Price: 31,500 VND/kg

Base Price = 25,000 × 1.2 = 30,000
Suggested Price ≈ 31,000 – 32,000 VND/kg
```

---

## 5.6. Duyệt và gửi bảng giá cho Sales

Daily Price Board có các trạng thái:

```text
Draft → Generated → Confirmed → Sent to Sales → Applied to Pricelist
```

Ý nghĩa:

| Trạng thái           | Ý nghĩa                                       |
| -------------------- | --------------------------------------------- |
| Draft                | Bảng giá mới tạo                              |
| Generated            | Đã tạo dòng giá từ dữ liệu CRM                |
| Confirmed            | Quản lý đã xác nhận bảng giá                  |
| Sent to Sales        | Bảng giá đã được gửi cho đội Sales            |
| Applied to Pricelist | Bảng giá đã được áp dụng thành Odoo Pricelist |
| Cancelled            | Bảng giá bị hủy                               |

Sau khi bảng giá được gửi cho Sales, nhân viên Sales có thể dùng giá đã duyệt để lập báo giá hoặc đơn bán hàng.

---

## 5.7. Apply to Odoo Pricelist

Module có thể tạo Odoo Pricelist từ Daily Price Board.

Ví dụ:

```text
Daily Price Board Date: 2026-05-17
Generated Pricelist: Fruit Daily Pricelist - 2026-05-17
```

Khi Sales tạo Quotation, người dùng có thể chọn Pricelist này để áp dụng giá bán trong ngày.

---

## 5.8. Các model chính của `fruit_crm_daily_pricing`

| Model                          | Vai trò                                 |
| ------------------------------ | --------------------------------------- |
| `crm.lead`                     | Được mở rộng bằng tab Fruit Market Info |
| `fruit.crm.market.info`        | Lưu tín hiệu thị trường từ CRM          |
| `fruit.daily.price.board`      | Bảng giá trái cây hằng ngày             |
| `fruit.daily.price.board.line` | Dòng chi tiết của bảng giá              |
| `product.pricelist`            | Pricelist được tạo từ bảng giá đã duyệt |

---

# 6. Cài đặt module

## 6.1. Yêu cầu môi trường

* Odoo 19
* Python/PostgreSQL theo bản cài Odoo
* Các app Odoo cần có:

  * Inventory / Stock
  * Product
  * CRM
  * Sales
  * Mail

---

## 6.2. Cấu trúc thư mục

Hai module nên được đặt trong thư mục `custom_addons`:

```text
custom_addons/
├── fruit_fresh_operations/
└── fruit_crm_daily_pricing/
```

---

## 6.3. Cấu hình `addons_path`

Mở file cấu hình Odoo, ví dụ:

```text
C:\Program Files\Odoo 19.0.20251013\server\odoo.conf
```

Thêm thư mục `custom_addons` vào `addons_path`.

Ví dụ:

```text
addons_path = C:\Program Files\Odoo 19.0.20251013\server\odoo\addons,C:\Program Files\Odoo 19.0.20251013\custom_addons
```

Sau khi sửa cấu hình, restart Odoo service.

---

## 6.4. Cài module từ giao diện Odoo

Các bước:

1. Bật Developer Mode.
2. Vào menu `Apps`.
3. Bấm `Update Apps List`.
4. Tìm module:

   * `Fruit Fresh Operations`
   * `Fruit CRM Daily Pricing`
5. Bấm `Activate`.

---

# 7. Kịch bản demo

## 7.1. Demo QC Partial và Wastage

```text
1. Mở Receipt WH/IN/DEMO-QC-001.
2. Bấm Create QC Check.
3. Kiểm tra Product, Lot và Received Qty.
4. Nhập:
   - Received Qty = 500
   - Accepted Qty = 460
   - Rejected Qty = 40
   - QC Result = Partial
5. Bấm Confirm QC.
6. Mở Lot BAT-2605-020 và kiểm tra QC Status = Partial.
7. Mở Wastage Logs và kiểm tra hệ thống đã tạo log 40 kg.
```

---

## 7.2. Demo FEFO Batch Control

```text
1. Mở Lots/Serial Numbers.
2. Nhập Expiry Date cho một số Lot.
3. Tạo các Lot có trạng thái Red, Yellow, Green.
4. Mở Fruit Operations → FEFO Batch Control.
5. Kiểm tra các lô Red/Yellow được hiển thị.
```

---

## 7.3. Demo FEFO Suggestion

```text
1. Mở Fruit Operations → FEFO Suggestion.
2. Chọn Product.
3. Chọn Source Location.
4. Nhập Required Qty.
5. Bấm Compute Suggestion.
6. Kiểm tra hệ thống gợi ý lô theo hạn sử dụng gần nhất.
```

---

## 7.4. Demo Daily Fruit Closing

```text
1. Mở Fruit Operations → Daily Fruit Closing.
2. Chọn Report Date và Main Stock Location.
3. Nhập Sales Amount và Estimated COGS nếu cần.
4. Bấm Compute Report.
5. Kiểm tra Wastage Qty, Closing Stock, FEFO Alerts và Gross Profit.
```

---

## 7.5. Demo CRM tạo bảng giá ngày

```text
1. Mở CRM Opportunity.
2. Thêm Fruit Market Info:
   - Product
   - Grade
   - Expected Qty
   - Customer Target Price
   - Competitor Price
   - Market Demand Level
3. Mở Fruit Daily Pricing → Daily Price Boards.
4. Tạo Daily Price Board cho cùng ngày.
5. Bấm Generate From CRM.
6. Kiểm tra Suggested Price và Final Price.
7. Bấm Confirm.
8. Bấm Send to Sales.
9. Bấm Apply to Pricelist.
10. Tạo Sales Quotation và chọn Pricelist vừa sinh ra.
```

---

# 8. Trạng thái hiện tại

Các module hiện đang ở mức MVP phục vụ đồ án ERP.

## 8.1. Đã thực hiện

* Tạo custom module `fruit_fresh_operations`.
* Tạo custom module `fruit_crm_daily_pricing`.
* Cài đặt được module trên Odoo local.
* Mở rộng Lot/Batch bằng các trường đặc thù.
* Tạo QC Check từ Receipt.
* Ghi nhận QC Partial.
* Tạo Wastage Log.
* Tạo FEFO Batch Control.
* Tạo FEFO Suggestion.
* Tạo Daily Fruit Closing Report.
* Mở rộng CRM để thu thập thông tin thị trường.
* Tạo Daily Price Board từ CRM.
* Tạo Pricelist từ bảng giá ngày.

## 8.2. Hạn chế hiện tại

* QC được xây dựng bằng custom module nhẹ, không thay thế hoàn toàn Odoo Quality app.
* Daily Closing là báo cáo quản trị vận hành, chưa phải báo cáo tài chính đầy đủ.
* Một số chỉ tiêu tài chính như doanh thu, COGS, gross profit đang ở mức ước tính.
* Module chưa triển khai đầy đủ luồng kế toán tài chính chuẩn.
* Chưa tự động hóa toàn bộ quy trình điều chuyển kho sau QC trong mọi tình huống.
* Pricelist hiện tạo theo Product, chưa xử lý sâu theo từng phân khúc khách hàng hoặc khu vực.
* Cần nạp dữ liệu demo đầy đủ để kiểm thử end-to-end.

---

# 9. Hướng phát triển tiếp theo

Các hướng có thể mở rộng trong tương lai:

* Tự động tạo Internal Transfer sau QC:

  * Hàng đạt → Stock.
  * Hàng lỗi → Damage/Scrap Location.
* Tích hợp Supplier Return và Purchase Claim cho hàng lỗi đầu vào.
* Tích hợp Customer Return và Credit Note cho hàng lỗi từ khách trả.
* Tạo dashboard BI cho hao hụt, tồn kho, FEFO và giá bán.
* Bổ sung workflow duyệt bảng giá nhiều cấp.
* Tích hợp AI/ML để dự báo nhu cầu và đề xuất giá.
* Tạo báo cáo xu hướng giá đối thủ.
* Tạo bảng giá riêng theo phân khúc khách hàng.
* Tích hợp thông báo bảng giá qua email hoặc kênh nội bộ.
* Kết nối với E-commerce để cập nhật giá bán online trong ngày.

```
```
