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
                instructor_state=models.Participant.INSTRUCTOR_PENDING
            )
            messages.success(request, 'Successfully applied for %s.' % course)

    return redirect(request.GET.get('next', reverse('coursereg:index')))

@login_required
def update(request):
    pass

@login_required
def delete(request, participant_id):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=participant_id)
    assert str(participant.user.id) == str(request.user.id)
    participant.delete()
    return redirect(request.GET.get('next', reverse('coursereg:index')))
