from __future__ import unicode_literals
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.db.models import Q
import re
from django.core.exceptions import ValidationError
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_password(User.objects.make_random_password())
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)

class Department(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.abbreviation

class Degree(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

class Grade(models.Model):
    name = models.CharField(max_length=100)
    points = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    should_count_towards_cgpa = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

def get_recent_last_reg_date():
    ''' Legacy function needed for the first DB migration '''
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.last_reg_date
    return timezone.now()

def get_recent_last_drop_date():
    ''' Legacy function needed for the first DB migration '''
    recent_course = Course.objects.order_by('-updated_at').first()
    if recent_course:
        return recent_course.last_drop_date
    return timezone.now()

class RegistrationType(models.Model):
    name = models.CharField(max_length=100)
    should_count_towards_cgpa = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

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
    registration_type = models.ForeignKey('RegistrationType', null=True, on_delete=models.CASCADE)
    is_drop = models.BooleanField(default=False)
    grade = models.ForeignKey('Grade', on_delete=models.CASCADE, blank=True, null=True)
    should_count_towards_cgpa = models.BooleanField(default=True)
    lock_from_student = models.BooleanField(default=False)
    is_adviser_reviewed = models.BooleanField(default=False)
    is_instructor_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.user.email + " in %s - %s" % (self.course.num, self.course.title)

    def get_status_desc(self):
        if self.is_drop:
            return 'Dropped this course'
        if self.grade == None:
            if self.user.is_dcc_review_pending:
                return 'In progress'
            else:
                return 'Registered'
        else:
            return self.grade

    def get_reg_type_desc(self):
        if self.is_drop:
            return 'Drop'
        else:
            return self.registration_type


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
    is_dcc_sent_notification = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def is_adviser_review_pending(self):
        if self.user_type == User.USER_TYPE_STUDENT:
            return Participant.objects.filter(user=self, is_adviser_reviewed=False).first()

    def cgpa(self):
        if self.user_type == User.USER_TYPE_STUDENT:
            total_credits = 0
            total_grade_points = 0
            for p in Participant.objects.filter(user=self).exclude(is_drop=False).exclude(should_count_towards_cgpa=False):
                if p.registration_type.should_count_towards_cgpa and p.course.should_count_towards_cgpa and p.grade and p.grade.should_count_towards_cgpa:
                    total_credits += p.course.credits
                    total_grade_points += p.grade.points * p.course.credits
            if total_credits > 0:
                return "%.1f" % (total_grade_points * 1.0 / total_credits)
        return '-'


    def get_full_name(self):
        return self.full_name.strip()

    def get_short_name(self):
        return self.full_name.strip()

    def __unicode__(self):
        return '%s (%s)' % (self.full_name, self.email)

class Notification(models.Model):
    ORIGIN_ADVISER = 0
    ORIGIN_INSTRUCTOR = 1
    ORIGIN_DCC = 2
    ORIGIN_OTHER = 3
    ORIGIN_STUDENT = 4

    ORIGIN_CHOICES = (
        (ORIGIN_ADVISER, 'Adviser'),
        (ORIGIN_INSTRUCTOR, 'Instructor'),
        (ORIGIN_DCC, 'DCC'),
        (ORIGIN_OTHER, 'Other'),
        (ORIGIN_STUDENT, 'Student')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    origin = models.IntegerField(default=ORIGIN_DCC, choices=ORIGIN_CHOICES)
    message = models.TextField()
    is_student_acknowledged = models.BooleanField(default=False)
    is_adviser_acknowledged = models.BooleanField(default=False)
    is_dcc_acknowledged = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return 'For %s - %s' % (self.user, self.message)

class Term(models.Model):
    name = models.CharField(max_length=100)
    year = models.CharField(max_length=4)
    start_reg_date = models.DateTimeField(default=timezone.now)
    last_reg_date = models.DateTimeField(default=timezone.now)
    last_adviser_approval_date = models.DateTimeField(default=timezone.now)
    last_instructor_approval_date = models.DateTimeField(default=timezone.now)
    last_cancellation_date = models.DateTimeField(default=timezone.now)
    last_conversion_date = models.DateTimeField(default=timezone.now)
    last_drop_date = models.DateTimeField(default=timezone.now)
    last_grade_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s %s' % (self.name, self.year)

    def clean(self):
        if self.start_reg_date <= self.last_reg_date:
            if self.last_reg_date <= self.last_adviser_approval_date:
                if self.last_adviser_approval_date <= self.last_instructor_approval_date:
                    if self.last_cancellation_date <= self.last_conversion_date:
                        if self.last_instructor_approval_date <= self.last_conversion_date:
                            if self.last_conversion_date <= self.last_drop_date:
                                    if self.last_drop_date <= self.last_grade_date:
                                        return
        raise ValidationError('Dates must be in increasing order. Last registration date <= Last adviser approval date <= Last instructor approval date and so on.')

class Course(models.Model):
    num = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    term = models.ForeignKey(Term)
    credits = models.CharField(max_length=100, default='', verbose_name="Credits (ex: 3:0)")
    should_count_towards_cgpa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    timings = models.CharField(max_length=100, default='Not fixed yet')

    def get_num_credits():
        return sum(int(c) for c in re.split(r'[^0-9]', self.credits) if c.isdigit())

    def is_start_reg_date_passed(self):
        return timezone.now() > self.term.start_reg_date

    def is_last_reg_date_passed(self):
        return timezone.now() > self.term.last_reg_date

    def is_last_cancellation_date_passed(self):
        return timezone.now() > self.term.last_cancellation_date

    def is_last_adviser_approval_date_passed(self):
        return timezone.now() > self.term.last_adviser_approval_date

    def is_last_instructor_approval_date_passed(self):
        return timezone.now() > self.term.last_instructor_approval_date

    def is_last_conversion_date_passed(self):
        return timezone.now() > self.term.last_conversion_date

    def is_last_drop_date_passed(self):
        return timezone.now() > self.term.last_drop_date

    def is_last_grade_date_passed(self):
        return timezone.now() > self.term.last_grade_date

    def is_instructor_review_pending(self):
        return Participant.objects.filter(course=self, user__user_type=User.USER_TYPE_STUDENT, is_instructor_reviewed=False).first()

    def __unicode__(self):
        return self.num + ' ' + self.title + ' (%s, %s)' % (self.credits, self.term)

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
