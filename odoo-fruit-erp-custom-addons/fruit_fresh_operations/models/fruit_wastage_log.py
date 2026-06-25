from odoo import api, fields, models


class FruitWastageLog(models.Model):
    _name = "fruit.wastage.log"
    _description = "Fruit Wastage Log"
    _order = "date desc, id desc"

    name = fields.Char(string="Wastage No.", default="New", copy=False)
    date = fields.Date(string="Date", default=fields.Date.context_today)

    qc_check_id = fields.Many2one("fruit.qc.check", string="QC Check")
    picking_id = fields.Many2one("stock.picking", string="Related Receipt")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    lot_id = fields.Many2one("stock.lot", string="Lot/Batch")
    qty = fields.Float(string="Wastage Qty", required=True)

    uom_id = fields.Many2one(
        "uom.uom",
        string="UoM",
        related="product_id.uom_id",
        store=True,
        readonly=True,
    )

    unit_cost = fields.Float(
        string="Unit Cost",
        related="product_id.standard_price",
        store=True,
        readonly=False,
    )

    amount = fields.Float(string="Wastage Amount", compute="_compute_amount", store=True)

    reason_type = fields.Selection([
        ("farm_damage", "Farm Damage"),
        ("transport_damage", "Transport Damage"),
        ("qc_failed", "QC Failed"),
        ("storage_damage", "Storage Damage"),
        ("expired", "Expired"),
        ("customer_return_damage", "Customer Return Damage"),
        ("stock_count_difference", "Stock Count Difference"),
    ], string="Reason Type", required=True)

    note = fields.Text(string="Note")

    state = fields.Selection([
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft")

    @api.depends("qty", "unit_cost")
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.qty * rec.unit_cost

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("fruit.wastage.log") or "WL/New"
        return super().create(vals_list)

    def action_post(self):
        for rec in self:
            rec.state = "posted"