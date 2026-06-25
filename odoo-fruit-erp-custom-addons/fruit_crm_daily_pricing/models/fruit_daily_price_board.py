from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta


class FruitDailyPriceBoard(models.Model):
    _name = "fruit.daily.price.board"
    _description = "Fruit Daily Price Board"
    _order = "price_date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Board Name", default="New", copy=False)

    price_date = fields.Date(
        string="Price Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    sales_team_id = fields.Many2one(
        "crm.team",
        string="Sales Team",
        tracking=True,
    )

    product_categ_id = fields.Many2one(
        "product.category",
        string="Product Category",
        help=(
            "Nếu chọn, chỉ tạo bảng giá cho sản phẩm thuộc category này và category con. "
            "Nếu để trống, lấy tất cả sản phẩm sale_ok=True."
        ),
    )

    target_margin_percent = fields.Float(
        string="Target Margin (%)",
        default=20.0,
        help="Biên lợi nhuận mục tiêu dùng để tính giá đề xuất.",
    )

    line_ids = fields.One2many(
        "fruit.daily.price.board.line",
        "board_id",
        string="Price Lines",
    )

    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Generated Pricelist",
        readonly=True,
    )

    state = fields.Selection([
        ("draft", "Draft"),
        ("generated", "Generated"),
        ("confirmed", "Confirmed"),
        ("sent", "Sent to Sales"),
        ("applied", "Applied to Pricelist"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft", tracking=True)

    note = fields.Text(string="Note")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == "New":
                rec.name = "Daily Fruit Price Board - %s" % rec.price_date
        return records

    def _get_demand_adjustment(self, total_qty, base_price):
        """Demand adjustment as percentage of base_price based on total CRM demand qty."""
        if total_qty >= 100:
            return base_price * 0.05
        if total_qty >= 50:
            return base_price * 0.03
        if total_qty >= 10:
            return base_price * 0.01
        return 0.0

    def _get_confidence_weighted_average(self, infos, field_name):
        """Weighted average by confidence and expected quantity for a given field."""
        total_weight = 0.0
        total_value = 0.0

        for info in infos:
            value = info[field_name]
            if not value:
                continue

            confidence_weight = max(info.confidence or 0.0, 1.0) / 100.0
            qty_weight = max(info.expected_qty or 0.0, 1.0)
            final_weight = confidence_weight * qty_weight

            total_value += value * final_weight
            total_weight += final_weight

        return (total_value / total_weight) if total_weight else 0.0

    def _round_price(self, price):
        """Round to nearest 100. If price < 100, round to 2 decimals."""
        if price < 100:
            return round(price, 2)
        return round(price / 100) * 100

    def action_generate_from_crm(self):
        """
        Daily Price Board = bảng giá ngày cho toàn bộ sản phẩm.
        Market Information = tín hiệu thị trường/CRM để điều chỉnh giá nếu có.
        """
        for board in self:
            board.line_ids.unlink()

            product_domain = [
                ("sale_ok", "=", True),
                ("active", "=", True),
            ]

            if board.product_categ_id:
                product_domain.append(
                    ("categ_id", "child_of", board.product_categ_id.id)
                )

            products = self.env["product.product"].search(product_domain)

            if not products:
                raise UserError(
                    "Không tìm thấy sản phẩm nào để tạo bảng giá. "
                    "Vui lòng kiểm tra Product Category hoặc sản phẩm sale_ok."
                )

            info_domain = [
                ("info_date", "=", board.price_date),
                ("product_id", "in", products.ids),
                "|",
                ("state", "=", "draft"),
                ("price_board_id", "=", board.id),
            ]

            if board.sales_team_id:
                info_domain.append(("sales_team_id", "=", board.sales_team_id.id))

            all_infos = self.env["fruit.crm.market.info"].search(info_domain)

            info_grouped = defaultdict(lambda: self.env["fruit.crm.market.info"])
            for info in all_infos:
                info_grouped[(info.product_id.id, info.grade)] |= info

            used_infos = self.env["fruit.crm.market.info"]
            lines_to_create = []

            for product in products:
                current_cost = product.standard_price or 0.0
                margin = board.target_margin_percent or 0.0

                if margin < 100:
                    base_price = (
                        current_cost / (1 - margin / 100.0)
                        if current_cost
                        else 0.0
                    )
                else:
                    base_price = current_cost

                product_grades = [
                    grade
                    for (product_id, grade) in info_grouped
                    if product_id == product.id
                ]

                if product_grades:
                    for grade in product_grades:
                        group_infos = info_grouped[(product.id, grade)]

                        total_qty = sum(group_infos.mapped("expected_qty"))

                        avg_target_price = self._get_confidence_weighted_average(
                            group_infos,
                            "customer_target_price",
                        )

                        avg_competitor_price = self._get_confidence_weighted_average(
                            group_infos,
                            "competitor_price",
                        )

                        demand_adjustment = self._get_demand_adjustment(
                            total_qty,
                            base_price,
                        )

                        market_reference = (
                            avg_competitor_price
                            if avg_competitor_price > 0
                            else avg_target_price
                        )

                        if market_reference > 0:
                            suggested_price = (
                                base_price * 0.6
                                + market_reference * 0.4
                                + demand_adjustment
                            )
                        else:
                            suggested_price = base_price + demand_adjustment

                        final_price = self._round_price(suggested_price)

                        lines_to_create.append({
                            "board_id": board.id,
                            "product_id": product.id,
                            "grade": grade,
                            "total_crm_demand_qty": total_qty,
                            "avg_customer_target_price": avg_target_price,
                            "avg_competitor_price": avg_competitor_price,
                            "current_cost": current_cost,
                            "target_margin_percent": margin,
                            "demand_adjustment": demand_adjustment,
                            "suggested_price": final_price,
                            "final_price": final_price,
                            "market_info_count": len(group_infos),
                            "note": "Generated from CRM market information.",
                        })

                        used_infos |= group_infos

                else:
                    final_price = self._round_price(base_price)

                    lines_to_create.append({
                        "board_id": board.id,
                        "product_id": product.id,
                        "grade": "grade_1",
                        "total_crm_demand_qty": 0.0,
                        "avg_customer_target_price": 0.0,
                        "avg_competitor_price": 0.0,
                        "current_cost": current_cost,
                        "target_margin_percent": margin,
                        "demand_adjustment": 0.0,
                        "suggested_price": final_price,
                        "final_price": final_price,
                        "market_info_count": 0,
                        "note": "Generated from product cost only. No market info for this date.",
                    })

            self.env["fruit.daily.price.board.line"].create(lines_to_create)

            if used_infos:
                used_infos.write({
                    "state": "used",
                    "price_board_id": board.id,
                })

            board.state = "generated"

    def action_confirm(self):
        for board in self:
            if not board.line_ids:
                raise UserError("Bảng giá chưa có dòng giá.")
            board.state = "confirmed"

    def action_send_to_sales(self):
        for board in self:
            if board.state not in ["confirmed", "generated", "applied"]:
                raise UserError("Chỉ gửi bảng giá sau khi đã generate hoặc confirm.")

            board.state = "sent"

            message = "Daily Fruit Price Board %s đã sẵn sàng cho Sales Team." % board.name
            board.message_post(body=message)

            users = self.env["res.users"]

            if board.sales_team_id:
                if "member_ids" in board.sales_team_id._fields:
                    users |= board.sales_team_id.member_ids
                if board.sales_team_id.user_id:
                    users |= board.sales_team_id.user_id

            if not users:
                users = self.env.user

            for user in users:
                board.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=user.id,
                    summary="Daily Fruit Price Board Ready",
                    note=message,
                )

    def action_apply_to_pricelist(self):
        """
        Apply final prices to a new pricelist.

        Odoo pricelist item does not support grade directly;
        duplicate products are consolidated and highest final_price wins.
        """
        for board in self:
            if not board.line_ids:
                raise UserError("Không có dòng giá để apply vào Pricelist.")

            product_price_map = {}

            for line in board.line_ids:
                if line.final_price <= 0:
                    continue

                product_id = line.product_id.id

                if (
                    product_id not in product_price_map
                    or line.final_price > product_price_map[product_id]
                ):
                    product_price_map[product_id] = line.final_price

            if not product_price_map:
                raise UserError(
                    "Tất cả dòng giá đều có final_price <= 0. "
                    "Không thể tạo Pricelist."
                )

            currency = self.env.company.currency_id

            pricelist = self.env["product.pricelist"].create({
                "name": "Fruit Daily Pricelist - %s" % board.price_date,
                "currency_id": currency.id,
            })

            items = []

            for product_id, final_price in product_price_map.items():
                items.append({
                    "pricelist_id": pricelist.id,
                    "applied_on": "0_product_variant",
                    "product_id": product_id,
                    "compute_price": "fixed",
                    "fixed_price": final_price,
                    "min_quantity": 0,
                    "date_start": board.price_date,
                    "date_end": board.price_date + timedelta(days=1),
                })

            self.env["product.pricelist.item"].create(items)

            board.pricelist_id = pricelist.id
            board.state = "applied"
            board.message_post(body="Đã tạo Pricelist: %s" % pricelist.display_name)

            return {
                "type": "ir.actions.act_window",
                "name": "Generated Pricelist",
                "res_model": "product.pricelist",
                "res_id": pricelist.id,
                "view_mode": "form",
                "target": "current",
            }

    def action_cancel(self):
        for board in self:
            board.state = "cancelled"


class FruitDailyPriceBoardLine(models.Model):
    _name = "fruit.daily.price.board.line"
    _description = "Fruit Daily Price Board Line"
    _order = "product_id, grade"

    board_id = fields.Many2one(
        "fruit.daily.price.board",
        string="Price Board",
        required=True,
        ondelete="cascade",
    )

    product_id = fields.Many2one(
        "product.product",
        string="Fruit Product",
        required=True,
    )

    grade = fields.Selection([
        ("premium", "Premium"),
        ("grade_1", "Loại 1"),
        ("grade_2", "Loại 2"),
        ("export", "Xuất khẩu"),
        ("vietgap", "VietGAP"),
        ("reject", "Reject"),
    ], string="Grade", required=True)

    total_crm_demand_qty = fields.Float(string="Total CRM Demand Qty")
    avg_customer_target_price = fields.Float(string="Avg Customer Target Price")
    avg_competitor_price = fields.Float(string="Avg Competitor Price")

    current_cost = fields.Float(string="Current Cost")
    target_margin_percent = fields.Float(string="Target Margin (%)")
    demand_adjustment = fields.Float(string="Demand Adjustment")

    suggested_price = fields.Float(string="Suggested Price")
    final_price = fields.Float(string="Final Approved Price")

    margin_percent = fields.Float(
        string="Final Margin (%)",
        compute="_compute_margin_percent",
        store=True,
    )

    market_info_count = fields.Integer(string="CRM Info Count")
    note = fields.Char(string="Note")

    @api.depends("current_cost", "final_price")
    def _compute_margin_percent(self):
        for line in self:
            if line.final_price > 0:
                line.margin_percent = (
                    (line.final_price - line.current_cost)
                    / line.final_price
                ) * 100
            else:
                line.margin_percent = 0.0