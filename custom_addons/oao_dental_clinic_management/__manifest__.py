{
    'name': 'Dental Clinic Management',
    'version': '16.0.0.0.1',
    'category': 'Healthcare',
    'summary': 'Dental clinic management system for dentists',
    'description': """
        OAO Dental Clinic Management
        ============================
        This module helps dentists manage their clinic activities, including patient records, appointments, treatments, and billing.
    """,
    'author': 'ABA TECH GROUP',
    'website': 'https://omeraba.com/tr/blog/odoo-projeleri-23/dis-klinigi-yonetim-sistemi-48',
    'depends': ['base', 'mail' ],
    'data': [
        'security/ir.model.access.csv',
        'data/employee.type.csv',
        'data/ir_cron_data.xml',
        'data/data.xml',
        'views/patient_views.xml',
        'views/employee_type_views.xml',
        'views/employee_views.xml',
        'views/patient_appointment_views.xml',
        'views/menu_views.xml',
    ],
    'sequence': '-1',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
