from __future__ import unicode_literals

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import re

class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    def abbreviation(self):
        r = re.search(r'\((.+)\)\s*$', self.name)
        if r:
            return r.group(1)
        else:
            return self.name

class Degree(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

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
    is_dcc_review_pending = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

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
    term = models.IntegerField(default=TERM_AUG, choices=TERM_CHOICES)
    last_reg_date = models.DateField(verbose_name="Last Registration Date", default=timezone.now)
    last_drop_date = models.DateField(verbose_name="Last Drop Date", default=timezone.now)
    credits = models.IntegerField(default=3)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.num + ' ' + self.title + ' (%s %s)' % (self.TERM_CHOICES[self.term][1], self.last_reg_date.year)

class Participant(models.Model):
    PARTICIPANT_STUDENT = 0
    PARTICIPANT_INSTRUCTOR = 1
    PARTICIPANT_TA = 2

    PARTICIPANT_CHOICES = (
        (PARTICIPANT_STUDENT, 'Student'),
        (PARTICIPANT_INSTRUCTOR, 'Instructor'),
        (PARTICIPANT_TA, 'TA'),
    )

    STATE_NA = 0
    STATE_CREDIT = 1
    STATE_AUDIT = 2
    STATE_DROP = 3

    STATE_CHOICES = (
        (STATE_NA, 'N/A'),
        (STATE_CREDIT, 'Credit'),
        (STATE_AUDIT, 'Audit'),
        (STATE_DROP, 'Drop'),
    )

    GRADE_NA = 0
    GRADE_S = 1
    GRADE_A = 2
    GRADE_B = 3
    GRADE_C = 4
    GRADE_D = 5
    GRADE_F = 6

    GRADE_CHOICES = (
        (GRADE_NA, 'N/A'),
        (GRADE_S, 'S'),
        (GRADE_A, 'A'),
        (GRADE_B, 'B'),
        (GRADE_C, 'C'),
        (GRADE_D, 'D'),
        (GRADE_F, 'F'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    participant_type = models.IntegerField(default=PARTICIPANT_INSTRUCTOR, choices=PARTICIPANT_CHOICES)
    state = models.IntegerField(default=STATE_NA, choices=STATE_CHOICES)
    grade = models.IntegerField(default=GRADE_NA, choices=GRADE_CHOICES)
    is_adviser_approved = models.BooleanField(default=False)
    is_instructor_approved = models.BooleanField(default=False)

    def __unicode__(self):
        return self.user.email + " in %s - %s" % (self.course.num, self.course.title)

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
