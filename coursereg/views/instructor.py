from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from coursereg import models

@login_required
def index(request):
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
    reg_requests = [
        (p.state == models.Participant.STATE_CREDIT, p.id, p.user)
        for p in models.Participant.objects.filter(course=course,
                                                   course__last_reg_date__gte=date.today(),
                                                   is_adviser_approved=True,
                                                   is_instructor_approved=False)]

    crediting = models.Participant.objects.filter(course=course,
                                                  state=models.Participant.STATE_CREDIT,
                                                  is_adviser_approved=True,
                                                  is_instructor_approved=True)
    auditing = models.Participant.objects.filter(course=course,
                                                 state=models.Participant.STATE_AUDIT,
                                                 is_adviser_approved=True,
                                                 is_instructor_approved=True)
    dropped = models.Participant.objects.filter(course=course,
                                                state=models.Participant.STATE_DROP,
                                                is_adviser_approved=True,
                                                is_instructor_approved=True)

    context = {
        'user_type': 'faculty',
        'nav_active': 'instructor',
        'user_email': request.user.email,
        'course': course,
        'registration_requests': reg_requests,
        'crediting': crediting,
        'auditing': auditing,
        'dropped': dropped
    }
    return render(request, 'coursereg/instructor_detail.html', context)
