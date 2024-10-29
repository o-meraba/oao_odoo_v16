from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
import re


class Patient(models.Model):
    _name = "patient.patient"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Patients"
    _order = 'name desc'

    patient_id = fields.Char(string="Patient ID", readonly=True, copy=False, default="New Patient")
    name = fields.Char(string="Patient Name", required=True)
    surname = fields.Char(string="Patient Surname", required=True)
    date_of_birth = fields.Date(string='Date Of Birth', default=date.today(), required=True)
    age = fields.Integer(string='Age In Years', compute="_compute_age", store=True)
    image = fields.Image(string="Image")
    gender = fields.Selection([
        ('male', "Male"),
        ('female', 'Female')
    ], string='Gender', default='male')
    note = fields.Text(string="Description")
    phone = fields.Char(string="Phone", required=True)
    email = fields.Char(string="Email")
    blood_type = fields.Selection([
        ('a-', 'A without Rh-factor'),
        ('a+', 'A with Rh-factor'),
        ('b-', 'B without Rh-factor'),
        ('b+', 'B with Rh-factor'),
    ], string="Blood Typing", required=True)
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
        existing_patient = self.search([
            ('name', '=', vals.get('name')),
            ('surname', '=', vals.get('surname')),
            ('date_of_birth', '=', vals.get('date_of_birth'))
        ], limit=1)

        if existing_patient:
            raise ValidationError(_("A patient with the same name, surname and date of birth already exists."))

        if not vals.get('patient_id'):
            # SQL ile mevcut en yüksek patient_id'yi alıyoruz
            self._cr.execute(
                "SELECT COALESCE(MAX(CAST(SUBSTRING(patient_id, 4, LENGTH(patient_id)) AS INTEGER)), 0) FROM patient_patient")
            max_id = self._cr.fetchone()[0]

            # Yeni patient_id'yi oluşturuyoruz
            new_id = max_id + 1
            vals['patient_id'] = f'PAT{str(new_id).zfill(5)}'  # PAT00001 gibi

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
        # 10 haneli telefon numarası doğrulama kodu
        for record in self:
            if not re.match(r"^[1-9][0-9]{9}$", record.phone):
                raise ValidationError(
                    _("Invalid phone number. Please enter a 10-digit phone number without spaces or special characters."))