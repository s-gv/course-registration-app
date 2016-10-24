from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import timedelta
from coursereg import models
from django.contrib.auth import update_session_auth_hash
from coursereg import utils
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from coursereg import utils
from django.utils import timezone
from collections import defaultdict

@login_required
def report(request):
    if not request.user.user_type == models.User.USER_TYPE_DCC:
        raise PermissionDenied
    from_date = timezone.now()
    to_date = timezone.now()
    if request.GET.get('from_date') and request.GET.get('to_date'):
        from_date = utils.parse_datetime_str(request.GET['from_date'])
        to_date = utils.parse_datetime_str(request.GET['to_date'])

    participants = [p for p in models.Participant.objects.filter(
        user__department=request.user.department,
        user__user_type=models.User.USER_TYPE_STUDENT,
        course__term__last_reg_date__range=[from_date, to_date]
    ).order_by('user__degree', 'user__full_name')]

    context = {
        'user_type': 'dcc',
        'nav_active': 'report',
        'user_email': request.user.email,
        'dept': request.user.department,
        'default_from_date': utils.datetime_to_str(from_date),
        'default_to_date': utils.datetime_to_str(to_date),
        'participants': participants,
    }
    return render(request, 'coursereg/dcc_report.html', context)

@login_required
def review(request):
    if not request.user.user_type == models.User.USER_TYPE_DCC:
        raise PermissionDenied

    pending_advisers = set(p.user.adviser for p in models.Participant.objects.filter(user__department=request.user.department, participant_type=models.Participant.PARTICIPANT_STUDENT, is_adviser_reviewed=False))
    pending_instructors = set(instructor for p in models.Participant.objects.filter(user__department=request.user.department, participant_type=models.Participant.PARTICIPANT_STUDENT, is_instructor_reviewed=False) for instructor in p.course.instructors())
    pending_faculty = pending_advisers | pending_instructors

    active_students = defaultdict(list)
    oldest_recent_year = timezone.now().year - 1
    for student in models.User.objects.filter(user_type=models.User.USER_TYPE_STUDENT, is_active=True, department=request.user.department).order_by('-is_dcc_review_pending', '-date_joined','full_name'):
        regd = student.date_joined
        if regd.year >= oldest_recent_year:
            active_students['%s (Joined in %s %s)' % (student.degree, regd.strftime('%b'), regd.strftime('%Y'))].append(student)
        else:
            active_students['%s (Joined before %s)' % (student.degree, oldest_recent_year)].append(student)

    print active_students

    context = {
        'user_type': 'dcc',
        'nav_active': 'review',
        'user_email': request.user.email,
        'pending_faculty': pending_faculty,
        'pending_advisers': pending_advisers,
        'pending_instructors': pending_instructors,
        'degrees': models.Degree.objects.all().order_by('name'),
        'active_students': dict(active_students),
    }
    return render(request, 'coursereg/dcc_review.html', context)

@login_required
def detail(request, student_id):
    if not request.user.user_type == models.User.USER_TYPE_DCC:
        raise PermissionDenied
    student = models.User.objects.get(id=student_id)
    if not student or student.department != request.user.department:
        raise PermissionDenied

    context = {
        'user_type': 'dcc',
        'nav_active': 'review',
        'user_email': request.user.email,
        'student': student,
        'participants': models.Participant.objects.filter(user=student).order_by('-course__term__last_reg_date'),
        'notifications': [(n.created_at, models.Notification.ORIGIN_CHOICES[n.origin][1], n.message)
            for n in models.Notification.objects.filter(user=student, is_dcc_acknowledged=False).order_by('-created_at')],
    }
    return render(request, 'coursereg/dcc_detail.html', context)

@require_POST
@login_required
def approve(request, student_id):
    if not request.user.user_type == models.User.USER_TYPE_DCC:
        raise PermissionDenied
    student = models.User.objects.get(id=student_id)
    if not student or student.department != request.user.department:
        raise PermissionDenied
    student.is_dcc_review_pending = False
    student.is_dcc_sent_notification = False
    student.save()
    models.Notification.objects.filter(user=student).update(is_dcc_acknowledged=True)
    messages.success(request, 'Courses registered by %s approved.' % student.full_name)
    return redirect('coursereg:dcc_review')
