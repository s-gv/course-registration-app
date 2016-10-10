from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models
from coursereg import utils
from django.core.exceptions import PermissionDenied

@login_required
def index(request):
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    context = {
        'user_type': 'faculty',
        'nav_active': 'adviser',
        'user_email': request.user.email,
        'students': models.User.objects.filter(adviser=request.user).order_by('-is_active', '-date_joined')
    }
    return render(request, 'coursereg/adviser.html', context)

@login_required
def detail(request, student_id):
    student = models.User.objects.get(id=student_id)
    if not request.user == student.adviser:
        raise PermissionDenied
    student.is_adviser_review_pending = False
    student.save()
    context = {
        'user_type': 'faculty',
        'nav_active': 'adviser',
        'user_email': request.user.email,
        'student': student,
        'reg_types': models.RegistrationType.objects.filter(is_active=True),
        'can_adviser_add_courses_for_students': models.Config.can_adviser_add_courses_for_students(),
        'notifications': [(n.created_at, models.Notification.ORIGIN_CHOICES[n.origin][1], n.message)
            for n in models.Notification.objects.filter(user=student, is_adviser_acknowledged=False).order_by('-created_at')],
        'participants': models.Participant.objects.filter(user=student).order_by('-course__term__last_reg_date'),
        'courses': models.Course.objects.filter(term__last_adviser_approval_date__gte=timezone.now(),
                                                term__start_reg_date__lte=timezone.now())
    }
    return render(request, 'coursereg/adviser_detail.html', context)
