import csv
import difflib
import io
import re
import unicodedata
import requests
from odoo import api, fields, models
from odoo.exceptions import UserError

# ---------------------------------------------------------------------------
# Noise words stripped before matching (Vietnamese + common packaging terms)
# ---------------------------------------------------------------------------
_NOISE_WORDS = {
    "kg", "g", "gr", "gram", "trai", "hop", "tui", "vi", "loai", "l1",
    "rpl", "vf", "select", "coop", "co", "op", "online", "tu", "khoang",
    "tro", "len", "dong", "goi", "mieng", "nhap", "khau", "noi", "dia",
    "trung", "my", "phap", "nam", "phi", "uc", "newzealand", "new", "zealand",
    "chon", "loc", "size", "combo", "khay", "nuoc", "tuoi", "sach",
    "nguyen", "trai", "bich", "lon", "vua", "to",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
}

# ---------------------------------------------------------------------------
# Fruit canonical groups + aliases (normalized, no diacritics)
# ---------------------------------------------------------------------------
_FRUIT_ALIASES = [
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
    ("me", ["me"]),
    ("sung", ["sung"]),
    ("dau", ["dau"]),
    ("cherry", ["cherry"]),
    ("blueberry", ["blueberry"]),
    ("raspberry", ["raspberry"]),
    ("avocado", ["avocado"]),
    ("chanh", ["chanh"]),
]


def _normalize_text(text):
    """Lowercase, remove Vietnamese diacritics, strip noise words."""
    if not text:
        return ""
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split() if t not in _NOISE_WORDS]
    return " ".join(tokens)


def _extract_fruit_key(product_name):
    """Return the canonical fruit group key for a product name, or None."""
    norm = _normalize_text(product_name)
    for canonical, aliases in _FRUIT_ALIASES:
        for alias in aliases:
            if re.search(r"(^|\s)%s(\s|$)" % re.escape(alias), norm):
                return canonical
    tokens = norm.split()
    return tokens[0] if tokens else None


def _fuzzy_score(a_norm, b_norm):
    """SequenceMatcher ratio between two already-normalized strings."""
    if not a_norm or not b_norm:
        return 0.0
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()


class FruitCrmMarketInfo(models.Model):
    _name = "fruit.crm.market.info"
    _description = "Fruit CRM Market Information"
    _order = "info_date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Reference", default="New", copy=False)

    lead_id = fields.Many2one(
        "crm.lead",
        string="Opportunity",
        required=True,
        ondelete="cascade",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="lead_id.partner_id",
        store=True,
        readonly=True,
    )

    salesperson_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        related="lead_id.user_id",
        store=True,
        readonly=True,
    )

    sales_team_id = fields.Many2one(
        "crm.team",
        string="Sales Team",
        related="lead_id.team_id",
        store=True,
        readonly=True,
    )

    info_date = fields.Date(
        string="Info Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    expected_delivery_date = fields.Date(
        string="Expected Delivery Date",
        tracking=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Fruit Product",
        required=True,
        tracking=True,
    )

    grade = fields.Selection([
        ("premium", "Premium"),
        ("grade_1", "Loại 1"),
        ("grade_2", "Loại 2"),
        ("export", "Xuất khẩu"),
        ("vietgap", "VietGAP"),
        ("reject", "Reject"),
    ], string="Grade", required=True, default="grade_1", tracking=True)

    expected_qty = fields.Float(
        string="Expected Demand Qty",
        required=True,
        default=1.0,
        tracking=True,
    )

    uom_id = fields.Many2one(
        "uom.uom",
        string="UoM",
        related="product_id.uom_id",
        readonly=True,
        store=True,
    )

    customer_target_price = fields.Float(
        string="Customer Target Price",
        help="Giá khách kỳ vọng/mong muốn.",
        tracking=True,
    )

    competitor_price = fields.Float(
        string="Competitor / Market Price",
        help="Giá đối thủ hoặc giá thị trường ghi nhận từ CRM.",
        tracking=True,
    )

    market_demand_level = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("very_high", "Very High"),
    ], string="Market Demand Level", default="medium", tracking=True)

    region = fields.Char(string="Region / Market Area")

    confidence = fields.Float(
        string="Confidence (%)",
        default=80,
        help="Độ tin cậy của thông tin thị trường, từ 0 đến 100.",
    )

    note = fields.Text(string="Market Note")

    state = fields.Selection([
        ("draft", "Draft"),
        ("used", "Used in Price Board"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft", tracking=True)

    price_board_id = fields.Many2one(
        "fruit.daily.price.board",
        string="Generated Price Board",
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Product matching helpers
    # ------------------------------------------------------------------

    def _find_best_product(self, ten_sp, sku=None):
        """
        Find the best matching product.product for a crawled product name.

        Priority:
          1. Exact SKU / default_code match
          2. Same fruit group key (canonical) + highest fuzzy score >= 0.50
          3. Fallback: any product with fuzzy score >= 0.55 against full name

        Returns (product, score) or (None, 0).
        """
        # 1. SKU exact match
        if sku:
            by_sku = self.env["product.product"].search(
                [("default_code", "=", sku), ("sale_ok", "=", True)], limit=1
            )
            if by_sku:
                return by_sku, 1.0

        crawled_norm = _normalize_text(ten_sp)
        crawled_key = _extract_fruit_key(ten_sp)

        # Build a candidate pool: products sharing the same fruit group key
        # plus a broad ilike on the first meaningful token as safety net
        candidate_ids = set()

        if crawled_key:
            # Search by canonical key word (already normalized, no diacritics)
            # We search the original Odoo name with ilike on the first token of the key
            key_token = crawled_key.split()[0]
            by_key = self.env["product.product"].search(
                [("sale_ok", "=", True), ("active", "=", True),
                 ("name", "ilike", key_token)],
                limit=200,
            )
            candidate_ids.update(by_key.ids)

        # Also add products whose normalized name shares the first crawled token
        first_tokens = [t for t in crawled_norm.split() if len(t) >= 3][:2]
        for token in first_tokens:
            by_token = self.env["product.product"].search(
                [("sale_ok", "=", True), ("active", "=", True),
                 ("name", "ilike", token)],
                limit=100,
            )
            candidate_ids.update(by_token.ids)

        if not candidate_ids:
            return None, 0.0

        candidates = self.env["product.product"].browse(list(candidate_ids))

        best_product = None
        best_score = 0.0

        for product in candidates:
            product_norm = _normalize_text(product.name)
            product_key = _extract_fruit_key(product.name)

            # Bonus: same fruit group
            group_bonus = 0.15 if (crawled_key and product_key == crawled_key) else 0.0

            fuzzy = _fuzzy_score(crawled_norm, product_norm)
            score = fuzzy + group_bonus

            # Substring bonus: if product name is fully contained in crawled name
            if product_norm and product_norm in crawled_norm:
                score += 0.10

            if score > best_score:
                best_score = score
                best_product = product

        # Accept if combined score >= 0.50
        if best_score >= 0.50 and best_product:
            return best_product, best_score

        return None, 0.0

    # ------------------------------------------------------------------
    # GitHub sync action
    # ------------------------------------------------------------------

    def action_sync_price_from_github(self):
        url = (
            "https://raw.githubusercontent.com/TuyenVont/"
            "odoo-fruit-erp-custom-addons/main/data_daily/gia_trai_cay_tong_hop.csv"
        )

        try:
            response = requests.get(url, timeout=15)
        except Exception as e:
            raise UserError(f"Không thể kết nối tới GitHub để lấy dữ liệu: {str(e)}")

        if response.status_code != 200:
            raise UserError("Tải file từ GitHub thất bại. Vui lòng kiểm tra lại đường dẫn link raw.")

        csv_data = io.StringIO(response.text)
        reader = csv.DictReader(csv_data)

        total_rows = 0
        created_count = 0
        skipped_no_price = 0
        unmatched_names = []

        lead_scraped = self.env["crm.lead"].search(
            [("name", "=", "Khảo sát giá sàn tự động")], limit=1
        )
        if not lead_scraped:
            lead_scraped = self.env["crm.lead"].create({
                "name": "Khảo sát giá sàn tự động",
                "description": "Gom nhóm dữ liệu giá thu thập tự động hàng ngày từ Co.op, BHX hoặc nguồn thị trường.",
            })

        for row in reader:
            total_rows += 1
            row_clean = {str(k).strip().lower(): v for k, v in row.items() if k}

            sku = (
                row_clean.get("mã sku")
                or row_clean.get("sku")
                or row_clean.get("ma sku")
                or ""
            ).strip()

            ten_sp = (
                row_clean.get("tên sản phẩm")
                or row_clean.get("ten san pham")
                or row_clean.get("name")
                or ""
            ).strip()

            gia_san_raw = (
                row_clean.get("giá bán hiện tại")
                or row_clean.get("gia ban hien tai")
                or row_clean.get("price")
                or ""
            )

            nguon_san = (
                row_clean.get("nguồn dữ liệu")
                or row_clean.get("nguon du lieu")
                or row_clean.get("source")
                or "Thị trường"
            )

            try:
                gia_san = float(str(gia_san_raw).replace(",", "").strip()) if gia_san_raw else 0.0
            except ValueError:
                gia_san = 0.0

            if not ten_sp or gia_san <= 0:
                skipped_no_price += 1
                continue

            best_product, score = self._find_best_product(ten_sp, sku=sku or None)

            if not best_product:
                unmatched_names.append(ten_sp)
                continue

            self.create({
                "lead_id": lead_scraped.id,
                "product_id": best_product.id,
                "grade": "grade_1",
                "info_date": fields.Date.context_today(self),
                "expected_delivery_date": fields.Date.context_today(self),
                "expected_qty": 1.0,
                "competitor_price": gia_san,
                "customer_target_price": gia_san,
                "market_demand_level": "medium",
                "region": nguon_san,
                "confidence": round(score * 100, 1),
                "note": (
                    f"Sản phẩm crawl: {ten_sp}\n"
                    f"SKU tham khảo: {sku or 'N/A'}\n"
                    f"Product Odoo map: {best_product.name} (ID {best_product.id})\n"
                    f"Match score: {score:.2f}"
                ),
                "state": "draft",
            })
            created_count += 1

        unmatched_summary = ""
        if unmatched_names:
            unmatched_summary = (
                f" | Không match: {len(unmatched_names)} sản phẩm"
                f" ({', '.join(unmatched_names[:5])}"
                f"{'...' if len(unmatched_names) > 5 else ''})"
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Đồng bộ hoàn tất",
                "message": (
                    f"Tổng {total_rows} dòng CSV | "
                    f"Match thành công: {created_count} | "
                    f"Bỏ qua (không có giá): {skipped_no_price}"
                    f"{unmatched_summary}"
                ),
                "sticky": True,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == "New":
                rec.name = "MI-%s-%s" % (
                    rec.info_date.strftime("%Y%m%d") if rec.info_date else "DATE",
                    rec.id,
                )
        return records
