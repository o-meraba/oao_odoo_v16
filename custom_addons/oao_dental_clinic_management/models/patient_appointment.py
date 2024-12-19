from datetime import timedelta, datetime

from dateutil.utils import today

from odoo import fields, models, api, _
from odoo.addons.test_convert.tests.test_env import record
from odoo.exceptions import ValidationError
from odoo.service.server import start


class PatientAppointment(models.Model):
    _name = 'patient.appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'appointment_serial'
    _description = 'Patient Clinic Appointment'

    appointment_serial = fields.Char(string="Appointment Serial", required=True, duplicate=False, readonly=True,
                                     index=True, default=lambda self: _("New Appointment"))
    patient_id = fields.Many2one('patient.patient', string="Patient Name", tracking=True)
    name = fields.Char('Appointment Subject', required=False)
    dentist_id = fields.Many2one('clinic.employee', string="Dentist", domain=[('employee_type.name', '=', 'Dentist')])
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    allday = fields.Boolean('All Day', default=False)
    duration = fields.Float('Duration', compute='_compute_duration', store=True, readonly=False)
    appointment_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent_email', 'Email Sent'),
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
    procedure_line_id =fields.One2many('dental.procedure.line', 'appointment_id', string="Procedures")

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

    def action_send_email_appointment_details(self):
        template_id = self.env.ref('oao_dental_clinic_management.email_template_appointment_details').id
        template = self.env['mail.template'].browse(template_id)
        if not template:
            raise ValidationError(_("Email template not found!"))

        result = template.send_mail(self.id, force_send=True)
        mail = self.env['mail.mail'].search([('id', '=', result)], limit=1)
        if mail and mail.state == 'exception':
            raise ValidationError(_("Email sending failed!"))
        else:
            self.appointment_status = 'sent_email'


    def status_cancelled_appointment(self):
        self.appointment_status = 'cancelled'

    @api.constrains('start')
    def _check_start_time(self):
        if self.start:
            now = datetime.now()
            if self.start < now:
                raise ValidationError(_("The start time cannot be in the past. "))

    @api.constrains('stop')
    def _check_stop_time(self):
        if self.start and self.stop:
            if self.stop < self.start:
                raise ValidationError(_('The stop time cannot be earlier than start time '))

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
        if vals.get('patient_id') and vals.get('dentist_id'):
            patient = self.env['patient.patient'].browse(vals['patient_id'])
            patient.write({'dentist_id': vals['dentist_id']})

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

            if 'dentist_id' in vals:
                patient = record.patient_id
                patient.write({'dentist_id': vals['dentist_id']})


        return super(PatientAppointment, self).write(vals)
