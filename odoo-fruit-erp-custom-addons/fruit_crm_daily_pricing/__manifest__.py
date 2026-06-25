{
    "name": "Fruit CRM Daily Pricing Sync",
    "version": "1.0",
    "category": "Sales",
    "summary": "Sync fruit market price from GitHub CSV to Odoo",
    "author": "ERP Student",  # Thêm tên bạn để tránh lỗi WARNING Missing author trong log cũ
    "license": "LGPL-3",    # Thêm license để tránh WARNING trong log cũ
    "depends": ["crm", "product"],
'data': [
    'security/ir.model.access.csv',
    'views/menu.xml',
    'views/crm_lead_views.xml',
    'views/fruit_crm_market_info_views.xml',
    'views/fruit_daily_price_board_views.xml',
],
    "installable": True,
    "application": True,    # <--- Đổi thành True để tìm thấy ngay lập tức trên giao diện Apps
    "auto_install": False,
}