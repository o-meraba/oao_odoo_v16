from odoo import models, fields


class ClinicCenter(models.Model):
    _name = 'clinic.center'
    _description = 'Clinic Center'

    name = fields.Char(string="Center Name", required=True)
    code = fields.Char(string="Center Code", required=True)
    administrator_id = fields.Many2one('res.users', string="Center Administrator")
    address = fields.Text(string="Center Address")