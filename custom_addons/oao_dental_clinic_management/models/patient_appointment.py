from datetime import timedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PatientAppointment(models.Model):
    _name = 'patient.appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'appointment_serial'
    _description = 'Patient Clinic Appointment'

    appointment_serial = fields.Char(string="Appointment Serial", required=True, duplicate=False, readonly=True,
                                     index=True, default=lambda self: _("New Appointment"))
    patient_id = fields.Many2one('patient.patient', string="Patient Name", tracking=True)
    name = fields.Char('Meeting Subject', required=False)
    dentist_id = fields.Many2one('clinic.employee', string="Dentist", domain=[('employee_type.name', '=', 'Dentist')])
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    product_id = fields.Many2one('product.product', string="Product")
    allday = fields.Boolean('All Day', default=False)
    duration = fields.Float('Duration', compute='_compute_duration', store=True, readonly=False)
    appointment_status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Appointment Confirmed'),
        ('completed_appointment', 'Appointment Completed'),
        ('cancelled', 'Appointment Cancelled'),
    ], required=False, string="Appointment Status", tracking=True, default='draft')
    urgency_level = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ], required=True, string="Urgency Level", tracking=True)
    start = fields.Datetime(
        'Start', required=True, tracking=True, default=fields.Date.today,
        help="Start date of an event, without time for full days events")
    stop = fields.Datetime(
        'Stop', required=True, tracking=True, default=lambda self: fields.Datetime.today() + timedelta(hours=0.5),
        compute='_compute_stop', readonly=False, store=True,
        help="Stop date of an event, without time for full days events")

    @api.depends('start', 'duration')
    def _compute_stop(self):
        duration_field = self._fields['duration']
        self.env.remove_to_compute(duration_field, self)
        for event in self:
            event.stop = event.start and event.start + timedelta(minutes=round((event.duration or 1.0) * 60))
            if event.allday:
                event.stop -= timedelta(seconds=1)

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if not start or not stop:
            return 0
        duration = (stop - start).total_seconds() / 3600
        return round(duration, 2)

    @api.depends('stop', 'start')
    def _compute_duration(self):
        for event in self.with_context(dont_notify=True):
            event.duration = self._get_duration(event.start, event.stop)

    @api.model
    def create(self, vals):  # save button in the form view
        if vals.get('dentist_id') and vals.get('start'):
            start_time = fields.Datetime.from_string(vals['start'])
            stop_time = start_time + timedelta(hours=vals.get('duration', 0.5))
            existing_appointments = self.env['patient.appointment'].search([
                ('dentist_id', '=', vals['dentist_id']),
                ('start', '<', stop_time),
                ('stop', '>', start_time)
            ])
            if existing_appointments:
                raise ValidationError(_("The dentist already has an appointment scheduled during this time."))

        if vals.get('patient_id') and vals.get('start'):
            start_time = fields.Datetime.from_string(vals['start'])
            stop_time = start_time + timedelta(hours=vals.get('duration', 0.5))
            existing_appointments_patient = self.env['patient.appointment'].search([
                ('patient_id', '=', vals['patient_id']),
                ('start', '<', stop_time),
                ('stop', '>', start_time)
            ])
            if existing_appointments_patient:
                raise ValidationError(_("The patient already has an appointment scheduled during this time."))

        if vals.get('appointment_serial', _('New Appointment')) == _('New Appointment'):
            vals['appointment_serial'] = self.env['ir.sequence'].next_by_code('patient.appointment.sequence') or _(
                'New Appointment')
        return super(PatientAppointment, self).create(vals)

    def write(self, vals):
        # Check for overlapping appointments with the same dentist on update
        for record in self:
            start_time = fields.Datetime.from_string(vals.get('start', record.start))
            duration = vals.get('duration', record.duration)
            stop_time = start_time + timedelta(hours=duration)

            if 'dentist_id' in vals or 'start' in vals or 'duration' in vals:
                existing_appointments_dentist = self.env['patient.appointment'].search([
                    ('dentist_id', '=', vals.get('dentist_id', record.dentist_id.id)),
                    ('start', '<', stop_time),
                    ('stop', '>', start_time),
                    ('id', '!=', record.id)
                ])
                if existing_appointments_dentist:
                    raise ValidationError(_("The dentist already has an appointment scheduled during this time."))

            if 'patient_id' in vals or 'start' in vals or 'duration' in vals:
                existing_appointments_patient = self.env['patient.appointment'].search([
                    ('patient_id', '=', vals.get('patient_id', record.patient_id.id)),
                    ('start', '<', stop_time),
                    ('stop', '>', start_time),
                    ('id', '!=', record.id)
                ])
                if existing_appointments_patient:
                    raise ValidationError(_("The patient already has an appointment scheduled during this time."))

        return super(PatientAppointment, self).write(vals)
