
from odoo import http, _
from odoo.http import request


class PatientAppointmentController(http.Controller):

    @http.route('/patient_appointment', type='http', auth='public', website=True)
    def patient_appointment_page(self, **kw):
        dentists = request.env['clinic.employee'].search([('employee_type.name', '=', 'Dentist')])
        return http.request.render('oao_dental_clinic_management.patient_appointment_template', { 'dentists': dentists})

    @http.route('/create/webappointment', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def control_patient_and_create_appointment(self, **post):
        name = post.get('name')
        surname = post.get('surname')
        birthdate = post.get('birthdate')
        phone = post.get('phone')
        dentist_id = post.get('dentist_id')

        obj_patient = request.env['patient.patient'].sudo().search([
                ('name', '=', name),
                ('surname', '=', surname),
                ('date_of_birth', '=', birthdate),
            ], limit=1)

        if not obj_patient:
            obj_patient = request.env['patient.patient'].sudo().create({
                'name': name,
                'surname': surname,
                'date_of_birth': birthdate,
                'phone': phone,
            })

        request.env['appointment.requests'].sudo().create({
            'patient_id': obj_patient.id,
            'dentist_id': dentist_id,
        })

        return request.render('oao_dental_clinic_management.patient_thanks')



