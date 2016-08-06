from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import timedelta
from coursereg import models
from django.core.mail import send_mail
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

@require_POST
@login_required
def create(request):
    course_id = request.POST['course_id']
    user_id = request.POST['user_id']
    reg_type = request.POST['reg_type']

    user = models.User.objects.get(id=user_id)
    if request.POST['origin'] == 'adviser':
        if not request.user == user.adviser: raise PermissionDenied
    else:
        if not request.user == user: raise PermissionDenied

    if not course_id:
        messages.error(request, 'Select a course.')
    else:
        course = models.Course.objects.get(id=course_id)
        if course.is_last_reg_date_passed(): raise PermissionDenied
        if models.Participant.objects.filter(user__id=user_id, course__id=course_id):
            messages.error(request, 'Already registered for %s.' % course)
        else:
            adviser_approve = course.auto_adviser_approve or user.adviser.auto_advisee_approve
            participant = models.Participant.objects.create(
                user_id=user_id,
                course_id=course_id,
                participant_type=models.Participant.PARTICIPANT_STUDENT,
                is_credit=(reg_type == 'credit'),
                should_count_towards_cgpa=True,
                is_adviser_approved=adviser_approve,
                is_instructor_approved=adviser_approve and course.auto_instructor_approve
            )
            if request.POST['origin'] == 'adviser':
                participant.is_adviser_approved = True
                participant.is_instructor_approved = course.auto_instructor_approve
                participant.save()
                msg = 'Applied for %s.' % participant.course
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_ADVISER,
                                                   message=msg)
                try:
                    send_mail('Coursereg notification', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
                except:
                    messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
            else:
                messages.success(request, 'Applied for %s.' % course)

    return redirect(request.POST.get('next', reverse('coursereg:index')))

@require_POST
@login_required
def update(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    if request.POST['origin'] == 'instructor':
        if not models.Participant.objects.filter(course=participant.course,
                user=request.user, participant_type=models.Participant.PARTICIPANT_INSTRUCTOR):
            raise PermissionDenied
        if request.POST['action'] == 'approve':
            if not participant.is_adviser_approved: raise PermissionDenied
            participant.is_instructor_approved = True
            participant.save()
            student = participant.user
            student.is_dcc_review_pending = True
            student.save()
        elif request.POST['action'] == 'reject':
            if participant.is_instructor_approved: raise PermissionDenied
            msg = 'Application for %s has been rejected by the course instructor.' % participant.course
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_INSTRUCTOR,
                                               message=msg)
            participant.delete()
            try:
                send_mail('Coursereg notification', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
        elif request.POST['action'] == 'grade':
            if participant.course.is_last_grade_date_passed(): raise PermissionDenied
            participant.grade = models.Grade.objects.get(id=request.POST['grade'])
            participant.save()
    elif request.POST['origin'] == 'adviser':
        if not participant.user.adviser == request.user: raise PermissionDenied
        if request.POST['action'] == 'state_change':
            if participant.course.is_drop_date_passed(): raise PermissionDenied
            state = request.POST['state']
            if state == 'credit':
                if not participant.is_credit:
                    if participant.course.is_last_conversion_date_passed(): raise PermissionDenied
                participant.is_credit = True
                participant.is_drop = False
            elif state == 'audit':
                if participant.is_credit:
                    if participant.course.is_last_conversion_date_passed(): raise PermissionDenied
                participant.is_credit = False
                participant.is_drop = False
            elif state == 'drop':
                participant.is_drop = True
            participant.save()
            student = participant.user
            student.is_dcc_review_pending = True
            student.save()
            msg = 'Registration for %s has changed to %s.' % (participant.course, state)
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_ADVISER,
                                               message=msg)
            try:
                send_mail('Coursereg notification', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
        elif request.POST['action'] == 'approve':
            participant.is_adviser_approved = True
            participant.is_instructor_approved = participant.course.auto_instructor_approve
            participant.save()
        elif request.POST['action'] == 'delete':
            if participant.course.is_last_reg_date_passed() and participant.is_instructor_approved: raise PermissionDenied
            if participant.is_instructor_approved:
                student = participant.user
                student.is_dcc_review_pending = True
                student.save()
            msg = 'Application for %s has been rejected by your adviser.' % participant.course
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_ADVISER,
                                               message=msg)
            participant.delete()
            try:
                send_mail('Coursereg notification', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
    return redirect(request.POST.get('next', reverse('coursereg:index')))

@require_POST
@login_required
def approve_all(request):
    student = models.User.objects.get(id=request.POST['student_id'])
    if request.POST['origin'] == 'adviser':
        if not student.adviser == request.user: raise PermissionDenied
        models.Participant.objects.filter(user=student).update(is_adviser_approved=True)
        models.Participant.objects.filter(course__auto_instructor_approve=True, user=student).update(is_instructor_approved=True)
    elif request.POST['origin'] == 'instructor':
        course = models.Course.objects.get(id=request.POST['course_id'])
        if not models.Participant.objects.filter(course=course,
                user=request.user, participant_type=models.Participant.PARTICIPANT_INSTRUCTOR):
            raise PermissionDenied
        if models.Participant.objects.filter(user=student, is_adviser_approved=True, is_instructor_approved=False):
            student.is_dcc_review_pending = True
            student.save()
        models.Participant.objects.filter(course=course, is_adviser_approved=True).update(is_instructor_approved=True)

    return redirect(request.POST.get('next', reverse('coursereg:index')))

@require_POST
@login_required
def delete(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    student = participant.user
    if not participant.user == request.user: raise PermissionDenied
    if participant.is_adviser_approved and not student.adviser.auto_advisee_approve: raise PermissionDenied
    if participant.user.adviser.auto_advisee_approve and participant.is_instructor_approved:
        student.is_dcc_review_pending = True
        student.save()
    if participant.course.is_last_reg_date_passed(): raise PermissionDenied
    participant.delete()
    return redirect(request.GET.get('next', reverse('coursereg:index')))
