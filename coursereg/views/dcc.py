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
from student import get_desc

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
def detail(request, student_id):
    assert request.user.user_type == models.User.USER_TYPE_DCC
    student = models.User.objects.get(id=student_id)
    assert student
    assert student.department == request.user.department
    participants = [(
        p.id,
        p.state == models.Participant.STATE_CREDIT,
        p.state == models.Participant.STATE_AUDIT,
        p.state == models.Participant.STATE_DROP,
        p.course, get_desc(p),
        not p.is_adviser_approved
    ) for p in models.Participant.objects.filter(user=student).order_by('-course__last_reg_date', 'course__title')]
    context = {
        'user_type': 'dcc',
        'user_email': request.user.email,
        'student': student,
        'participants': participants,
        'notifications': [(n.created_at, models.Notification.ORIGIN_CHOICES[n.origin][1], n.message)
            for n in models.Notification.objects.filter(user=student, origin=models.Notification.ORIGIN_DCC, is_dcc_acknowledged=False).order_by('-created_at')],
    }
    return render(request, 'coursereg/dcc_detail.html', context)

@login_required
def approve(request, student_id):
    assert request.method == 'POST'
    assert request.user.user_type == models.User.USER_TYPE_DCC
    student = models.User.objects.get(id=student_id)
    assert student
    assert student.department == request.user.department
    student.is_dcc_review_pending = False
    student.save()
    models.Notification.objects.filter(user=student, origin=models.Notification.ORIGIN_DCC).update(is_dcc_acknowledged=True,
                                                                                                   is_student_acknowledged=True,
                                                                                                   is_adviser_acknowledged=True)
    messages.success(request, 'Courses registered by %s approved.' % student.full_name)
    return redirect(request.POST.get('next', reverse('coursereg:index')))
