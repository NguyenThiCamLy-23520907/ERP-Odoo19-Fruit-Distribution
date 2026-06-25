import csv  # FIX: Bổ sung thư viện csv bị thiếu để tránh lỗi NameError hệ thống
import io
import json
import re
import unicodedata
import requests

from odoo import models, fields, api
from odoo.exceptions import UserError

GITHUB_CSV_URL = "https://raw.githubusercontent.com/TuyenVont/odoo-fruit-erp-custom-addons/main/data_daily/gia_trai_cay_tong_hop.csv"

class CrmLead(models.Model):
    _inherit = "crm.lead"

    fruit_market_info_ids = fields.One2many(
        "fruit.crm.market.info",
        "lead_id",
        string="Fruit Market Info"
    )

    fruit_market_info_count = fields.Integer(
        string="Fruit Market Info Count",
        compute="_compute_fruit_market_info_count"
    )

    # Lưu lịch sử giá tạm thời để có thể Khôi phục (Restore) khi cần sửa đổi tay
    previous_prices = fields.Text("Previous Prices JSON")

    @api.depends('fruit_market_info_ids')
    def _compute_fruit_market_info_count(self):
        for lead in self:
            lead.fruit_market_info_count = len(lead.fruit_market_info_ids)

    # Chuẩn hóa text tiếng Việt không dấu, xóa từ thừa
    def _normalize_text(self, text):
        if not text:
            return ""
        text = str(text).lower().strip()
        text = text.replace("đ", "d")
        text = unicodedata.normalize("NFD", text)
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        noise_words = {
            "kg", "g", "gr", "gram", "trai", "hop", "tui", "vi",
            "loai", "l1", "rpl", "vf", "select", "coop", "co", "op",
            "online", "tu", "khoang", "tro", "len", "dong", "goi",
            "mieng", "nhap", "khau", "noi", "dia", "trung", "my",
            "phap", "nam", "phi", "uc", "newzealand", "new", "zealand",
            "chon", "loc", "size", "combo", "khay", "nuoc", "tuoi",
            "sach", "bich", "lon", "vua", "to",
        }
        tokens = [t for t in text.split() if t not in noise_words and not t.isdigit()]
        return " ".join(tokens)

    # Lấy nhóm trái cây gốc để định vị Mapping (Fuzzy Keyword)
    def _extract_fruit_key(self, product_name):
        normalized_name = self._normalize_text(product_name)
        fruit_aliases = [
            ("thanh long", ["thanh long"]),
            ("dua luoi", ["dua luoi"]),
            ("dua hau", ["dua hau"]),
            ("dua gang", ["dua gang"]),
            ("dua le", ["dua le"]),
            ("dua xiem", ["dua xiem"]),
            ("dua", ["dua", "thom", "khom"]),   # dứa / thơm / khóm
            ("chuoi", ["chuoi"]),
            ("buoi", ["buoi"]),
            ("cam", ["cam"]),
            ("tao", ["tao"]),
            ("oi", ["oi"]),
            ("xoai", ["xoai"]),
            ("man", ["man"]),
            ("le", ["le"]),
            ("quyt", ["quyt"]),
            ("mit", ["mit"]),
            ("sapoche", ["sapoche", "sapo"]),
            ("bo", ["bo"]),
            ("coc", ["coc"]),
            ("kiwi", ["kiwi"]),
            ("nho", ["nho"]),
            ("chanh day", ["chanh day"]),
            ("du du", ["du du"]),
            ("dao", ["dao"]),
            ("mang cut", ["mang cut"]),
            ("sau rieng", ["sau rieng"]),
            ("chom chom", ["chom chom"]),
            ("vai", ["vai"]),
            ("nhan", ["nhan"]),
            ("cherry", ["cherry"]),
            ("blueberry", ["blueberry"]),
            ("avocado", ["avocado"]),
            ("chanh", ["chanh"]),
        ]
        for canonical_key, aliases in fruit_aliases:
            for alias in aliases:
                if re.search(r"(^|\s)%s(\s|$)" % re.escape(alias), normalized_name):
                    return canonical_key
        tokens = normalized_name.split()
        return tokens[0] if tokens else False

    # Đo độ tương đồng chuỗi văn bản
    def _match_score(self, a, b):
        a = self._normalize_text(a)
        b = self._normalize_text(b)
        if not a or not b:
            return 0
        if a == b or a in b or b in a:
            return 1
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio()

    def sync_market_price_from_github(self):
        """Update Market Info theo bộ key mềm, CSV tự bung ra 1-nhiều sản phẩm Odoo phù hợp"""
        try:
            response = requests.get(GITHUB_CSV_URL, timeout=20)
            response.raise_for_status()
            text = response.content.decode("utf-8-sig")
        except Exception as e:
            raise UserError(f"Lỗi khi lấy CSV từ GitHub: {e}")

        reader = csv.DictReader(io.StringIO(text))
        price_groups = {}

        # Gom nhóm giá trung bình từ file dữ liệu crawl về
        for row in reader:
            product_name = row.get("Tên Sản Phẩm") or row.get("product_name")
            price_raw = row.get("Giá Bán Hiện Tại") or row.get("market_price")
            if not product_name or not price_raw:
                continue
            try:
                price = float(str(price_raw).replace(",", "").replace(".", "").strip())
            except Exception:
                continue
            fruit_key = self._extract_fruit_key(product_name)
            if not fruit_key:
                continue
            price_groups.setdefault(fruit_key, []).append(price)

        if not price_groups:
            raise UserError("Không tìm thấy dữ liệu giá hợp lệ trong file CSV.")

        market_price_by_key = {k: sum(v)/len(v) for k,v in price_groups.items() if v}

        # Tìm toàn bộ sản phẩm đang kinh doanh trong hệ thống Odoo của bạn
        ProductTemplate = self.env["product.product"].sudo().search([("active","=",True),("sale_ok","=",True)])
        match_threshold = 0.45
        total_updated_count = 0

        for lead in self:
            updated_count = 0
            previous_prices_dict = {}
            unmatched_products = []

            for product in ProductTemplate:
                product_key = self._extract_fruit_key(product.name)
                selected_price = False

                # Ánh xạ thông minh: Nếu cùng nhóm từ khóa gốc (Cóc, Ổi, Cam, Mít)
                if product_key and product_key in market_price_by_key:
                    selected_price = market_price_by_key[product_key]
                else:
                    # Fallback fuzzy nếu không khớp nhóm
                    product_norm = self._normalize_text(product.name)
                    best_score = 0
                    for csv_key, csv_price in market_price_by_key.items():
                        score = self._match_score(csv_key, product_norm)
                        if score >= match_threshold and score > best_score:
                            best_score = score
                            selected_price = csv_price

                if selected_price:
                    info_exist = self.env["fruit.crm.market.info"].search([
                        ("lead_id", "=", lead.id),
                        ("product_id", "=", product.id),
                        ("grade", "=", "grade_1"),
                        ("info_date", "=", fields.Date.today()),
                    ], limit=1)

                    previous_prices_dict[str(product.id)] = (
                        info_exist.customer_target_price if info_exist else product.list_price
                    )

                    vals = {
                        "lead_id": lead.id,
                        "product_id": product.id,
                        "grade": "grade_1",
                        "customer_target_price": selected_price,
                        "competitor_price": selected_price,
                        "info_date": fields.Date.today(),
                        "expected_qty": 0.0,
                        "state": "draft",
                    }

                    if info_exist:
                        info_exist.write(vals)
                    else:
                        self.env["fruit.crm.market.info"].create(vals)
                    updated_count += 1
                else:
                    unmatched_products.append(product.name)

            lead.previous_prices = json.dumps(previous_prices_dict)
            total_updated_count += updated_count

        unmatched_summary = ""
        if unmatched_products:
            sample = ", ".join(unmatched_products[:5])
            more = f"... (+{len(unmatched_products) - 5})" if len(unmatched_products) > 5 else ""
            unmatched_summary = f" | Không match: {len(unmatched_products)} SP ({sample}{more})"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Đồng bộ giá thị trường thành công",
                "message": (
                    f"Đã cập nhật {total_updated_count} dòng Market Info."
                    f"{unmatched_summary}"
                ),
                "type": "success",
                "sticky": True,
            },
        }

    def restore_previous_prices(self):
        """Khôi phục lại giá trị bảng đệm trước khi đồng bộ (Tuyệt đối không đổi đơn giá gốc sản phẩm)"""
        for lead in self:
            if not lead.previous_prices:
                continue
            
            previous_prices_dict = json.loads(lead.previous_prices)
            for product_id, old_price in previous_prices_dict.items():
                # Tìm dòng đệm tương ứng của cơ hội này trong ngày để trả lại giá cũ
                info_line = self.env["fruit.crm.market.info"].search([
                    ("lead_id", "=", lead.id),
                    ("product_id", "=", int(product_id)),
                    ("info_date", "=", fields.Date.today())
                ], limit=1)
                
                if info_line:
                    info_line.write({
                        'customer_target_price': old_price,
                        'competitor_price': old_price
                    })
            
            lead.previous_prices = ""
            
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Restore Prices",
                "message": "Đã khôi phục dữ liệu giá bảng đệm về phiên bản trước thành công.",
                "type": "success",
                "sticky": False
            }
        }