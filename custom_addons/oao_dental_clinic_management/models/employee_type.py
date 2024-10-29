from odoo import api, fields, models


class EmployeeType(models.Model):
    _name = 'employee.type'

    name = fields.Char(string="Employee Type")
