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
        is_adviser_approved=True,
        is_instructor_approved=True,
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
    context = {
        'user_type': 'dcc',
        'nav_active': 'review',
        'faculty_approval_pending': models.Participant.objects.filter(
                Q(is_adviser_approved=False) | Q(is_instructor_approved=False),
                user__department=request.user.department,
                participant_type=models.Participant.PARTICIPANT_STUDENT).first(),
        'all_active_students': [student for student in models.User.objects.filter(
            user_type=models.User.USER_TYPE_STUDENT,
            is_active=True,
            department=request.user.department).order_by('full_name')],
        'user_email': request.user.email
    }
    return render(request, 'coursereg/dcc_review.html', context)

@login_required
def detail(request, student_id):
    if not request.user.user_type == models.User.USER_TYPE_DCC:
        raise PermissionDenied
    student = models.User.objects.get(id=student_id)
    if not student or student.department != request.user.department:
        raise PermissionDenied
    participants = [(
        p.id,
        p.should_count_towards_cgpa,
        p.is_credit,
        not p.is_credit,
        p.is_drop,
        p.course, utils.get_state_desc(p),
        not p.is_adviser_approved
    ) for p in models.Participant.objects.filter(user=student).order_by('-course__term__last_reg_date', 'course__title')]
    context = {
        'user_type': 'dcc',
        'nav_active': 'review',
        'user_email': request.user.email,
        'student': student,
        'participants': participants,
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
    student.save()
    models.Notification.objects.filter(user=student).update(is_dcc_acknowledged=True)
    messages.success(request, 'Courses registered by %s approved.' % student.full_name)
    return redirect('coursereg:dcc_review')

@require_POST
@login_required
def remind(request):
    if not request.user.user_type == models.User.USER_TYPE_DCC:
        raise PermissionDenied
    adviser_pending = models.Participant.objects.filter(
        participant_type=models.Participant.PARTICIPANT_STUDENT,
        is_adviser_approved=False,
        user__department=request.user.department,
    ).values('user__adviser').annotate(num_pending=Count('user__adviser'))

    courses_pending = models.Participant.objects.filter(
        participant_type=models.Participant.PARTICIPANT_STUDENT,
        user__department=request.user.department,
        is_adviser_approved=True,
        is_instructor_approved=False
    ).values_list('course', flat=True)

    instructor_pending = models.Participant.objects.filter(
        participant_type=models.Participant.PARTICIPANT_INSTRUCTOR,
        course__in=courses_pending
    ).values('user').annotate(num_courses=Count('user'))

    faculty_pending = set([p['user__adviser'] for p in adviser_pending] + [p['user'] for p in instructor_pending])
    msg = 'Please review pending approvals in the Coursereg website.'
    mail_send_failed = False
    for faculty_id in faculty_pending:
        faculty = models.User.objects.get(id=faculty_id)
        try:
            send_mail('Coursereg notification', msg, settings.DEFAULT_FROM_EMAIL, [faculty.email])
        except:
            mail_send_failed = True
            break

    if mail_send_failed:
        messages.warning(request, 'Failed to send email.')
    else:
        messages.success(request, 'Reminder e-mails sent.')

    return redirect('coursereg:dcc_review')
