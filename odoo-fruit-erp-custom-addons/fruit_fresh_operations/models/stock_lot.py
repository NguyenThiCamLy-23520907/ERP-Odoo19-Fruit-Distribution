from datetime import date
from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    x_harvest_date = fields.Date(string="Harvest Date")
    x_expiry_date = fields.Date(string="Expiry Date")

    x_grade = fields.Selection([
        ("premium", "Premium"),
        ("grade_1", "Loại 1"),
        ("grade_2", "Loại 2"),
        ("export", "Xuất khẩu"),
        ("reject", "Reject"),
    ], string="Grade")

    x_qc_status = fields.Selection([
        ("pending", "Pending"),
        ("passed", "Passed"),
        ("failed", "Failed"),
        ("partial", "Partial"),
    ], string="QC Status", default="pending")

    x_source_farm = fields.Char(string="Source Farm / Supplier")
    x_qc_note = fields.Text(string="QC Note")

    x_days_to_expiry = fields.Integer(
        string="Days to Expiry",
        compute="_compute_fefo_alert",
        store=True,
    )

    x_fefo_alert = fields.Selection([
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("red", "Red"),
        ("expired", "Expired"),
    ], string="FEFO Alert", compute="_compute_fefo_alert", store=True)

    @api.depends("x_expiry_date")
    def _compute_fefo_alert(self):
        today = date.today()
        for lot in self:
            if not lot.x_expiry_date:
                lot.x_days_to_expiry = 0
                lot.x_fefo_alert = False
                continue

            days = (lot.x_expiry_date - today).days
            lot.x_days_to_expiry = days

            if days < 0:
                lot.x_fefo_alert = "expired"
            elif days <= 2:
                lot.x_fefo_alert = "red"
            elif days <= 5:
                lot.x_fefo_alert = "yellow"
            else:
                lot.x_fefo_alert = "green"