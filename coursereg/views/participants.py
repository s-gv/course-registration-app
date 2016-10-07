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
        if not models.Config.can_adviser_add_courses_for_students(): raise PermissionDenied
    else:
        if not request.user == user: raise PermissionDenied

    if not course_id:
        messages.error(request, 'Select a course.')
    else:
        course = models.Course.objects.get(id=course_id)
        if not course.is_start_reg_date_passed(): raise PermissionDenied
        if request.POST['origin'] == 'adviser':
            if course.is_last_adviser_approval_date_passed(): raise PermissionDenied
        else:
            if course.is_last_reg_date_passed(): raise PermissionDenied
        if models.Participant.objects.filter(user__id=user_id, course__id=course_id):
            messages.error(request, 'Already registered for %s.' % course)
        else:
            adviser_approve = course.auto_adviser_approve or user.adviser.auto_advisee_approve
            participant = models.Participant.objects.create(
                user_id=user_id,
                course_id=course_id,
                participant_type=models.Participant.PARTICIPANT_STUDENT,
                registration_type=models.RegistrationType.objects.get(pk=reg_type),
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
            if participant.course.is_last_instructor_approval_date_passed(): raise PermissionDenied
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
        if request.POST['action'] == 'reg_type_change':
            reg_type = models.RegistrationType.objects.get(pk=request.POST['reg_type'])
            if participant.course.is_last_conversion_date_passed(): raise PermissionDenied
            participant.registration_type = reg_type
            participant.save()
            msg = 'Registration for %s by %s has changed to %s.' % (participant.course, participant.user, reg_type)
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_ADVISER,
                                               message=msg)
            try:
                send_mail('Coursereg', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
        if request.POST['action'] == 'drop':
            if participant.course.is_last_drop_date_passed(): raise PermissionDenied
            participant.is_drop = True
            participant.save()
            msg = '%s dropped by %s.' % (participant.course, participant.user)
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_ADVISER,
                                               message=msg)
            try:
                send_mail('Coursereg', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
        if request.POST['action'] == 'undrop':
            if participant.course.is_last_drop_date_passed(): raise PermissionDenied
            participant.is_drop = False
            participant.save()
            msg = 'Drop request for %s by %s cancelled.' % (participant.course, participant.user)
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_ADVISER,
                                               message=msg)
            try:
                send_mail('Coursereg', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
    elif request.POST['origin'] == 'student':
        if not request.user == participant.user: raise PermissionDenied
        if participant.lock_from_student:
            messages.error(request, "Account privileges restricted. Contact the administrator for more information.")
        else:
            if request.POST['action'] == 'reg_type_change':
                reg_type = models.RegistrationType.objects.get(pk=request.POST['reg_type'])
                if participant.course.is_last_conversion_date_passed(): raise PermissionDenied
                participant.registration_type = reg_type
                participant.save()
                msg = 'Registration for %s by %s has changed to %s.' % (participant.course, participant.user, reg_type)
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_STUDENT,
                                                   message=msg)
                try:
                    send_mail('Coursereg', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.adviser.email])
                except:
                    messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
            if request.POST['action'] == 'drop':
                if participant.course.is_last_drop_date_passed(): raise PermissionDenied
                participant.is_drop = True
                participant.save()
                msg = '%s dropped by %s.' % (participant.course, participant.user)
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_STUDENT,
                                                   message=msg)
                try:
                    send_mail('Coursereg', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.adviser.email])
                except:
                    messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
            if request.POST['action'] == 'undrop':
                if participant.course.is_last_drop_date_passed(): raise PermissionDenied
                participant.is_drop = False
                participant.save()
                msg = 'Drop request for %s by %s cancelled.' % (participant.course, participant.user)
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_STUDENT,
                                                   message=msg)
                try:
                    send_mail('Coursereg', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.adviser.email])
                except:
                    messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')

    return redirect(request.POST.get('next', reverse('coursereg:index')))

@require_POST
@login_required
def approve_all(request):
    if request.POST['origin'] == 'adviser':
        student = models.User.objects.get(id=request.POST['student_id'])
        if not student.adviser == request.user: raise PermissionDenied
        for p in models.Participant.objects.filter(user=student, is_adviser_approved=False):
            if not p.course.is_last_adviser_approval_date_passed():
                p.is_adviser_approved = True
                if p.course.auto_instructor_approve:
                    p.is_instructor_approved = True
                p.save()
            else:
                messages.error(request, "Last date for %s has passed" % p.course)
    elif request.POST['origin'] == 'instructor':
        course = models.Course.objects.get(id=request.POST['course_id'])
        if not models.Participant.objects.filter(course=course,
                user=request.user, participant_type=models.Participant.PARTICIPANT_INSTRUCTOR):
            raise PermissionDenied
        if course.is_last_instructor_approval_date_passed(): raise PermissionDenied
        for p in models.Participant.objects.filter(
                course=course,
                participant_type=models.Participant.PARTICIPANT_STUDENT,
                is_adviser_approved=True,
                is_instructor_approved=False):
            p.is_instructor_approved = True
            p.save()
            student = p.user
            student.is_dcc_review_pending = True
            student.save()

    return redirect(request.POST.get('next', reverse('coursereg:index')))

@require_POST
@login_required
def delete(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    if request.user == participant.user:
        # Student requested deletion
        if request.participant.course.is_last_reg_date_passed(): raise PermissionDenied
    elif request.user == participant.user.adviser:
        # Adviser requested deletion
        if participant.course.is_last_adviser_approval_date_passed(): raise PermissionDenied
    else:
        raise PermissionDenied
    participant.delete()
    return redirect(request.POST.get('next', reverse('coursereg:index')))
