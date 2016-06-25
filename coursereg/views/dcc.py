from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models
from django.contrib.auth import update_session_auth_hash
import smtplib
import logging

@login_required
def index(request):
    assert request.user.user_type == models.User.USER_TYPE_DCC
    context = {
        'user_type': 'dcc',
        'nav_active': 'home',
        'pending_students': [(student.full_name, student.email, student.id)
            for student in models.User.objects.filter(user_type=models.User.USER_TYPE_STUDENT,
                                                      is_dcc_review_pending=True,
                                                      is_active=True,
                                                      department=request.user.department).order_by('full_name')],
        'all_active_students': [(student.full_name, student.email, student.id)
            for student in models.User.objects.filter(user_type=models.User.USER_TYPE_STUDENT,
                                                      is_active=True,
                                                      department=request.user.department).order_by('full_name')],
        'user_email': request.user.email
    }
    return render(request, 'coursereg/dcc.html', context)

@login_required
def students_read(request, student_id):
    assert request.user.user_type == models.User.USER_TYPE_DCC
