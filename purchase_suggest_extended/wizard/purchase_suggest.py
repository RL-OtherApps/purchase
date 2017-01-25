# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare
# from openerp.exceptions import UserError
import logging

logger = logging.getLogger(__name__)


class PurchaseSuggestGenerate(models.TransientModel):
    _inherit = 'purchase.suggest.generate'

    @api.model
    def _prepare_suggest_line(self, product_id, qty_dict):
        sline = super(PurchaseSuggestGenerate, self)._prepare_suggest_line(
            product_id, qty_dict)
        op = qty_dict['orderpoint']
        qty = sline['qty_to_order']
        reste = op.qty_multiple > 0 and qty % op.qty_multiple or 0.0
        if float_compare(
                reste, 0.0, precision_rounding=op.product_uom.rounding) > 0:
            qty += op.qty_multiple - reste
            sline['qty_to_order'] = sline['qty_to_order']
        return sline


class PurchaseSuggest(models.TransientModel):
    _inherit = 'purchase.suggest'

    replenishment_cost = fields.Float(
        related='product_id.replenishment_cost',
        store=True,
    )
    order_amount = fields.Monetary(
        string='Order Amount',
        compute='_compute_order_amount',
        store=True,
    )
    currency_id = fields.Many2one(
        related='product_id.currency_id',
        store=True,
    )
    virtual_available = fields.Float(
        string='Forecasted Quantity',
        compute='_compute_virtual_available',
        store=True,
        digits=dp.get_precision('Product Unit of Measure'),
        help="in the unit of measure of the product"
    )
    rotation = fields.Float(
        related='orderpoint_id.rotation',
        store=True,
    )

    @api.multi
    @api.depends('qty_to_order', 'replenishment_cost')
    def _compute_order_amount(self):
        for rec in self:
            rec.order_amount = rec.replenishment_cost * rec.qty_to_order

    @api.multi
    @api.depends(
        'qty_available',
        'outgoing_qty',
        'incoming_qty',
        'draft_po_qty',
    )
    def _compute_virtual_available(self):
        for rec in self:
            rec.qty_available = rec.qty_available - rec.outgoing_qty \
                + rec.incoming_qty + rec.draft_po_qty
