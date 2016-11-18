import datetime
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User, Course, Department, Participant, Grade, Term, RegistrationType, Notification
from utils import is_error_msg_present
import logging

class DccTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dept = Department.objects.create(name='Electrical Communication Engineering (ECE)')
        cls.dcc = User.objects.create_user(email='dcc@test.com', password='dcc12345', user_type=User.USER_TYPE_DCC)
        cls.charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        cls.ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=cls.charles)
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        aug_term = Term.objects.create(
            name='Aug-Dec',
            year='2016',
            last_reg_date=tomorrow,
            last_adviser_approval_date=tomorrow,
            last_instructor_approval_date=tomorrow,
            last_conversion_date=tomorrow,
            last_drop_date=tomorrow,
            last_grade_date=tomorrow
        )
        aug_term_expired = Term.objects.create(
            name='Aug-Dec',
            year='2016',
            last_reg_date=yesterday,
            last_cancellation_date=yesterday,
            last_adviser_approval_date=yesterday,
            last_instructor_approval_date=yesterday,
            last_conversion_date=yesterday,
            last_drop_date=yesterday,
            last_grade_date=yesterday
        )
        cls.s_grade = Grade.objects.create(name="S grade", points=7.5, should_count_towards_cgpa=True)
        cls.course = Course.objects.create(num='E0-111', title='Course Name1', department=dept, term=aug_term)
        cls.course_yesterday = Course.objects.create(num='E0-123', title='Course Name A', department=dept, term=aug_term_expired)
        cls.course2 = Course.objects.create(num='E1-222', title='Course Name2', department=dept, term=aug_term)
        cls.course3 = Course.objects.create(num='E2-333', title='Course Name3', department=dept, term=aug_term)
	cls.credit = RegistrationType.objects.create(name='Credit',should_count_towards_cgpa=True,is_active=True)
	cls.audit = RegistrationType.objects.create(name='Audit',should_count_towards_cgpa=False,is_active=True)
	cls.nonrtp = RegistrationType.objects.create(name='NonRTP',should_count_towards_cgpa=False,is_active=True)
	
    def setUp(self):
        self.client = Client()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)
		
    def test_1_dcc_new_badge_alert_for_new_request(self):
        self.client.login(email='ben@test.com', password='ben12345')
        self.client.post(reverse('coursereg:participants_create'),
                {'course_id': self.course.id, 'reg_type': 1, 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.client.login(email='dcc@test.com', password='dcc12345')
        self.assertTrue(User.objects.filter(id = self.ben.id, is_dcc_review_pending = True))

    def test_2_dcc_approve(self):
        self.client.login(email='ben@test.com', password='ben12345')
        self.client.post(reverse('coursereg:participants_create'),{'course_id': self.course.id, 'reg_type': 1, 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.client.login(email='dcc@test.com', password='dcc12345')
        self.client.post(reverse('coursereg:dcc_approve',args=[self.ben.id]),
			{'origin': 'dcc'}, follow=True)
        self.assertTrue(User.objects.filter(id = self.ben.id, is_dcc_review_pending = False))

    def test_3_dcc_notify(self):
        self.client.login(email='ben@test.com', password='ben12345')
        self.client.post(reverse('coursereg:participants_create'),{'course_id': self.course.id, 'reg_type': 1, 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.client.login(email='dcc@test.com', password='dcc12345')
        response = self.client.post(reverse('coursereg:notify'),
			{'origin': 'dcc', 'id' : self.ben.id, 'message' : 'meet me'}, follow=True)
        #print response.status_code
        self.assertTrue(Notification.objects.filter(user_id = self.ben.id, message = 'meet me'))
		
# adviser pending ; instructor pending 
