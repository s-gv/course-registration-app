from __future__ import unicode_literals
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.db.models import Q
import re

class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)

class Department(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=100, default='-')

    def __unicode__(self):
        return self.abbreviation

class Degree(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class Grade(models.Model):
    name = models.CharField(max_length=100)
    points = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    should_count_towards_cgpa = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

def get_default_grade():
    default_grade = Grade.objects.filter(name="Not graded", should_count_towards_cgpa=False).first()
    if not default_grade:
        default_grade = Grade.objects.create(name="Not graded", should_count_towards_cgpa=False, points=0)
    return default_grade.id

class Participant(models.Model):
    PARTICIPANT_STUDENT = 0
    PARTICIPANT_INSTRUCTOR = 1
    PARTICIPANT_TA = 2

    PARTICIPANT_CHOICES = (
        (PARTICIPANT_STUDENT, 'Student'),
        (PARTICIPANT_INSTRUCTOR, 'Instructor'),
        (PARTICIPANT_TA, 'TA'),
    )

    user = models.ForeignKey('User', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    participant_type = models.IntegerField(default=PARTICIPANT_INSTRUCTOR, choices=PARTICIPANT_CHOICES)
    is_credit = models.BooleanField(default=True)
    is_drop = models.BooleanField(default=False)
    is_drop_mentioned = models.BooleanField(default=False)
    grade = models.ForeignKey('Grade', on_delete=models.CASCADE, blank=True, default=get_default_grade)
    is_adviser_approved = models.BooleanField(default=False)
    is_instructor_approved = models.BooleanField(default=False)
    should_count_towards_cgpa = models.BooleanField(default=True)

    def __unicode__(self):
        return self.user.email + " in %s - %s" % (self.course.num, self.course.title)

class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_STUDENT = 0
    USER_TYPE_FACULTY = 1
    USER_TYPE_DCC = 2
    USER_TYPE_OTHER = 3

    USER_TYPE_CHOICES = (
        (USER_TYPE_STUDENT, "Student"),
        (USER_TYPE_FACULTY, "Faculty"),
        (USER_TYPE_DCC, "DCC"),
        (USER_TYPE_OTHER, "Other"),
    )

    email = models.EmailField(max_length=254, unique=True)
    full_name = models.CharField(max_length=250)
    user_type = models.IntegerField(default=USER_TYPE_OTHER, choices=USER_TYPE_CHOICES)
    adviser = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, limit_choices_to={'user_type': USER_TYPE_FACULTY})
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    sr_no = models.CharField(max_length=200, default='-')
    telephone = models.CharField(max_length=100, default='', blank=True)
    is_dcc_review_pending = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def is_adviser_review_pending(self):
        if self.user_type == User.USER_TYPE_STUDENT:
            return Participant.objects.filter(user=self, is_adviser_approved=False).first()

    def is_instructor_review_pending(self):
        if self.user_type == User.USER_TYPE_STUDENT:
            return Participant.objects.filter(user=self, is_instructor_approved=False).first()

    def is_adviser_or_instructor_pending(self):
        if self.user_type == User.USER_TYPE_STUDENT:
            return Participant.objects.filter(
                Q(is_adviser_approved=False) | Q(is_instructor_approved=False),
                user=self).first()

    def is_grade_pending(self):
        if self.user_type == User.USER_TYPE_STUDENT:
            return Participant.objects.filter(
                is_adviser_approved=True,
                is_instructor_approved=True,
                grade=Participant.GRADE_NA,
                user=self).first()

    def cgpa(self):
        if self.user_type == User.USER_TYPE_STUDENT:
            total_credits = 0
            total_grade_points = 0
            for p in Participant.objects.filter(user=self, is_credit=True).exclude(is_drop=False).exclude(should_count_towards_cgpa=False):
                if p.course.should_count_towards_cgpa and p.grade and p.grade.should_count_towards_cgpa:
                    total_credits += p.course.credits
                    total_grade_points += p.grade.points * p.course.credits
            if total_credits > 0:
                return "%.1f" % (total_grade_points * 1.0 / total_credits)
        return '-'


    def get_full_name(self):
        return self.full_name.strip()

    def get_short_name(self):
        return self.full_name.strip()

class Notification(models.Model):
    ORIGIN_ADVISER = 0
    ORIGIN_INSTRUCTOR = 1
    ORIGIN_DCC = 2
    ORIGIN_OTHER = 3

    ORIGIN_CHOICES = (
        (ORIGIN_ADVISER, 'Adviser'),
        (ORIGIN_INSTRUCTOR, 'Instructor'),
        (ORIGIN_DCC, 'DCC'),
        (ORIGIN_OTHER, 'Other')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    origin = models.IntegerField(default=ORIGIN_DCC, choices=ORIGIN_CHOICES)
    message = models.TextField()
    is_student_acknowledged = models.BooleanField(default=False)
    is_adviser_acknowledged = models.BooleanField(default=False)
    is_dcc_acknowledged = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)


def get_recent_last_reg_date():
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.last_reg_date
    return timezone.now()

def get_recent_last_conversion_date():
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.last_conversion_date
    return timezone.now()

def get_recent_last_drop_date():
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.last_drop_date
    return timezone.now()

def get_recent_last_drop_with_mention_date():
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.last_drop_with_mention_date
    return timezone.now()

def get_recent_last_grade_date():
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.last_grade_date
    return timezone.now()

def get_recent_term():
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.term
    return Course.TERM_AUG

def get_recent_year():
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.year
    return str(timezone.now().year)


class Course(models.Model):
    TERM_AUG = 0
    TERM_JAN = 1
    TERM_SUMMER = 2
    TERM_OTHER = 3

    TERM_CHOICES = (
        (TERM_AUG, "Aug-Dec"),
        (TERM_JAN, "Jan-Apr"),
        (TERM_SUMMER, "Summer"),
        (TERM_OTHER, "Other"),
    )

    num = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    term = models.IntegerField(default=get_recent_term, choices=TERM_CHOICES)
    year = models.CharField(max_length=4, default=get_recent_year)
    num_credits = models.IntegerField(default=3, verbose_name="Number of credits")
    credit_label = models.CharField(max_length=100, default='', verbose_name="Credit split (ex: 3:0)", blank=True)
    should_count_towards_cgpa = models.BooleanField(default=True)
    auto_instructor_approve = models.BooleanField(default=False)
    last_reg_date = models.DateTimeField(verbose_name="Last registration date", default=get_recent_last_reg_date)
    last_conversion_date = models.DateTimeField(verbose_name="Last credit/audit conversion date", default=get_recent_last_conversion_date)
    last_drop_date = models.DateTimeField(verbose_name="Last drop date", default=get_recent_last_drop_date)
    last_drop_with_mention_date = models.DateTimeField(verbose_name="Last drop with mention date", default=get_recent_last_drop_with_mention_date)
    last_grade_date = models.DateTimeField(verbose_name="Last grade date", default=get_recent_last_grade_date)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_last_reg_date_passed(self):
        return timezone.now() > self.last_reg_date

    def is_last_conversion_date_passed(self):
        return timezone.now() > self.last_conversion_date

    def is_drop_date_passed(self):
        return timezone.now() > self.last_drop_date

    def is_last_grade_date_passed(self):
        return timezone.now() > self.last_grade_date

    def is_instructor_review_pending(self):
        return Participant.objects.filter(course=self, is_adviser_approved=True, is_instructor_approved=False).first()

    def __unicode__(self):
        return self.num + ' ' + self.title + ' (%s %s)' % (Course.TERM_CHOICES[self.term][1], self.year)

class Faq(models.Model):
    FAQ_STUDENT = 0
    FAQ_FACULTY = 1
    FAQ_DCC = 2

    FAQ_CHOICES = (
        (FAQ_STUDENT, "Student"),
        (FAQ_FACULTY, "Faculty"),
        (FAQ_DCC, "DCC")
    )

    faq_for = models.IntegerField(default=FAQ_STUDENT, choices=FAQ_CHOICES)
    question = models.TextField()
    answer = models.TextField()

    def __unicode__(self):
        return self.question

class Config(models.Model):
    key = models.CharField(max_length=1000)
    value = models.CharField(max_length=1000)
