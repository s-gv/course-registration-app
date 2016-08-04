from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import date, timedelta
from coursereg import models
from django.core.exceptions import PermissionDenied

@login_required
def index(request):
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    context = {
        'user_type': 'faculty',
        'nav_active': 'instructor',
        'user_email': request.user.email,
        'courses': [p.course for p in models.Participant.objects.filter(user=request.user).order_by('-course__last_reg_date')]
    }
    return render(request, 'coursereg/instructor.html', context)

@login_required
def detail(request, course_id):
    course = models.Course.objects.get(id=course_id)
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    if not models.Participant.objects.filter(course=course,
            user=request.user, participant_type=models.Participant.PARTICIPANT_INSTRUCTOR):
        raise PermissionDenied
    reg_requests = [
        (p.is_credit, p.id, p.user)
        for p in models.Participant.objects.filter(course=course,
                                                   is_adviser_approved=True,
                                                   is_instructor_approved=False)]

    crediting = models.Participant.objects.filter(course=course,
                                                  is_credit=True,
                                                  is_drop=False,
                                                  is_adviser_approved=True,
                                                  is_instructor_approved=True)
    auditing = models.Participant.objects.filter(course=course,
                                                 is_credit=False,
                                                 is_drop=False,
                                                 is_adviser_approved=True,
                                                 is_instructor_approved=True)
    dropped = models.Participant.objects.filter(course=course,
                                                is_drop=True,
                                                is_adviser_approved=True,
                                                is_instructor_approved=True)

    context = {
        'user_type': 'faculty',
        'user_email': request.user.email,
        'course': course,
        'registration_requests': reg_requests,
        'crediting': crediting,
        'auditing': auditing,
        'dropped': dropped,
        'grades': models.Grade.objects.all().order_by('-points'),
        'participants_for_export': models.Participant.objects.filter(course=course,
                                        is_adviser_approved=True,
                                        is_instructor_approved=True).order_by('is_drop').order_by('-is_credit')
    }
    return render(request, 'coursereg/instructor_detail.html', context)
