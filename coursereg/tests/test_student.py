import datetime
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User, Course, Department
from utils import is_error_msg_present

class StudentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dept = Department.objects.create(name='Electrical Communication Engineering (ECE)')
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        cls.ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=charles)
        today = datetime.datetime.now()
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        cls.course_today = Course.objects.create(num='E0-232', title='Course Name', department=dept, last_reg_date=today)
        cls.course_yesterday = Course.objects.create(num='E0-211', title='Noname', department=dept, last_reg_date=yesterday)

    def setUp(self):
        self.client = Client()

    def test_was_course_with_last_reg_date_in_future_shown(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.get(reverse('coursereg:index'), follow=True)
        self.assertTrue(self.course_today in response.context['courses'])

    def test_was_course_with_last_reg_date_in_past_not_shown(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.get(reverse('coursereg:index'), follow=True)
        self.assertFalse(self.course_yesterday in response.context['courses'])

    def test_was_course_added(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.post(reverse('coursereg:participants_create'),
            {'course_id': self.course_today.id, 'reg_type': 'credit', 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.assertTrue(any([p[4] == self.course_today for p in response.context['participants']]))

    def test_was_course_removed(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.post(reverse('coursereg:participants_create'),
            {'course_id': self.course_today.id, 'reg_type': 'credit', 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        participant_id = response.context['participants'][0][0]
        response = self.client.post(reverse('coursereg:participants_delete', args=[participant_id]), follow=True)
        self.assertFalse(any([p[4] == self.course_today for p in response.context['participants']]))
