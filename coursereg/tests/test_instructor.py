import datetime
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User, Course, Department, Participant, Grade, Term, RegistrationType 
from utils import is_error_msg_present
import logging

class InstructorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dept = Department.objects.create(name='Electrical Communication Engineering (ECE)')
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        rajesh = User.objects.create_user(email='rajesh@test.com', password='rajesh12345', user_type=User.USER_TYPE_FACULTY)
        cls.ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=rajesh)
        cls.alyssa = User.objects.create_user(email='alyssa@test.com', password='alyssa12345', user_type=User.USER_TYPE_STUDENT, adviser=rajesh)
        cls.rama = User.objects.create_user(email='rama@test.com', password='rama12345', user_type=User.USER_TYPE_STUDENT, adviser=rajesh)
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
        cls.course_yesterday = Course.objects.create(num='E0-111', title='Course Name1', department=dept, term=aug_term_expired)
	cls.credit = RegistrationType.objects.create(name='Credit',should_count_towards_cgpa=True,is_active=True)
	cls.audit = RegistrationType.objects.create(name='Audit',should_count_towards_cgpa=False,is_active=True)
	cls.nonrtp = RegistrationType.objects.create(name='NonRTP',should_count_towards_cgpa=False,is_active=True)
	
	# To add as instructor for courses
	cls.participant = Participant.objects.create(user=charles, course=cls.course,
	participant_type=Participant.PARTICIPANT_INSTRUCTOR, grade=cls.s_grade)
	cls.participant = Participant.objects.create(user=charles, course=cls.course_yesterday,
	participant_type=Participant.PARTICIPANT_INSTRUCTOR, grade=cls.s_grade)
        
    def setUp(self):
        self.client = Client()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_1_instructor_review(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'review', 'origin': 'instructor'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course,is_instructor_reviewed = True))
		
    def test_2_instructor_cancel(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_delete',args=[participant.id]),
			{'origin': 'instructor'}, follow=True)
		self.assertFalse(Participant.objects.filter(user=self.ben, course=self.course))
		
    def test_3_instructor_new_badge_alert_for_new_request(self):
        self.client.login(email='ben@test.com', password='ben12345')
        self.client.post(reverse('coursereg:participants_create'),
                {'course_id': self.course.id, 'reg_type': 1, 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.client.login(email='charles@test.com', password='charles12345')
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, is_instructor_reviewed=False))

    def test_4_instructor_mark_all(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade,is_instructor_reviewed=False)
		participant = Participant.objects.create(user=self.alyssa, course=self.course,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade,is_instructor_reviewed=False)
		participant = Participant.objects.create(user=self.rama, course=self.course,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.nonrtp, grade=self.s_grade,is_instructor_reviewed=False)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update_all'),
			{'course_id': self.course.id,'action': 'review', 'origin': 'instructor'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, is_instructor_reviewed = True))
		self.assertTrue(Participant.objects.filter(user=self.alyssa, course=self.course, is_instructor_reviewed = True))
		self.assertTrue(Participant.objects.filter(user=self.rama, course=self.course, is_instructor_reviewed = True))

    def test_5_instructor_delete_after_instructor_ApprovalDate(self):
		participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_delete',args=[participant.id]),
                {'origin': 'instructor'}, follow=True)
		self.assertEqual(response.status_code, 403)        
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday))


#  NotGraded
