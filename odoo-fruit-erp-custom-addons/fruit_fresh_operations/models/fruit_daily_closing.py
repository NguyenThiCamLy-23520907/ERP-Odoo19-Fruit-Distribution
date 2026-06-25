from odoo import fields, models


class FruitDailyClosingReport(models.Model):
    _name = "fruit.daily.closing.report"
    _description = "Daily Fruit Closing Report"
    _order = "report_date desc, id desc"

    name = fields.Char(string="Report No.", default="New", copy=False)
    report_date = fields.Date(string="Report Date", default=fields.Date.context_today, required=True)
    location_id = fields.Many2one("stock.location", string="Main Stock Location", required=True)

    receipt_qty = fields.Float(string="Receipt Qty")
    delivery_qty = fields.Float(string="Delivery Qty")
    wastage_qty = fields.Float(string="Wastage Qty")
    closing_stock_qty = fields.Float(string="Closing Stock Qty")

    sales_amount = fields.Float(string="Estimated Sales Amount")
    estimated_cogs = fields.Float(string="Estimated COGS")
    wastage_amount = fields.Float(string="Wastage Amount")
    gross_profit = fields.Float(string="Estimated Gross Profit")

    red_lot_count = fields.Integer(string="Red Lots")
    yellow_lot_count = fields.Integer(string="Yellow Lots")
    expired_lot_count = fields.Integer(string="Expired Lots")

    note = fields.Text(string="Note")

    def action_compute_report(self):
        for rec in self:
            wastages = self.env["fruit.wastage.log"].search([
                ("date", "=", rec.report_date),
                ("state", "!=", "cancelled"),
            ])

            quants = self.env["stock.quant"].search([
                ("location_id", "child_of", rec.location_id.id),
            ])

            rec.wastage_qty = sum(wastages.mapped("qty"))
            rec.wastage_amount = sum(wastages.mapped("amount"))
            rec.closing_stock_qty = sum(quants.mapped("quantity"))

            rec.red_lot_count = self.env["stock.lot"].search_count([
                ("x_fefo_alert", "=", "red")
            ])
            rec.yellow_lot_count = self.env["stock.lot"].search_count([
                ("x_fefo_alert", "=", "yellow")
            ])
            rec.expired_lot_count = self.env["stock.lot"].search_count([
                ("x_fefo_alert", "=", "expired")
            ])

            rec.gross_profit = rec.sales_amount - rec.estimated_cogs - rec.wastage_amount