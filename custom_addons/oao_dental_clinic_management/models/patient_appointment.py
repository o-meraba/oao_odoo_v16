from datetime import timedelta

from odoo import fields, models, api, _


class PatientAppointment(models.Model):
    _name = 'patient.appointment'
    _rec_name = 'appointment_serial'
    _description = 'Patient Clinic Appointment'

    appointment_serial = fields.Char(string="Appointment Serial", required=True, duplicate=False, readonly=True,
                                     index=True, default=lambda self: _("New Appointment"))
    patient_id = fields.Many2one('patient.patient', string="Patient Name", tracking=True)
    appointment_status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Appointment Confirmed'),
        ('in_exam', 'Examination'),
        ('completed_exam', 'Examination Completed'),
        ('completed_appointment', 'Appointment Completed'),
        ('cancelled', 'Appointment Cancelled'),
    ], required=False, string="Appointment Status", tracking=True)

    name = fields.Char('Meeting Subject', required=False)
    start = fields.Datetime(
        'Start', required=True, tracking=True, default=fields.Date.today,
        help="Start date of an event, without time for full days events")

    stop = fields.Datetime(
        'Stop', required=True, tracking=True, default=lambda self: fields.Datetime.today() + timedelta(hours=0.5),
        compute='_compute_stop', readonly=False, store=True,
        help="Stop date of an event, without time for full days events")

    allday = fields.Boolean('All Day', default=False)

    duration = fields.Float('Duration', compute='_compute_duration', store=True, readonly=False)

    @api.depends('start', 'duration')
    def _compute_stop(self):
        # stop and duration fields both depends on the start field.
        # But they also depends on each other.
        # When start is updated, we want to update the stop datetime based on
        # the *current* duration. In other words, we want: change start => keep the duration fixed and
        # recompute stop accordingly.
        # However, while computing stop, duration is marked to be recomputed. Calling `event.duration` would trigger
        # its recomputation. To avoid this we manually mark the field as computed.
        duration_field = self._fields['duration']
        self.env.remove_to_compute(duration_field, self)
        for event in self:
            # Round the duration (in hours) to the minute to avoid weird situations where the event
            # stops at 4:19:59, later displayed as 4:19.
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

        if vals.get('appointment_serial', _('New Appointment')) == _('New Appointment'):
            vals['appointment_serial'] = self.env['ir.sequence'].next_by_code('patient.appointment.sequence') or _(
                'New Appointment')
        res = super(PatientAppointment, self).create(vals)
        return res