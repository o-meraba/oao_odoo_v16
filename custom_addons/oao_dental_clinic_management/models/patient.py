from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
import re


class Patient(models.Model):
    _name = "patient.patient"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Patients"
    _order = 'name desc'

    patient_serial = fields.Char(string="Patient Serial", required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _("New Patient"))
    name = fields.Char(string="Patient Name", required=True)
    surname = fields.Char(string="Patient Surname", required=True)
    date_of_birth = fields.Date(string='Date Of Birth', default=date.today(), required=True)
    age = fields.Integer(string='Age In Years', compute="_compute_age", store=True)
    image = fields.Image(string="Image")
    gender = fields.Selection([
        ('male', "Male"),
        ('female', 'Female')
    ], string='Gender', default='male', required=True)
    note = fields.Text(string="Description")
    phone = fields.Char(string="Phone", required=True)
    email = fields.Char(string="Email")
    blood_type = fields.Selection([
        ('a-', 'A without Rh-factor'),
        ('a+', 'A with Rh-factor'),
        ('b-', 'B without Rh-factor'),
        ('b+', 'B with Rh-factor'),
    ], string="Blood Types", required=True)
    active = fields.Boolean(string="Active", default=True)

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} {rec.surname or ''}".strip()
            result.append((rec.id, name))
        return result

    @api.depends('date_of_birth')
    def _compute_age(self):
        if self.date_of_birth:
            today = datetime.now().date()
            age = today - self.date_of_birth
            age_in_years = age.days // 365.25
            self.age = int(age_in_years)
        else:
            self.age = 0

    @api.model
    def _cron_update_ages(self):
        records = self.search([])
        for record in records:
            record._compute_age()

    @api.model
    def create(self, vals):
        name = vals.get('name')
        surname = vals.get('surname')
        date_of_birth = vals.get('date_of_birth')
        if name and surname and date_of_birth:
            existing_patient = self.search([
                ('name', '=', name),
                ('surname', '=', surname),
                ('date_of_birth', '=', date_of_birth)
            ], limit=1)
            if existing_patient:
                raise ValidationError(_("A patient with the same name,surname, date of birth already exists."))

        if vals.get('patient_serial', _('New Patient')) == _('New Patient'):
            vals['patient_serial'] = self.env['ir.sequence'].next_by_code('patient.sequence') or _('New Patient')

        return super(Patient, self).create(vals)

    @api.constrains('date_of_birth')
    def validation_date_of_birth(self):
        today = datetime.now().date()
        for rec in self:
            if rec.date_of_birth:
                if rec.date_of_birth > today:
                    raise ValidationError(_("Invalid Date of Birth"))

    @api.constrains('phone')
    def _validation_phone(self):
        for record in self:
            if not re.match(r"^[1-9][0-9]{9}$", record.phone):
                raise ValidationError(
                    _("Invalid phone number. Please enter a 10-digit phone number without spaces or special characters."))

    @api.constrains("email")
    def _check_email_constraints(self):
        email_pattern = r"^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+$"
        for record in self:
            if not re.match(email_pattern, record.email):
                raise ValidationError("Invalid email.")
