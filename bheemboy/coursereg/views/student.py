from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models
from django.contrib.auth import update_session_auth_hash
from . import user

def index(request):
    if not request.user.adviser:
        messages.error(request, 'Adviser not assigned. Contact the administrator.')
        return redirect('coursereg:fatal_error')
    participants = [
        (
            p.course,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.state == models.Participant.STATE_REQUESTED,
            p.id
        ) for p in models.Participant.objects.filter(user=request.user)]
    context = {
		'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now()+timedelta(days=100)),
    }
    return render(request, 'coursereg/student.html', context)

@login_required
def faq(request):
	context = {
		'user_email': request.user.email,
	}
	return render(request, 'coursereg/student_faq.html', context)

@login_required
def profile(request):
    context = {
		'user_email': request.user.email,
        'user_full_name': request.user.full_name,
        'user_id': request.user.id,
        'adviser_full_name': request.user.adviser.full_name,
        'program': models.User.PROGRAM_CHOICES[request.user.program][1],
        'sr_no': request.user.sr_no,
    }
    return render(request, 'coursereg/student_profile.html', context)

@login_required
def participant_delete(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    assert participant.user_id == request.user.id
    if participant.state != models.Participant.STATE_REQUESTED:
        messages.error(request, 'Unable to unregister from the course. Please speak to the administrator.')
    else:
        participant.delete()
        messages.success(request, 'Unregistered from %s.' % participant.course)
    return redirect('coursereg:index')

@login_required
def participant_create(request):
    assert request.method == 'POST'
    course_id = request.POST['course_id']
    user_id = request.POST['user_id']
    assert int(user_id) == int(request.user.id)

    if not course_id:
        messages.error(request, 'Select the course you want to register for.')
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
                participant_type=models.Participant.PARTICIPANT_CREDIT,
                state=models.Participant.STATE_REQUESTED,
                grade=models.Participant.GRADE_NA
            )
            messages.success(request, 'Successfully applied for %s.' % course)

    return redirect('coursereg:index')
