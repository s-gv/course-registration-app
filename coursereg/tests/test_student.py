import datetime
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User, Course, Department, Participant, Grade, Term,RegistrationType
from utils import is_error_msg_present
import logging

class StudentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dept = Department.objects.create(name='Electrical Communication Engineering (ECE)')
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        cls.ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=charles)
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
            #last_drop_with_mention_date=tomorrow,
            last_grade_date=tomorrow
        )
        aug_term_expired = Term.objects.create(
            name='Aug-Dec',
            year='2016',
            last_reg_date=yesterday,
            last_adviser_approval_date=yesterday,
            last_instructor_approval_date=yesterday,
            last_conversion_date=yesterday,
            last_drop_date=yesterday,
            #last_drop_with_mention_date=yesterday,
            last_grade_date=yesterday
        )
        cls.s_grade = Grade.objects.create(name="S grade", points=7.5, should_count_towards_cgpa=True)
        cls.course_tomorrow = Course.objects.create(num='E0-232', title='Course Name', department=dept, term=aug_term)
        cls.course_yesterday = Course.objects.create(num='E0-211', title='Noname', department=dept, term=aug_term_expired)
	cls.credit = RegistrationType.objects.create(name='Credit',should_count_towards_cgpa=True,is_active=True)
	cls.audit = RegistrationType.objects.create(name='Audit',should_count_towards_cgpa=False,is_active=True)

    def setUp(self):
        self.client = Client()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_was_course_with_last_reg_date_in_future_shown(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.get(reverse('coursereg:index'), follow=True)
        self.assertTrue(self.course_tomorrow in response.context['courses'])

    def test_was_course_with_last_reg_date_in_past_not_shown(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.get(reverse('coursereg:index'), follow=True)
        self.assertFalse(self.course_yesterday in response.context['courses'])

    def test_was_student_able_register_for_course_before_last_reg_date(self):
        self.client.login(email='ben@test.com', password='ben12345')
        self.client.post(reverse('coursereg:participants_create'),
                {'course_id': self.course_tomorrow.id, 'reg_type': 1, 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_tomorrow))

    def test_was_student_able_register_for_course_after_last_reg_date(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.post(reverse('coursereg:participants_create'),
             {'course_id': self.course_yesterday.id, 'reg_type': 1, 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Participant.objects.filter(user=self.ben, course=self.course_yesterday))
    
    def test_was_course_added(self):
		self.client.login(email='ben@test.com', password='ben12345')
		response = self.client.post(reverse('coursereg:participants_create'),
			{'course_id': self.course_tomorrow.id, 'reg_type': 1, 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
		#self.assertTrue(any([p[5] == self.course_tomorrow for p in response.context['participants']]))
		# Check with sagar
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_tomorrow))

    def test_was_course_removed(self):
        participant = Participant.objects.create(user=self.ben, course=self.course_tomorrow,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade,
            is_adviser_approved=False, is_instructor_approved=False)
        self.client.login(email='ben@test.com', password='ben12345')
        self.client.post(reverse('coursereg:participants_delete', args=[participant.id]), follow=True)
        self.assertFalse(Participant.objects.filter(user=self.ben, course=self.course_tomorrow))
        
    def test_was_student_not_able_to_delete_course_after_adviser_approval(self):
        participant = Participant.objects.create(user=self.ben, course=self.course_tomorrow,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade,
            is_adviser_approved=True, is_instructor_approved=True)
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.post(reverse('coursereg:participants_delete', args=[participant.id]), follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_tomorrow))

    def test_was_student_not_able_to_delete_approved_course_after_last_reg_date(self):
        participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade,
            is_adviser_approved=True, is_instructor_approved=True)
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.post(reverse('coursereg:participants_delete', args=[participant.id]), follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday))

    def test_could_student_delete_graded_course(self):
        participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade,
            is_adviser_approved=True, is_instructor_approved=True)
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.post(reverse('coursereg:participants_delete', args=[participant.id]), follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday))
