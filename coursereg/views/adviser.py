from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models

@login_required
def index(request):
    context = {
        'user_type': 'faculty',
        'nav_active': 'advisees',
        'user_email': request.user.email
    }
    return render(request, 'coursereg/adviser.html', context)

@login_required
def detail(request):
    context = {
        'user_type': 'faculty',
        'user_email': request.user.email
    }
    return render(request, 'coursereg/adviser_detail.html', context)
