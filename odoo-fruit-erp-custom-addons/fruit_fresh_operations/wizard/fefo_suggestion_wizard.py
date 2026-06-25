from odoo import fields, models

from odoo.exceptions import UserError

class FruitFefoSuggestionWizard(models.TransientModel):
    _name = "fruit.fefo.suggestion.wizard"
    _description = "FEFO Suggestion Wizard"

    product_id = fields.Many2one("product.product", string="Product", required=True)
    required_qty = fields.Float(string="Required Qty", required=True)
    location_id = fields.Many2one("stock.location", string="Source Location", required=True)

    line_ids = fields.One2many(
        "fruit.fefo.suggestion.line",
        "wizard_id",
        string="Suggested Lots",
    )

    def action_compute_suggestion(self):
        self.line_ids.unlink()

        quants = self.env["stock.quant"].search([
            ("product_id", "=", self.product_id.id),
            ("location_id", "child_of", self.location_id.id),
            ("lot_id", "!=", False),
            ("quantity", ">", 0),
        ])

        lot_rows = []
        for quant in quants:
            lot = quant.lot_id
            available_qty = quant.quantity - quant.reserved_quantity

            if available_qty <= 0:
                continue
            if lot.x_qc_status == "failed":
                continue

            if lot.x_fefo_alert == "expired":

                if lot.x_fefo_alert == "expired" or (lot.x_expiry_date and lot.x_expiry_date < fields.Date.today()):

                    continue

            lot_rows.append({
                "lot": lot,
                "available_qty": available_qty,
                "expiry_date": lot.x_expiry_date or fields.Date.today(),
                "days_to_expiry": lot.x_days_to_expiry,
                "alert": lot.x_fefo_alert,
            })


        if not lot_rows:
            raise UserError("Không tìm thấy bất kỳ lô hàng nào còn tồn kho cho sản phẩm này tại vị trí đã chọn (hoặc tất cả các lô hiện có đều đã hết hạn hoặc bị đánh giá QC hỏng). Vui lòng thực hiện Nhập kho (Receipt) và QC Đạt trước khi chạy Gợi ý FEFO.")

        lot_rows.sort(key=lambda r: (r["expiry_date"], r["lot"].name))

        remaining = self.required_qty
        seq = 1

        for row in lot_rows:
            if remaining <= 0:
                break

            suggested_qty = min(row["available_qty"], remaining)

            self.env["fruit.fefo.suggestion.line"].create({
                "wizard_id": self.id,
                "sequence": seq,
                "lot_id": row["lot"].id,
                "available_qty": row["available_qty"],
                "suggested_qty": suggested_qty,
                "expiry_date": row["expiry_date"],
                "days_to_expiry": row["days_to_expiry"],
                "alert_level": row["alert"],
                "reason": "FEFO: ưu tiên lô có hạn sử dụng gần nhất.",
            })

            remaining -= suggested_qty
            seq += 1

        return {
            "type": "ir.actions.act_window",
            "res_model": "fruit.fefo.suggestion.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }


class FruitFefoSuggestionLine(models.TransientModel):
    _name = "fruit.fefo.suggestion.line"
    _description = "FEFO Suggestion Line"

    wizard_id = fields.Many2one("fruit.fefo.suggestion.wizard")
    sequence = fields.Integer(string="Seq")
    lot_id = fields.Many2one("stock.lot", string="Suggested Lot")
    available_qty = fields.Float(string="Available Qty")
    suggested_qty = fields.Float(string="Suggested Qty")
    expiry_date = fields.Date(string="Expiry Date")
    days_to_expiry = fields.Integer(string="Days to Expiry")
    alert_level = fields.Selection([
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("red", "Red"),
        ("expired", "Expired"),
    ], string="Alert")

    reason = fields.Char(string="Reason")

    reason = fields.Char(string="Reason")

