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

    PROGRAM_OTHER = 0
    PROGRAM_MTECH = 1
    PROGRAM_MSC = 2
    PROGRAM_PHD = 3
    PROGRAM_ME = 4


    email = models.EmailField(max_length=254, unique=True)
    full_name = models.CharField(max_length=250)
    user_type = models.IntegerField(default=USER_TYPE_STUDENT, choices=(
        (USER_TYPE_FACULTY, "Faculty"),
        (USER_TYPE_STUDENT, "Student"),
        (USER_TYPE_OTHER, "Other"),
    ))
    adviser = models.ForeignKey('self', null=True, on_delete=models.CASCADE)
    program = models.IntegerField(default=PROGRAM_OTHER, choices=(
        (PROGRAM_OTHER, 'Other'),
        (PROGRAM_ME, 'ME'),
        (PROGRAM_MTECH, 'MTech'),
        (PROGRAM_MSC, 'MSc'),
        (PROGRAM_PHD, 'PhD'),
    ))
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
