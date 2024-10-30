
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import re


class Employee(models.Model):
    _name = 'clinic.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee'

    employee_type = fields.Many2one('employee.type', string='Employee Type', required=True)
    name = fields.Char(string='Employee Name', required=True)
    surname = fields.Char(string='Employee Surname', required=True)
    date_of_birth = fields.Date(string='Date of Birth', required=True)
    age = fields.Integer(string='Age In Years', compute="_compute_age", store=True)
    phone = fields.Char(string='Phone Number', required=True)
    second_phone = fields.Char(string='Second Phone', required=True)
    image = fields.Image(string="Image")
    email = fields.Char(string='Email Address')
    tc_number = fields.Char(string='TC No', required=True)
    home_address = fields.Text(string='Home Address', required=True)
    bank_account_number = fields.Char(string='Bank Account Number', required=True)
    active = fields.Boolean(string="Active", default=True)
    gender = fields.Selection([
        ('male', "Male"),
        ('female', 'Female')
    ], string='Gender', default='male', required=True)
    note = fields.Text(string="Description")

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

    @api.constrains('date_of_birth')
    def validation_date_of_birth(self):
        today = datetime.now().date()
        for rec in self:
            if rec.date_of_birth:
                if rec.date_of_birth > today:
                    raise ValidationError(_("Invalid Date of Birth"))

    @api.constrains('phone', 'second_phone')
    def _validation_phone(self):
        for record in self:
            if record.phone and not re.match(r"^[1-9][0-9]{9}$", record.phone):
                raise ValidationError(
                    _("Invalid phone number. Please enter a 10-digit phone number without spaces or special "
                      "characters for the primary phone."))
            if record.second_phone and not re.match(r"^[1-9][0-9]{9}$", record.second_phone):
                raise ValidationError(
                    _("Invalid phone number. Please enter a 10-digit phone number without spaces or special "
                      "characters for the secondary phone."))
    @api.constrains("email")
    def _check_email_constraints(self):
        email_pattern = r"^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+$"
        for record in self:
            if not re.match(email_pattern, record.email):
                raise ValidationError("Invalid email.")