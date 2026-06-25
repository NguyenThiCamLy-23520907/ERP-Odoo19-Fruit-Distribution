from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    fruit_qc_check_ids = fields.One2many(
        "fruit.qc.check",
        "picking_id",
        string="Fruit QC Checks",
    )

    fruit_qc_count = fields.Integer(
        string="QC Count",
        compute="_compute_fruit_qc_count",
    )

    def _compute_fruit_qc_count(self):
        for picking in self:
            picking.fruit_qc_count = len(picking.fruit_qc_check_ids)

    def action_create_fruit_qc_check(self):
        self.ensure_one()

        if self.picking_type_code != "incoming":
            raise UserError("QC Check chỉ tạo từ phiếu nhập hàng / Receipt.")

        move_lines = self.move_line_ids.filtered(lambda l: l.product_id)
        if not move_lines:
            raise UserError("Phiếu nhập chưa có dòng sản phẩm.")

        line = move_lines[0]

        if not line.lot_id:
            raise UserError("Bạn cần nhập Lot/Serial Number trước khi tạo QC Check.")

        lot = line.lot_id
        if not lot and line.lot_name:
            # Tìm hoặc tự động tạo Lot record từ chuỗi lot_name mà người dùng nhập
            lot = self.env["stock.lot"].search([
                ("name", "=", line.lot_name),
                ("product_id", "=", line.product_id.id),
                ("company_id", "=", self.company_id.id),
            ], limit=1)
            if not lot:
                lot = self.env["stock.lot"].create({
                    "name": line.lot_name,
                    "product_id": line.product_id.id,
                    "company_id": self.company_id.id,
                })
            line.write({"lot_id": lot.id})

        if not line.lot_id:
            raise UserError("Bạn cần nhập Lot/Serial Number và bấm Lưu trước khi tạo QC Check. Hãy kiểm tra chắc chắn sản phẩm đã được bật cấu hình theo dõi theo Lot.")

        received_qty = line.quantity or line.qty_done or line.reserved_uom_qty or 0

        qc = self.env["fruit.qc.check"].create({
            "picking_id": self.id,
            "product_id": line.product_id.id,
            "lot_id": line.lot_id.id,
            "received_qty": received_qty,
            "accepted_qty": received_qty,
            "rejected_qty": 0,
            "qc_result": "passed",
        })

        return {
            "type": "ir.actions.act_window",
            "name": "Fruit QC Check",
            "res_model": "fruit.qc.check",
            "res_id": qc.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_fruit_qc_checks(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Fruit QC Checks",
            "res_model": "fruit.qc.check",
            "view_mode": "list,form",
            "domain": [("picking_id", "=", self.id)],
            "context": {"default_picking_id": self.id},
        }
