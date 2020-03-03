# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import models, fields, api, exceptions, _


class Session(models.Model):
    _name = 'openacademy.session'
    _description = "OpenAcademy Sessions"
    _inherit = 'mail.thread'

    name = fields.Char(required=True)
    # start_date = fields.Date()
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    # testy = fields.Float(string="Multi")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    color = fields.Integer()
    biography = fields.Html()

    # For the workflow
    state = fields.Selection([
        ('draft', "Draft"),
        ('confirm', "IN Progress"),
        ('validate', "Validated"),
    ], default='draft', string='State')

    button_invoice = fields.Boolean(string='Button Invoice')
    invoice_ids = fields.One2many("account.move", "session_id")
    invoice_count = fields.Integer(string="count invoice", compute="_compute_invoice_count")

    # instructor_id = fields.Many2one('res.partner', string="Instructor")
    instructor_id = fields.Many2one('res.partner', string="Instructor",
                                    domain=['|', ('instructor', '=', True),
                                            ('category_id.name', 'ilike', "Teacher")])

    course_id = fields.Many2one('openacademy.course',
                                ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')

    end_date = fields.Date(string="End Date", store=True,
                           compute='_get_end_date', inverse='_set_end_date')

    attendees_count = fields.Integer(
        string="Attendees count", compute='_get_attendees_count', store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)

    # computed field
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.duration = (r.end_date - r.start_date).days + 1

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    # onchange : warn about negative number of seats / attendee_ids > seats
    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': _("Incorrect 'seats' value"),
                    'message': _("The number of available seats may not be negative"),

                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': _("Too many attendees"),
                    'message': _("Increase seats or remove excess attendees"),

                },
            }

    # @api.onchange('seats', 'attendee_ids')
    # def _count_seat_duration(self):
    #     # set auto-changing field
    #     self.testy = self.seats < len(self.attendee_ids);
    #     # Can optionally return a warning and domains
    #     return {
    #         'warning': {
    #             'title': "Something bad happened",
    #             'message': "It was very bad indeed",
    #         }
    #     }

    # constraints python
    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError("A session's instructor can't be an attendee")

    def confirm(self):
        self.write({
            'state': 'confirm'
        })

    def validate(self):
        self.write({
            'state': 'validate',
        })

    def invoice(self):
        id_product_template = self.env['product.template'].search([('name', 'ilike', 'Session')]).id
        id_product_product = self.env['product.product'].search([('product_tmpl_id', '=', id_product_template)]).id
        list_price_product_template = self.env['product.template'].search([('name', 'ilike', 'Session')]).list_price
        self.button_invoice = True
        data = {
            'session_id': self.id,
            'partner_id': self.instructor_id.id,
            'type': 'in_invoice',
            'invoice_date': self.date,
            "invoice_line_ids": [],
        }

        line = {
            "name": self.name,
            "quantity": self.duration,
            "price_unit": list_price_product_template,
            "product_id": id_product_product,

        }
        data["invoice_line_ids"].append((0, 0, line))
        invoice2 = self.env['account.move'].create(data)

    def action_view_invoice(self):
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

    def _compute_invoice_count(self):
        self.invoice_count = self.env['account.move'].search_count([('session_id', '=', self.id)])
    