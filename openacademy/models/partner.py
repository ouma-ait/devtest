# -*- coding: utf-8 -*-
from odoo import fields, models, api


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
