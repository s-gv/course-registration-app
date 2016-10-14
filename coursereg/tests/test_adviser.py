import datetime
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User, Course, Department, Participant, Grade, Term, RegistrationType, Config
from utils import is_error_msg_present
import logging

class AdviserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dept = Department.objects.create(name='Electrical Communication Engineering (ECE)')
        cls.charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        cls.ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=cls.charles)
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        aug_term = Term.objects.create(
            name='Aug-Dec',
            year='2016',
            last_reg_date=tomorrow,
            last_adviser_approval_date=tomorrow,
            last_instructor_approval_date=tomorrow,
            last_conversion_date=tomorrow,
            last_drop_date=tomorrow,
            #last_drop_with_mention_date=tomorrow,
            last_grade_date=tomorrow
        )
        cls.s_grade = Grade.objects.create(name="S grade", points=7.5, should_count_towards_cgpa=True)
        cls.course = Course.objects.create(num='E0-111', title='Course Name1', department=dept, term=aug_term)
        cls.course2 = Course.objects.create(num='E1-222', title='Course Name2', department=dept, term=aug_term)
        cls.course3 = Course.objects.create(num='E2-333', title='Course Name3', department=dept, term=aug_term)
	cls.credit = RegistrationType.objects.create(name='Credit',should_count_towards_cgpa=True,is_active=True)
	cls.audit = RegistrationType.objects.create(name='Audit',should_count_towards_cgpa=False,is_active=True)
	cls.set = Config.objects.create(key='can_adviser_add_courses_for_students',value='1')	

    def setUp(self):
        self.client = Client()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_adviser_approve_credit(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'reg_type_change', 'origin': 'adviser','reg_type': '1'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course,registration_type = '1'))

    def test_adviser_approve_audit(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'reg_type_change', 'origin': 'adviser','reg_type': '2'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course,registration_type = '2'))

    def test_adviser_delete(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_delete',args=[participant.id]),
			{'origin': 'adviser'}, follow=True)
		self.assertFalse(Participant.objects.filter(user=self.ben, course=self.course))

    
