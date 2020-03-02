# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import json
import math
import re

from werkzeug import urls

from odoo import fields, http


class Academy(http.Controller):
    @http.route(['/my/', '/my/home'], website=True, auth='user')
    def index(self, **kw):
        Partners = http.request.env['res.partner']
        return http.request.render('openacademy.sessionMenu', {
            'partners': Partners.search([])
        })

    @http.route('/my/<model("res.partner"):partner>/', auth='public', website=True)
    def partner(self, partner):
        sessions = list(partner.inst_ids)
        return http.request.render('openacademy.sessionList', {
            'session': sessions
        })

    @http.route(['/my/session/<model("openacademy.session"):session>/',
                 '/my/home/session/<model("openacademy.session"):session>/'], auth='user', website=True)
    def session(self, session):
        return http.request.render('openacademy.temp', {
            'session': session
        })

    @http.route(['/my/session/details/<model("openacademy.session"):session>/'], auth='user', website=True)
    def sess(self, session):
        return http.request.render('openacademy.portal_my_details', {
            'session': session
        })

    @http.route(['/my/session/details/edit/', '/my/home/session/details/edit/'], auth='user', website=True)
    def session_edit(self, id_ses, **kw):
        session = http.request.env['openacademy.session'].search([('id', '=', id_ses)])

        session.name = kw['name']
        session.duration = kw['duration']
        session.start_date = kw['start_date']
        session.seats = kw['seats']
        session.taken_seats = kw['taken_seats']

        return http.request.redirect('/my/home')
