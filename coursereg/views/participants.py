from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models

@login_required
def create(request):
    assert request.method == 'POST'
    course_id = request.POST['course_id']
    user_id = request.POST['user_id']
    reg_type = request.POST['reg_type']
    assert str(user_id) == str(request.user.id)

    state = models.Participant.STATE_CREDIT
    if reg_type == 'audit':
        state = models.Participant.STATE_AUDIT

    if not course_id:
        messages.error(request, 'Select a course.')
    else:
        course = models.Course.objects.get(id=course_id)
        if models.Participant.objects.filter(user__id=user_id, course__id=course_id):
            messages.error(request, 'Already registered for %s.' % course)
        elif timezone.now().date() > course.last_reg_date:
            messages.error(request, 'Registration for %s is now closed.' % course)
        else:
            models.Participant.objects.create(
                user_id=user_id,
                course_id=course_id,
                participant_type=models.Participant.PARTICIPANT_STUDENT,
                state=state,
                grade=models.Participant.GRADE_NA,
                is_adviser_approved=False,
                is_instructor_approved=False
            )
            messages.success(request, 'Successfully applied for %s.' % course)

    return redirect(request.GET.get('next', reverse('coursereg:index')))

@login_required
def update(request, participant_id):
    participant = models.Participant.objects.get(id=participant_id)
    if request.POST['origin'] == 'instructor':
        if request.POST['action'] == 'approve':
            participant.is_instructor_approved = True
            participant.save()
        elif request.POST['action'] == 'reject':
            models.Notification.objects.create(user=participant.user,
                                               origin=models.Notification.ORIGIN_INSTRUCTOR,
                                               message='Rejected application for %s' % participant.course)
            participant.delete()
        elif request.POST['action'] == 'grade':
            participant.grade = int(request.POST['grade'])
            participant.save()
    return redirect(request.POST.get('next', reverse('coursereg:index')))

@login_required
def approve_all(request):
    course = models.Course.objects.get(id=request.POST['course_id'])
    models.Participant.objects.filter(course=course, is_adviser_approved=True).update(is_instructor_approved=True)
    return redirect(request.POST.get('next', reverse('coursereg:index')))

@login_required
def delete(request, participant_id):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=participant_id)
    assert str(participant.user.id) == str(request.user.id)
    participant.delete()
    return redirect(request.GET.get('next', reverse('coursereg:index')))
