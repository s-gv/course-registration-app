from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models
from student import get_desc
from django.core.exceptions import PermissionDenied

@login_required
def index(request):
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    context = {
        'user_type': 'faculty',
        'nav_active': 'adviser',
        'user_email': request.user.email,
        'students': [u for u in models.User.objects.filter(adviser=request.user).order_by('-is_active', '-date_joined')]
    }
    return render(request, 'coursereg/adviser.html', context)

@login_required
def detail(request, student_id):
    student = models.User.objects.get(id=student_id)
    if not request.user == student.adviser:
        raise PermissionDenied
    context = {
        'user_type': 'faculty',
        'user_email': request.user.email,
        'student': student,
        'notifications': [(n.created_at, models.Notification.ORIGIN_CHOICES[n.origin][1], n.message)
            for n in models.Notification.objects.filter(user=student, is_adviser_acknowledged=False).order_by('-created_at')],
        'participants': [(p, get_desc(p)) for p in models.Participant.objects.filter(user=student).order_by('-course__last_reg_date')],
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now()+timedelta(days=100))
    }
    return render(request, 'coursereg/adviser_detail.html', context)
