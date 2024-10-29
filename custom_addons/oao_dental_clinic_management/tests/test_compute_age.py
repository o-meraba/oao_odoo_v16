from odoo.tests.common import TransactionCase # add TransactionCase class from Odoo Test Module
from datetime import datetime # add datetime class
from odoo.exceptions import ValidationError

class TestComputeAgeMethod(TransactionCase):

    def setUp(self):
        super(TestComputeAgeMethod, self).setUp()
        self.test_record = self.env['patient.patient'].create({
            'date_of_birth': datetime(2000, 1, 1).date(),
            'name' : 'ömer',
            'surname': 'aba',
            'phone': "5454",
            'blood_type': 'b+'
        })

    def test_compute_age_with_valid_date(self):
        self.test_record.compute_age()

        today = datetime.now().date()
        expected_age = (today - datetime(2000, 1, 1).date()).days // 365.25
        self.assertEqual(self.test_record.age,f"{int(expected_age)} Years Old",
                        "The computed age is incorrect with a valid date_of_birth")
    
    def test_compute_age_with_no_date(self):
        """Test that compute_age returns 'No Date of Birth' if date_of_birth is empty."""
        self.test_record.date_of_birth = None
        self.test_record.compute_age()
        
        self.assertEqual(self.test_record.age, "No Date of Birth", 
                         "The computed age should be 'No Date of Birth' if date_of_birth is empty")
    
    def test_compute_age_with_future_date(self):
        """Test that compute_age handles future dates correctly"""
        with self.assertRaises(ValidationError, msg="A future date should raise a ValidationError"):
            self.test_record.date_of_birth = datetime(datetime.now().year + 1, 1,1).date()
            self.test_record.compute_age()