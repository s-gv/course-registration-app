from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models
from . import student, faculty, dcc
from django.contrib.auth import update_session_auth_hash

@login_required
def index(request):
    if request.user.is_superuser:
        return redirect('admin:index')
    elif request.user.user_type == models.User.USER_TYPE_STUDENT:
        return student.index(request)
    elif request.user.user_type == models.User.USER_TYPE_FACULTY:
        return faculty.index(request)
    elif request.user.user_type == models.User.USER_TYPE_DCC:
        return dcc.index(request)
    else:
        messages.error(request, "User type not recognized.")
        return redirect('coursereg:fatal')

def fatal_error(request):
    context = {}
    return render(request, 'coursereg/fatal.html', context)

def faq(request):
    context = {
        'nav_active': 'faq',
        'user_email': request.user.email
    }
    if request.user.user_type == models.User.USER_TYPE_STUDENT:
        context['faqs'] = models.Faq.objects.filter(faq_for=models.Faq.FAQ_STUDENT)
        context['user_type'] = 'student'
    elif request.user.user_type == models.User.USER_TYPE_FACULTY:
        context['faqs'] = models.Faq.objects.filter(faq_for=models.Faq.FAQ_FACULTY)
        context['user_type'] = 'faculty'
    elif request.user.user_type == models.User.USER_TYPE_DCC:
        context['faqs'] = models.Faq.objects.filter(faq_for=models.Faq.FAQ_DCC)
        context['user_type'] = 'dcc'
    else:
        raise Http404('User type not recognized')

    return render(request, 'coursereg/faq.html', context)

def profile(request):
    context = {
        'nav_active': 'profile',
        'user_email': request.user.email,
        'user_full_name': request.user.full_name
    }
    if request.user.user_type == models.User.USER_TYPE_STUDENT:
        context['user_type'] = 'student'
        context['adviser_full_name'] = request.user.adviser.full_name
        context['degree'] = models.User.DEGREE_CHOICES[request.user.degree][1]
        context['department'] = request.user.department
        context['sr_no'] = request.user.sr_no
    elif request.user.user_type == models.User.USER_TYPE_FACULTY:
        context['user_type'] = 'faculty'
    elif request.user.user_type == models.User.USER_TYPE_DCC:
        context['user_type'] = 'dcc'

    return render(request, 'coursereg/profile.html', context)
