# 🍎 Đồ án triển khai hệ thống ERP cho doanh nghiệp phân phối trái cây bằng Odoo 19

## Giới thiệu

Đây là repository chứa các **custom module Odoo** được phát triển trong đồ án môn **Hệ thống Hoạch định Nguồn lực Doanh nghiệp (ERP)**.

Dự án mô phỏng việc triển khai hệ thống ERP cho một doanh nghiệp hoạt động trong lĩnh vực **thu mua, phân phối và bán lẻ trái cây tươi**. Mục tiêu của dự án là số hóa quy trình nghiệp vụ, nâng cao hiệu quả quản lý và hỗ trợ ra quyết định thông qua việc ứng dụng Odoo ERP.

Repository này bao gồm hai custom module được xây dựng nhằm mở rộng các chức năng chuẩn của Odoo để đáp ứng các nghiệp vụ đặc thù của ngành trái cây tươi.

---

# Thông tin dự án

- **Tên dự án:** ERP Implementation for Fruit Distribution Business
- **Nền tảng ERP:** Odoo 19
- **Loại dự án:** Đồ án học phần ERP
- **Số lượng thành viên:** 5

---

# Vai trò của tôi

**Business Analyst – Phân hệ Kế toán (Accounting)**

Trong dự án, tôi đảm nhận các công việc sau:

- Phân tích quy trình nghiệp vụ của phân hệ Kế toán bằng BPMN.
- Tham gia chuẩn hóa dữ liệu Master Data và Transaction Data.
- Thực hiện import dữ liệu lên hệ thống Odoo.
- Cấu hình và kiểm thử các nghiệp vụ:
  - Vendor Bill
  - Customer Invoice
  - Payment
  - Theo dõi công nợ
- Kiểm thử luồng nghiệp vụ giữa các phân hệ Sales – Inventory – Accounting.
- Tham gia viết tài liệu và chuẩn bị nội dung demo hệ thống.

---

# Mục tiêu của dự án

Dự án được xây dựng nhằm giải quyết một số bài toán thường gặp trong doanh nghiệp kinh doanh trái cây:

- Quản lý lô hàng (Lot/Batch).
- Kiểm định chất lượng đầu vào.
- Theo dõi hạn sử dụng.
- Xuất kho theo nguyên tắc FEFO.
- Quản lý hàng hư, hàng hao hụt.
- Xây dựng bảng giá bán theo ngày.
- Hỗ trợ báo cáo vận hành.

---

# Các phân hệ triển khai

Hệ thống sử dụng các phân hệ chuẩn của Odoo:

- CRM
- Purchase
- Inventory
- Sales
- Accounting

Ngoài ra, nhóm phát triển thêm hai custom module:

- Fruit Fresh Operations
- Fruit CRM Daily Pricing

---

# Công nghệ sử dụng

- Odoo 19
- PostgreSQL
- SQL
- Microsoft Excel
- BPMN
- Git
- GitLab
- Windows VPS

---

# Cấu trúc repository

```
custom_addons/
├── fruit_fresh_operations/
└── fruit_crm_daily_pricing/
```

---

# Chức năng chính

## Fruit Fresh Operations

Module mở rộng phân hệ Kho nhằm hỗ trợ các nghiệp vụ:

- Quản lý Lot/Batch.
- Theo dõi ngày thu hoạch.
- Theo dõi hạn sử dụng.
- Kiểm định chất lượng (QC Check).
- Quản lý hàng hư (Wastage Log).
- Kiểm soát FEFO.
- Gợi ý lô hàng xuất trước.
- Báo cáo đóng ngày.

---

## Fruit CRM Daily Pricing

Module mở rộng CRM nhằm:

- Thu thập thông tin thị trường.
- Tổng hợp nhu cầu khách hàng.
- Đề xuất giá bán theo ngày.
- Sinh bảng giá.
- Tạo Pricelist trên Odoo.

---

# Quy trình nghiệp vụ

```
Thu mua
    ↓
Nhập kho
    ↓
Kiểm định chất lượng (QC)
    ↓
Quản lý tồn kho
    ↓
Bán hàng
    ↓
Xuất kho
    ↓
Lập hóa đơn
    ↓
Thanh toán
```

---

# Hướng dẫn cài đặt

## Yêu cầu

- Odoo 19
- PostgreSQL
- Inventory
- Purchase
- Sales
- CRM

## Cài đặt

1. Sao chép hai module vào thư mục:

```
custom_addons/
```

2. Cập nhật đường dẫn `addons_path` trong file `odoo.conf`.

3. Khởi động lại dịch vụ Odoo.

4. Vào **Apps** và cài đặt:

- Fruit Fresh Operations
- Fruit CRM Daily Pricing

---

# Kịch bản demo

Có thể trình diễn các nghiệp vụ sau:

- Kiểm định chất lượng (QC).
- Ghi nhận hàng hao hụt.
- FEFO Batch Control.
- FEFO Suggestion.
- Daily Fruit Closing Report.
- CRM Daily Pricing.
- Sinh bảng giá bán.

---

# Hình ảnh minh họa

```
docs/
└── screenshots/
```

Bao gồm:

- Đăng nhập hệ thống.
- Inventory.
- Sales.
- Accounting.
- CRM.
- Dashboard.
- Daily Pricing.

---

# Tài liệu

```
docs/
```

Bao gồm:

- Báo cáo đồ án.
- BPMN.
- Use Case Diagram.
- Activity Diagram.

---

# Trạng thái dự án

### Đã hoàn thành

- Phân tích nghiệp vụ.
- Thiết kế BPMN.
- Cài đặt Odoo 19.
- Xây dựng custom module.
- Chuẩn hóa dữ liệu.
- Import dữ liệu.
- Kiểm thử hệ thống.
- Demo các quy trình nghiệp vụ.

---

# Hướng phát triển

Trong tương lai, dự án có thể mở rộng:

- Dashboard Business Intelligence.
- Dự báo nhu cầu bằng AI/ML.
- Dashboard Power BI.
- Báo cáo tồn kho.
- Báo cáo hao hụt.
- Dashboard doanh thu.
- Dashboard lợi nhuận.
- Tối ưu thuật toán định giá.

---
