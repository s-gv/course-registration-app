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

def faculty(request):
    participants = [
        (
            p.course,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.state == models.Participant.STATE_REQUESTED,
            p.id
        ) for p in models.Participant.objects.filter(user=request.user)]

    advisees = [
        (
            u.id,
            u.full_name,
        ) for u in models.User.objects.filter(adviser=request.user)]
    print advisees

    advisee_requests = []
    for advisee in advisees:
        advisee_reqs = [
            (
                advisee[0],
                advisee[1],
                p.course,
                models.Participant.STATE_CHOICES[p.state][1],
                ##models.Participant.GRADE_CHOICES[p.grade][1],
                p.participant_type,
                (p.state == models.Participant.STATE_REQUESTED) or (p.state == models.Participant.STATE_DROP_REQUESTED),
                p.id
            ) for p in models.Participant.objects.filter(user=advisee[0])]
        advisee_requests = advisee_requests + advisee_reqs
    context = {
	'user_email': request.user.email,
        'user_full_name': request.user.full_name,
        'user_id': request.user.id,
        'sr_no': request.user.sr_no,
        'participants': participants,
        'advisees' : advisees,
        'advisee_requests' : advisee_requests,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now()),
    }
    return render(request, 'coursereg/faculty.html', context)


def course_page(request):
    assert request.method == 'POST'
    current_course = models.Course.objects.get(id=request.POST['course_id'])
    students = []
    instructors = []
    TAs = []

    for p in models.Participant.objects.filter(course=current_course):
        if( ( p.participant_type == 0 or  p.participant_type == 1) and p.state != models.Participant.STATE_REQUESTED) :
                req = (p.user.id,
                    p.user.full_name,
                    p.user.program,
                    models.Participant.STATE_CHOICES[p.state][1],
                    models.Participant.GRADE_CHOICES[p.grade][1],
                    p.state == models.Participant.STATE_ADVISOR_DONE,
                    p.id)
                students.append(req)
        if( ( p.participant_type == 2) ):
                req = (p.user.id,
                    p.user.full_name,
                    p.id)
                instructors.append(req)
        if( ( p.participant_type == 3) ):
                req = (p.user.id,
                    p.user.full_name,
                    p.id)
                TAs.append(req)


    context = {
        'course_id': current_course.id,
        'course_name': current_course,
        'course_credits': current_course.credits,
        'students': students,
        'instructors': instructors,
        'TAs': TAs,
    }
    return render(request, 'coursereg/course.html', context)

def student_details(request):
    assert request.method == 'POST'
    current_student_id = request.POST['student_id']
    participants = [
        (
            p.course,
            p.state,
            p.grade,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.state == models.Participant.STATE_REQUESTED,
            p.id
        ) for p in models.Participant.objects.filter(user=current_student_id)]
    context = {
        'student_name': models.User.objects.filter(pk=current_student_id),   
	    'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now()+timedelta(days=100)),
    }
    return render(request, 'coursereg/student_details.html', context)

@login_required
def participant_advisor_act(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    advisee     = models.User.objects.get(id=request.POST['advisee_id'])
    assert participant.user_id == advisee.id
    if (participant.state != models.Participant.STATE_REQUESTED) and (participant.state != models.Participant.STATE_DROP_REQUESTED):
        messages.error(request, 'Unable Accept the enrolment request, please contact the admin.')
    elif (participant.state == models.Participant.STATE_REQUESTED):
		participant.state = models.Participant.STATE_ADVISOR_DONE
		participant.save()
		req_info = str(advisee.full_name) + ' for ' + str(participant.course)
		messages.success(request, 'Accepted the enrolment request of %s.' % req_info)
    else:
		participant.state = models.Participant.STATE_ADV_DROP_DONE
		participant.save()
		req_info = str(advisee.full_name) + ' for ' + str(participant.course)
		messages.success(request, 'Dropped the enrolment request of %s.' % req_info)
    return redirect('coursereg:index')

@login_required
def participant_advisor_rej(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    advisee     = models.User.objects.get(id=request.POST['advisee_id'])
    assert participant.user_id == advisee.id
    if (participant.state != models.Participant.STATE_REQUESTED) and (participant.state != models.Participant.STATE_DROP_REQUESTED):
        messages.error(request, 'Unable Accept the enrolment request, please contact the admin.')
    elif (participant.state == models.Participant.STATE_REQUESTED):
		participant.state = models.Participant.STATE_ADVISOR_REJECT
		participant.save()
		req_info = str(advisee.full_name) + ' for ' + str(participant.course)
		messages.success(request, 'Rejected the enrolment request of %s.' % req_info)
		#participant.delete()
    else:
		participant.state = models.Participant.STATE_ADV_DROP_REJECT
		participant.save()
		req_info = str(advisee.full_name) + ' for ' + str(participant.course)
		messages.success(request, 'Rejected the drop request of %s.' % req_info)
    return redirect('coursereg:index')


@login_required
def participant_instr_act(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    student     = models.User.objects.get(id=request.POST['student_id'])
    ## Collect the course page context and pass it back to the course page
    current_course     = models.Course.objects.get(id=request.POST['course_id'])

    assert participant.user_id == student.id
    if participant.state != models.Participant.STATE_ADVISOR_DONE:
        messages.error(request, 'Unable Accept the enrolment request, please contact the admin.')
    else:
        participant.state = models.Participant.STATE_INSTRUCTOR_DONE
        req_info = str(student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'Instructor Accepted the enrolment request of %s.' % req_info)

    ## Read the DB and re-render the course page.
    students = []
    instructors = []
    TAs = []
    for p in models.Participant.objects.filter(course=current_course):
        if( ( p.participant_type == 0 or  p.participant_type == 1) and p.state != models.Participant.STATE_REQUESTED) :
                req = (p.user.id,
                    p.user.full_name,
                    p.user.program,
                    models.Participant.STATE_CHOICES[p.state][1],
                    models.Participant.GRADE_CHOICES[p.grade][1],
                    p.state == models.Participant.STATE_ADVISOR_DONE,
                    p.id)
                students.append(req)
        if ((p.participant_type == 2)):
            req = (p.user.id,
                   p.user.full_name,
                   p.id)
            instructors.append(req)
        if ((p.participant_type == 3)):
            req = (p.user.id,
                   p.user.full_name,
                   p.id)
            TAs.append(req)

    context = {
        'course_id': current_course.id,
        'course_name': current_course,
        'course_credits': current_course.credits,
        'students': students,
        'instructors': instructors,
        'TAs': TAs,
    }

    return render(request, 'coursereg/course.html', context)

@login_required
def participant_instr_rej(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    student     = models.User.objects.get(id=request.POST['student_id'])
    ## Collect the course page context and pass it back to the course page
    current_course     = models.Course.objects.get(id=request.POST['course_id'])

    assert participant.user_id == student.id
    if participant.state != models.Participant.STATE_ADVISOR_DONE:
        messages.error(request, 'Unable Accept the enrolment request, please contact the admin.')
    else:
        participant.state = models.Participant.STATE_INSTRUCTOR_REJECT
        req_info = str(student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'Instructor Rejected the enrolment request of %s.' % req_info)

    ## Read the DB and re-render the course page.
    students = []
    instructors = []
    TAs = []
    for p in models.Participant.objects.filter(course=current_course):
        if( ( p.participant_type == 0 or  p.participant_type == 1) and p.state != models.Participant.STATE_REQUESTED ) :
                req = (p.user.id,
                    p.user.full_name,
                    p.user.program,
                    models.Participant.STATE_CHOICES[p.state][1],
                    models.Participant.GRADE_CHOICES[p.grade][1],
                    p.state == models.Participant.STATE_ADVISOR_DONE,
                    p.id)
                students.append(req)
        if ((p.participant_type == 2)):
            req = (p.user.id,
                   p.user.full_name,
                   p.id)
            instructors.append(req)
        if ((p.participant_type == 3)):
            req = (p.user.id,
                   p.user.full_name,
                   p.id)
            TAs.append(req)

    context = {
        'course_id': current_course.id,
        'course_name': current_course,
        'course_credits': current_course.credits,
        'students': students,
        'instructors': instructors,
        'TAs': TAs,
    }

    return render(request, 'coursereg/course.html', context)


@login_required
def faq(request):
        context = {
                'user_email': request.user.email,
        'faqs': models.Faq.objects.filter(faq_for=models.Faq.FAQ_FACULTY),
        }
        return render(request, 'coursereg/faculty_faq.html', context)

