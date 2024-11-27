
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import re


class Employee(models.Model):
    _name = 'clinic.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee'

    employee_type = fields.Many2one('employee.type', string='Employee Type', required=True)
    related_user = fields.Many2one('res.users', string='Related User', help="User associated with this employee")
    name = fields.Char(string='Employee Name', required=True)
    surname = fields.Char(string='Employee Surname', required=True)
    date_of_birth = fields.Date(string='Date of Birth', required=True)
    age = fields.Integer(string='Age In Years', compute="_compute_age", store=True)
    phone = fields.Char(string='Phone Number', required=True)
    second_phone = fields.Char(string='Second Phone', required=True)
    image = fields.Image(string="Image")
    email = fields.Char(string='Email Address')
    tc_number = fields.Char(string='TC No', required=True)
    city = fields.Many2one('res.country.state', string="City", domain="[('country_id', '=', 224)]")
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
            if record.phone and record.second_phone and record.phone == record.second_phone:
                raise ValidationError(_("Phone and Second Phone can not be same."))
    @api.constrains("email")
    def _check_email_constraints(self):
        email_pattern = r"^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+$"
        for record in self:
            if record.email:
                if not re.match(email_pattern, record.email):
                    raise ValidationError("Invalid email.")

    @api.constrains('tc_number')
    def _check_tc_number(self):
        for record in self:
            tc_no = record.tc_number

            if tc_no:
                if not tc_no.isdigit() or len(tc_no) != 11:
                    raise ValidationError("TC Kimlik Numarası 11 haneli bir sayı olmalıdır.")

                # İlk hane 0 olmamalı
                if tc_no[0] == '0':
                    raise ValidationError("TC Kimlik Numarası 0 ile başlayamaz.")

                # Algoritmaya göre doğrulama
                digits = list(map(int, tc_no))
                if not (
                        sum(digits[:10]) % 10 == digits[10] and
                        (sum(digits[0:9:2]) * 7 - sum(digits[1:8:2])) % 10 == digits[9]
                ):
                    raise ValidationError("Geçerli bir TC Kimlik Numarası giriniz.")


    # @api.model
    # def create(self, vals):
    #     employee = super(Employee, self).create(vals)
    #     employee_type = vals.get('employee_type')
    #     if employee_type:
    #         employee_type_name = self.env['employee.type'].browse(employee_type).name
    #
    #         if employee_type_name == 'Dentist':
    #             default_password = "clinic123"
    #             if not employee.related_user:
    #                 user_vals = {
    #                     'name': employee.name,
    #                     'login': f"{employee.name.lower().replace(' ', '_')}.{employee.surname.lower().replace(' ', '_')}@clinic.com",
    #                     'password': default_password,
    #                     'groups_id': [
    #                         (4, self.env.ref('oao_dental_clinic_management.group_dental_clinic_dentists').id),
    #                         (4, self.env.ref('base.group_user').id)
    #                     ]
    #                 }
    #                 user = self.env['res.users'].create(user_vals)
    #                 employee.related_user = user.id
    #     return employee
    @api.model
    def create(self, vals):
        # Yeni bir employee kaydı oluştur
        employee = super(Employee, self).create(vals)
        employee_type = vals.get('employee_type')

        if employee_type:
            # Employee type bilgisi üzerinden isim al
            employee_type_rec = self.env['employee.type'].browse(employee_type)
            employee_type_name = employee_type_rec.name if employee_type_rec else False

            if employee_type_name == 'Dentist':
                default_password = "clinic123"

                # Benzersiz bir login oluştur
                base_login = f"{employee.name.lower().replace(' ', '_')}.{employee.surname.lower().replace(' ', '_')}"
                login = base_login
                counter = 1
                while self.env['res.users'].search([('login', '=', f"{login}@clinic.com")]):
                    login = f"{base_login}{counter}"
                    counter += 1
                login = f"{login}@clinic.com"

                # Kullanıcı yoksa yeni bir kullanıcı oluştur
                if not employee.related_user:
                    user_vals = {
                        'name': employee.name,
                        'login': login,
                        'password': default_password,
                        'groups_id': [
                            (4, self.env.ref('oao_dental_clinic_management.group_dental_clinic_dentists').id),
                            (4, self.env.ref('base.group_user').id)
                        ]
                    }
                    # Kullanıcı oluştur ve employee ile ilişkilendir
                    user = self.env['res.users'].create(user_vals)
                    employee.related_user = user.id

        return employee