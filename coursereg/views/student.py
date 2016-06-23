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

def index(request):
    if not request.user.adviser:
        messages.error(request, 'Adviser not assigned. Contact the administrator.')
        return redirect('coursereg:fatal')
    participants = [
        (
            p.course,
            p.state,
            p.grade,
            p.participant_type,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            models.Participant.PARTICIPANT_CHOICES[p.participant_type][1],
            (p.state == models.Participant.STATE_REQUESTED) or (p.state == models.Participant.STATE_ADVISOR_DONE) or (p.state == models.Participant.STATE_INSTRUCTOR_DONE) or (p.state == models.Participant.STATE_ADVISOR_REJECT) or (p.state == models.Participant.STATE_INSTRUCTOR_REJECT),
            p.id
        ) for p in models.Participant.objects.filter(user=request.user).order_by('-course__last_reg_date', 'course__title')]
    context = {
		'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now()+timedelta(days=100)),
        'remarks': request.user.dcc_remarks,
    }
    return render(request, 'coursereg/student.html', context)

@login_required
def faq(request):
	context = {
		'user_email': request.user.email,
        'faqs': models.Faq.objects.filter(faq_for=models.Faq.FAQ_STUDENT),
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
        'department': request.user.department,
        'sr_no': request.user.sr_no,
    }
    return render(request, 'coursereg/student_profile.html', context)

@login_required
def participant_delete(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    modify_value = request.POST['modify_type']
    assert participant.user_id == request.user.id
    if (participant.state == models.Participant.STATE_NA):
        messages.error(request, 'Unable to unregister from the course. Please speak to the administrator.')
    else:
        #participant.delete()
        if participant.state == models.Participant.STATE_REQUESTED and modify_value == 'cancel':
			participant.delete()
			messages.success(request, 'Cancelled registration of course %s.' % participant.course)
        elif (participant.state == models.Participant.STATE_ADVISOR_DONE or participant.state == models.Participant.STATE_INSTRUCTOR_DONE or participant.state == models.Participant.STATE_INSTRUCTOR_REJECT) and modify_value == 'cancel':
            if (participant.state == models.Participant.STATE_ADVISOR_DONE or participant.state == models.Participant.STATE_INSTRUCTOR_REJECT):
                participant.state = models.Participant.STATE_CANCEL_REQUESTED
                participant.save()
            else:
                participant.state = models.Participant.STATE_CANCEL_REQUESTED_1
                participant.save()
            messages.success(request, 'Request raised for cancelling the registration for the course %s.' % participant.course)
        elif participant.state == models.Participant.STATE_FINAL_APPROVED and modify_value == 'drop':
            participant.state = models.Participant.STATE_DROP_REQUESTED
            participant.save()
            messages.success(request, 'Request raised for dropping the course %s.' % participant.course)
        elif participant.state == models.Participant.STATE_FINAL_APPROVED and modify_value == 'audit':
            participant.state = models.Participant.STATE_AUDIT_REQUESTED
            participant.save()
            messages.success(request, 'Request raised for auditing the course %s.' % participant.course)
        elif participant.state == models.Participant.STATE_FINAL_APPROVED and modify_value == 'credit':
            participant.state = models.Participant.STATE_CREDIT_REQUESTED
            participant.save()
            messages.success(request, 'Request raised for crediting the course %s.' % participant.course)
    return redirect('coursereg:index')


@login_required
def participant_create(request):
    assert request.method == 'POST'
    course_id = request.POST['course_id']
    user_id = request.POST['user_id']
    reg_type = request.POST['reg_type']
    assert int(user_id) == int(request.user.id)

    participant_type = models.Participant.PARTICIPANT_CREDIT
    if reg_type == 'audit':
        participant_type = models.Participant.PARTICIPANT_AUDIT

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
                participant_type=participant_type,
                state=models.Participant.STATE_REQUESTED,
                grade=models.Participant.GRADE_NA
            )
            messages.success(request, 'Successfully applied for %s.' % course)

    return redirect('coursereg:index')
