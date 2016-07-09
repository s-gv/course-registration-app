from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User
import utils

class UserLoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        ben = utils.create_user('ben@test.com', 'ben12345', User.USER_TYPE_STUDENT, None)
        charles = utils.create_user('charles@test.com', 'charles12345', User.USER_TYPE_FACULTY, None)
        alyssa = utils.create_user('alyssa@test.com', 'alyssa12345', User.USER_TYPE_STUDENT, charles)
        dcc = utils.create_user('dcc@test.com', 'dcc12345', User.USER_TYPE_DCC, None)

    def test_was_login_with_wrong_password_rejected(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'ben@test.com', 'password': 'blahblah'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/signin.html')
        self.assertRedirects(response, reverse('coursereg:signin'))
        self.assertEquals(utils.is_error_msg_present(response), True)

    def test_was_student_without_adviser_shown_fatal_error(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'ben@test.com', 'password': 'ben12345'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/fatal.html')

    def test_was_student_shown_right_index_page(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'alyssa@test.com', 'password': 'alyssa12345'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/student.html')

    def test_was_faculty_shown_right_index_page(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'charles@test.com', 'password': 'charles12345'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/adviser.html')

    def test_was_dcc_shown_right_index_page(self):
        response = self.client.post(reverse('coursereg:signin'), {'email': 'dcc@test.com', 'password': 'dcc12345'}, follow=True)
        self.assertTemplateUsed(response, 'coursereg/dcc.html')
