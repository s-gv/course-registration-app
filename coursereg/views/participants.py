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
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings

@require_POST
@login_required
def create(request):
    course_id = request.POST['course_id']
    user_id = request.POST['user_id']
    reg_type = request.POST['reg_type']

    user = models.User.objects.get(id=user_id)
    if request.POST['origin'] == 'adviser':
        if not request.user == user.adviser: raise PermissionDenied
        if not settings.CAN_ADVISER_ADD_COURSES_FOR_STUDENTS: raise PermissionDenied
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
            participant = models.Participant.objects.create(
                user=user,
                course=course,
                participant_type=models.Participant.PARTICIPANT_STUDENT,
                registration_type=models.RegistrationType.objects.get(pk=reg_type),
                should_count_towards_cgpa=True,
            )
            participant.save()
            user.is_dcc_review_pending = True
            user.save()
            if request.POST['origin'] == 'adviser':
                participant.is_adviser_reviewed = True
                participant.save()
                msg = 'Enrolled in %s.' % participant.course
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_ADVISER,
                                                   message=msg)
                try:
                    send_mail('New course application', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
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
        if request.POST['action'] == 'review':
            participant.is_instructor_reviewed = True
            participant.save()
        if request.POST['action'] == 'grade':
            if participant.course.is_last_grade_date_passed(): raise PermissionDenied
            if request.POST['grade'] == 'null':
                participant.grade = None
            else:
                participant.grade = models.Grade.objects.get(id=request.POST['grade'])
            participant.is_instructor_reviewed = True
            participant.save()
    elif request.POST['origin'] == 'adviser':
        if not participant.user.adviser == request.user: raise PermissionDenied
        if request.POST['action'] == 'review':
            participant.is_adviser_reviewed = True
            participant.save()
        if request.POST['action'] == 'reg_type_change':
            reg_type = models.RegistrationType.objects.get(pk=request.POST['reg_type'])
            if participant.course.is_last_conversion_date_passed(): raise PermissionDenied
            msg = 'Registration for %s has changed from %s to %s.' % (participant.course, participant.registration_type, reg_type)
            participant.registration_type = reg_type
            participant.is_adviser_reviewed = True
            participant.save()
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_ADVISER,
                                               message=msg)
            try:
                send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
        if request.POST['action'] == 'drop':
            if participant.course.is_last_drop_date_passed(): raise PermissionDenied
            participant.is_drop = True
            participant.is_adviser_reviewed = True
            participant.save()
            msg = 'Course %s dropped.' % participant.course
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_ADVISER,
                                               message=msg)
            try:
                send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
        if request.POST['action'] == 'undrop':
            if participant.course.is_last_drop_date_passed(): raise PermissionDenied
            participant.is_drop = False
            participant.is_adviser_reviewed = True
            participant.save()
            msg = 'Drop request for %s is cancelled.' % participant.course
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_ADVISER,
                                               message=msg)
            try:
                send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
        if request.POST['action'] == 'disable_student_edits':
            participant.lock_from_student = True
            participant.is_adviser_reviewed = True
            participant.save()
        if request.POST['action'] == 'enable_student_edits':
            participant.lock_from_student = False
            participant.is_adviser_reviewed = True
            participant.save()
    elif request.POST['origin'] == 'student':
        student = request.user
        if not request.user == participant.user: raise PermissionDenied
        if participant.lock_from_student:
            messages.error(request, "Permission denied.")
        else:
            if request.POST['action'] == 'reg_type_change':
                reg_type = models.RegistrationType.objects.get(pk=request.POST['reg_type'])
                if participant.course.is_last_conversion_date_passed(): raise PermissionDenied
                msg = 'Registration for %s by %s has changed from %s to %s.' % (participant.course, participant.user, participant.registration_type, reg_type)
                participant.registration_type = reg_type
                participant.is_adviser_reviewed = False
                participant.save()
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_STUDENT,
                                                   message=msg)
                try:
                    send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.adviser.email])
                except:
                    messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
            if request.POST['action'] == 'drop':
                if participant.course.is_last_drop_date_passed(): raise PermissionDenied
                participant.is_drop = True
                participant.is_adviser_reviewed = False
                participant.save()
                msg = '%s has dropped %s.' % (participant.user, participant.course)
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_STUDENT,
                                                   message=msg)
                try:
                    send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.adviser.email])
                except:
                    messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
            if request.POST['action'] == 'undrop':
                if participant.course.is_last_drop_date_passed(): raise PermissionDenied
                participant.is_drop = False
                participant.is_adviser_reviewed = False
                participant.save()
                msg = 'Drop request for %s by %s cancelled.' % (participant.course, participant.user)
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_STUDENT,
                                                   message=msg)
                try:
                    send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.adviser.email])
                except:
                    messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')

    return redirect(request.POST.get('next', reverse('coursereg:index')))

@require_POST
@login_required
def delete(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    student = participant.user
    if request.POST['origin'] == 'student':
        if request.user != participant.user: raise PermissionDenied
        if participant.course.is_last_cancellation_date_passed(): raise PermissionDenied
        if participant.lock_from_student:
            messages.error(request, "Permission denied.")
        else:
            participant.delete()
            if participant.course.is_last_reg_date_passed():
                msg = 'Registration for %s was cancelled by %s.' % (participant.course, student)
                models.Notification.objects.create(user=participant.user,
                                                   origin=models.Notification.ORIGIN_STUDENT,
                                                   message=msg)
                try:
                    send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.adviser.email])
                except:
                    messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
    elif request.POST['origin'] == 'adviser':
        if request.user != participant.user.adviser: raise PermissionDenied
        if participant.course.is_last_adviser_approval_date_passed(): raise PermissionDenied
        participant.delete()
        msg = 'Registration for %s was cancelled.' % participant.course
        models.Notification.objects.create(user=participant.user,
                                           origin=models.Notification.ORIGIN_ADVISER,
                                           message=msg)
        try:
            send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
        except:
            messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
    elif request.POST['origin'] == 'instructor':
        if not models.Participant.objects.filter(course=participant.course, user=request.user, participant_type=models.Participant.PARTICIPANT_INSTRUCTOR).first(): raise PermissionDenied
        if participant.course.is_last_instructor_approval_date_passed(): raise PermissionDenied
        participant.delete()
        msg = 'Registration for %s by %s was cancelled by the course instructor.' % (participant.course, participant.user)
        models.Notification.objects.create(user=participant.user,
                                           origin=models.Notification.ORIGIN_INSTRUCTOR,
                                           message=msg)
        try:
            send_mail('Course registration changed', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
        except:
            messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
    return redirect(request.POST.get('next', reverse('coursereg:index')))
