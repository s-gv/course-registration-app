from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User, Faq
from utils import is_error_msg_present
import logging

class ProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dcc = User.objects.create_user(email='dcc@test.com', password='dcc12345', user_type=User.USER_TYPE_DCC)
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=charles)

    def setUp(self):
        self.client = Client()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_was_student_shown_right_profile_page(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.post(reverse('coursereg:profile'), follow=True)
        self.assertTemplateUsed(response, 'coursereg/profile.html')
        self.assertEquals(response.context['user_type'], 'student')

    def test_was_faculty_shown_right_profile_page(self):
        self.client.login(email='charles@test.com', password='charles12345')
        response = self.client.post(reverse('coursereg:profile'), follow=True)
        self.assertTemplateUsed(response, 'coursereg/profile.html')
        self.assertEquals(response.context['user_type'], 'faculty')

    def test_was_dcc_shown_right_profile_page(self):
        self.client.login(email='dcc@test.com', password='dcc12345')
        response = self.client.post(reverse('coursereg:profile'), follow=True)
        self.assertTemplateUsed(response, 'coursereg/profile.html')
        self.assertEquals(response.context['user_type'], 'dcc')

class FAQTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dcc = User.objects.create_user(email='dcc@test.com', password='dcc12345', user_type=User.USER_TYPE_DCC)
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=charles)
        cls.faq_student = Faq.objects.create(faq_for=Faq.FAQ_STUDENT, question='student q?', answer='student a')
        cls.faq_faculty = Faq.objects.create(faq_for=Faq.FAQ_FACULTY, question='faculty q?', answer='faculty a')
        cls.faq_dcc = Faq.objects.create(faq_for=Faq.FAQ_DCC, question='dcc q?', answer='dcc a')

    def setUp(self):
        self.client = Client()

    def test_was_student_shown_right_faqs(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.get(reverse('coursereg:faq'))
        self.assertTemplateUsed(response, 'coursereg/faq.html')
        self.assertTrue(self.faq_student in response.context['faqs'])

    def test_was_faculty_shown_right_faqs(self):
        self.client.login(email='charles@test.com', password='charles12345')
        response = self.client.get(reverse('coursereg:faq'))
        self.assertTemplateUsed(response, 'coursereg/faq.html')
        self.assertTrue(self.faq_faculty in response.context['faqs'])

    def test_was_dcc_shown_right_faqs(self):
        self.client.login(email='dcc@test.com', password='dcc12345')
        response = self.client.get(reverse('coursereg:faq'))
        self.assertTemplateUsed(response, 'coursereg/faq.html')
        self.assertTrue(self.faq_dcc in response.context['faqs'])
