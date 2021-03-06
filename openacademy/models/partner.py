# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _


class Partner(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
    instructor = fields.Boolean("Instructor", default=False)
    sessions_count = fields.Integer(string="Sessions count", compute='_get_sessions_count')

    session_ids = fields.Many2many('openacademy.session',
                                   string="Attended Sessions", readonly=True)

    inst_ids = fields.One2many('openacademy.session', 'instructor_id', string="Sessions")

    def _get_sessions_count(self):
        self.sessions_count = len(self.inst_ids)

    invoice_count = fields.Integer(string="count invoice", compute="_compute_invoice_count")

    def _compute_invoice_count(self):
        self.invoice_count = self.env['account.move'].search_count([('partner_id', '=', self.id)])

    def facturer1(self):
        id_product_template = self.env['product.template'].search([('name', 'ilike', 'Session')]).id
        id_product_product = self.env['product.product'].search([('product_tmpl_id', '=', id_product_template)]).id
        list_price_product_template = self.env['product.template'].search([('name', 'ilike', 'Session')]).list_price
        data = {
            'partner_id': self.id,
            'type': 'out_invoice',  # for the customer
            "invoice_line_ids": [],
        }
        list = []
        quantity = 0
        val = 0
        for line in self.session_ids:
            if line.state == 'validate':
                val = val + 1
                quantity = quantity + line.duration
                line.state = 'invoiced'

        if len(self.session_ids) == 0:
            raise exceptions.ValidationError("This instructor has no sessions")
        if val == 0:
            raise exceptions.ValidationError("A session not validated can not be invoiced")

        line1 = {
            "name": line.name,
            "quantity": quantity,
            "price_unit": list_price_product_template,
            "product_id": id_product_product,

        }
        list.append(line1)
        for element in list:
            data["invoice_line_ids"].append((0, 0, element))
        invoice = self.env['account.move'].create(data)

        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]

        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = invoices.id

        context = {
            'default_type': 'out_invoice',
        }

        action['context'] = context
        return action

    def facturer2(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_invoice',
        }

        action['context'] = context
        return action

    def print_invoice(self):
        list_invoices = []
        invoices = self.mapped('invoice_ids.id')
        for line in invoices:
            list_invoices.append(line)
        invoice_last_id = max(list_invoices)
        invoice = self.env['account.move'].search([('id', '=', invoice_last_id)])
        return self.env.ref('account.account_invoices').report_action(invoice)