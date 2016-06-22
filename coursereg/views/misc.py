from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models
from . import student, faculty, light_admin, dcc
from django.contrib.auth import update_session_auth_hash

@login_required
def index(request):
    if request.user.is_superuser:
        return redirect('admin:index')
    elif request.user.user_type == models.User.USER_TYPE_STUDENT:
        return student.index(request)
    elif request.user.user_type == models.User.USER_TYPE_FACULTY:
        return faculty.faculty(request)
    elif request.user.user_type == models.User.USER_TYPE_DCC:
        return dcc.dcc(request)
    elif request.user.user_type == 2:
        return light_admin.admin(request)
    else:
        messages.error(request, "User type not recognized.")
        return redirect('coursereg:fatal')

def fatal_error(request):
    context = {}
    return render(request, 'coursereg/fatal.html', context)


def default_landing(request):
    context = {}
    return render(request, 'coursereg/default_landing.html', context)

