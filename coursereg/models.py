from __future__ import unicode_literals

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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

class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_FACULTY = 0
    USER_TYPE_STUDENT = 1
    USER_TYPE_OTHER = 2
    #USER_TYPE_ADMIN = 3

    PROGRAM_OTHER = 0
    PROGRAM_MTECH = 1
    PROGRAM_MSC = 2
    PROGRAM_PHD = 3
    PROGRAM_ME = 4

    PROGRAM_CHOICES = (
        (PROGRAM_OTHER, 'Other'),
        (PROGRAM_MTECH, 'MTech'),
        (PROGRAM_MSC, 'MSc'),
        (PROGRAM_PHD, 'PhD'),
        (PROGRAM_ME, 'ME'),
    )

    email = models.EmailField(max_length=254, unique=True)
    full_name = models.CharField(max_length=250)
    user_type = models.IntegerField(default=USER_TYPE_STUDENT, choices=(
        (USER_TYPE_FACULTY, "Faculty"),
        (USER_TYPE_STUDENT, "Student"),
        (USER_TYPE_OTHER, "Other"),
    ))
    adviser = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, limit_choices_to={'user_type': USER_TYPE_FACULTY})
    program = models.IntegerField(default=PROGRAM_OTHER, choices=PROGRAM_CHOICES)
    date_joined = models.DateTimeField(default=timezone.now)
    sr_no = models.CharField(max_length=200, default='-')

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        return self.full_name.strip()

    def get_short_name(self):
        return self.full_name.strip()


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
    credits = models.IntegerField(default=3)
    department = models.CharField(max_length=100)

    def __unicode__(self):
        return self.num + ' ' + self.title + ' (%s %s)' % (self.TERM_CHOICES[self.term][1], self.last_reg_date.year)

class Participant(models.Model):
    PARTICIPANT_CREDIT = 0
    PARTICIPANT_AUDIT = 1
    PARTICIPANT_INSTRUCTOR = 2
    PARTICIPANT_TA = 3

    PARTICIPANT_CHOICES = (
        (PARTICIPANT_CREDIT, 'Credit'),
        (PARTICIPANT_AUDIT, 'Audit'),
        (PARTICIPANT_INSTRUCTOR, 'Instructor'),
        (PARTICIPANT_TA, 'TA'),
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

    STATE_REQUESTED = 0
    STATE_ADVISOR_DONE = 1
    STATE_INSTRUCTOR_DONE = 2
    STATE_FINAL_APPROVED = 3
    STATE_NA = 4
    STATE_ADVISOR_REJECT =5
    STATE_INSTRUCTOR_REJECT = 6

    STATE_CHOICES = (
        (STATE_REQUESTED, 'Requested'),
        (STATE_ADVISOR_DONE, 'Advisor approved'),
        (STATE_INSTRUCTOR_DONE, 'Instructor approved'),
        (STATE_FINAL_APPROVED, 'Final approved'),
        (STATE_NA, 'N/A'),
        (STATE_ADVISOR_REJECT, 'Advisor rejected'),
        (STATE_INSTRUCTOR_REJECT, 'Instructor rejected')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    participant_type = models.IntegerField(default=PARTICIPANT_INSTRUCTOR, choices=PARTICIPANT_CHOICES)
    state = models.IntegerField(default=STATE_NA, choices=STATE_CHOICES)
    grade = models.IntegerField(default=GRADE_NA, choices=GRADE_CHOICES)

    def __unicode__(self):
        return self.user.email + " in %s - %s" % (self.course.num, self.course.title)

class Faq(models.Model):
    FAQ_STUDENT = 0
    FAQ_FACULTY = 1

    FAQ_CHOICES = (
        (FAQ_STUDENT, "Student"),
        (FAQ_FACULTY, "Faculty"),
    )

    faq_for = models.IntegerField(default=FAQ_STUDENT, choices=FAQ_CHOICES)
    question = models.TextField()
    answer = models.TextField()

    def __unicode__(self):
        return self.question
