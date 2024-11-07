from datetime import date
from odoo import api, fields, models


class AppointmentRequests(models.Model):
    _name = 'appointment.requests'
    _description = "Appointment Requests from Web"

    name = fields.Char('Meeting Subject', default="Web Appointment Requests", readonly=True)
    patient_id = fields.Many2one('patient.patient', string="Patient Name", tracking=True, readonly=True)
    dentist_id = fields.Many2one('clinic.employee', string="Dentist", domain=[('employee_type.name', '=', 'Dentist')], readonly=True)
    appointment_day = fields.Date(string="Request Day", readonly=True)
    is_contacted = fields.Boolean(string="Is Contacted?")

    @api.model
    def create(self, vals):
        vals['appointment_day'] = date.today()

        return super(AppointmentRequests, self).create(vals)