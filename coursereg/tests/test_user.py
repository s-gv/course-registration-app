from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User
from utils import is_error_msg_present

class UserLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dcc = User.objects.create_user(email='dcc@test.com', password='dcc12345', user_type=User.USER_TYPE_DCC)
        admin = User.objects.create_superuser(email='admin@test.com', password='admin12345', user_type=User.USER_TYPE_OTHER)
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        alyssa = User.objects.create_user(email='alyssa@test.com', password='alyssa12345', user_type=User.USER_TYPE_STUDENT, adviser=charles)
        ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT)

    def setUp(self):
        self.client = Client()

    def test_was_login_with_wrong_password_rejected(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'ben@test.com', 'password': 'blahblah'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/signin.html')
        self.assertRedirects(response, reverse('coursereg:signin'))
        self.assertTrue(is_error_msg_present(response))

    def test_was_student_without_adviser_shown_fatal_error(self):
        with self.assertRaises(Exception) as context:
            response = self.client.post(reverse('coursereg:signin'), {'email': 'ben@test.com', 'password': 'ben12345'}, follow=True)

    def test_was_student_shown_right_index_page(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'alyssa@test.com', 'password': 'alyssa12345'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/student.html')

    def test_was_faculty_shown_right_index_page(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'charles@test.com', 'password': 'charles12345'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/adviser.html')

    def test_was_dcc_shown_right_index_page(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'dcc@test.com', 'password': 'dcc12345'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/dcc.html')

    def test_was_superuser_shown_right_index_page(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'admin@test.com', 'password': 'admin12345'}, follow=True)
        self.assertTemplateUsed(response, 'admin/index.html')


class ChangePasswordTests(TestCase):
    def setUp(self):
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        self.client = Client()

    def test_was_faculty_password_changed(self):
        self.client.login(email='charles@test.com', password='charles12345')
        response = self.client.post(reverse('coursereg:change_passwd'),
            {'passwd': 'charles12345', 'newpasswd': 'test12345', 'newpasswd2': 'test12345'}, follow=True)
        self.assertFalse(self.client.login(email='charles@test.com', password='charles12345'))
        self.assertTrue(self.client.login(email='charles@test.com', password='test12345'))
