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
import smtplib

def dcc(request):
    students = []
    for u in models.User.objects.filter(department=request.user.department):
        if (u.user_type==1):
            req = (
                u.id,
                u.full_name,
            )
            students.append(req)

    context = {
        'user_email': request.user.email,
        'students' : students,
    }
    return render(request, 'coursereg/dcc.html', context)

def send_remainder(request):
    smtpObj = smtplib.SMTP('www.ece.iisc.ernet.in', 25)
    dcc_email_id = 'dcc_chair@ece.iisc.ernet.in'
    outstanding_participants = []
    # Send remainder mails for all the outstanding requests pending adviser approval, notify both adviser and advisee.
    adviser_list = {}
    advisee_list = {}
    for p in models.Participant.objects.all():
        if(p.participant_type != models.Participant.PARTICIPANT_INSTRUCTOR):
            if((p.state == models.Participant.STATE_REQUESTED  or p.state ==  models.Participant.STATE_DROP_REQUESTED)):
                advisee =  p.user
                adviser = advisee.adviser
                adviser_list[adviser] = adviser.full_name
                advisee_list[advisee] = advisee.full_name             
    for adviser in adviser_list:
                mail_text =  'Subject: Bheemboy Remainder:Pending Tasks - Adviser Approval\nDear Prof. '+str(adviser.full_name)+',\n\nThere are course enrolment/drop requests from your advisees in the Bheemby portal pending your approval.\nKindly login to the Bheemboy portal and Accept/Reject these requests. \n\n\nSincerely,\nDCC Chair.'
                smtpObj.sendmail(dcc_email_id, str(adviser), mail_text)
    for advisee in advisee_list:
                mail_text =  'Subject: Bheemboy Remainder:Pending Tasks - Adviser Approval\nDear '+str(advisee.full_name)+',\n\nYour Course enrolment/drop request is pending an approval from your adviser in the Bheemby portal.\nKindly follow up with your adviser. \n\n\nSincerely,\nDCC Chair.'
                smtpObj.sendmail(dcc_email_id, str(advisee), mail_text)
    # Send remainder mails for all the outstanding requests pending instructor approval, notify both intructor and student.
    instructor_list = {}
    student_list    = {}
    for p in models.Participant.objects.all():
        if(p.participant_type != models.Participant.PARTICIPANT_INSTRUCTOR):
            if( p.state ==  models.Participant.STATE_ADVISOR_DONE ):
                curr_course          = p.course              
                student_list[p.user] = curr_course
                instructors = []
                for i in models.Participant.objects.all():
                    if(i.participant_type == models.Participant.PARTICIPANT_INSTRUCTOR and i.course == curr_course):
                        instructors.append(i.user)
                for instructor in instructors:
                    instructor_list[instructor] = curr_course
    for instructor in instructor_list:
                mail_text =  'Subject: Bheemboy Remainder:Pending Tasks - Instructor Approval\nDear Prof. '+str(instructor.full_name)+',\n\nThere are course enrolment requests from students pending your approval in the Bheemboy portal.\nKindly login to the Bheemboy portal and Accept/Reject these requests. \n\n\nSincerely,\nDCC Chair.'
                smtpObj.sendmail( dcc_email_id, str(instructor), mail_text)
    for student in student_list:
                mail_text =  'Subject: Bheemboy Remainder:Pending Tasks - Instructor Approval\nDear '+str(student.full_name)+',\n\nYour course enrolment request is pending an approval from the course instructor in the Bheemby portal.\nKindly follow up with the instructor. \n\n\nSincerely,\nDCC Chair.'
                smtpObj.sendmail( dcc_email_id, str(student), mail_text)
    return dcc(request)


def student_details_dcc(request):
    assert request.method == 'POST'
    current_student_id = request.POST['student_id']
    student = models.User.objects.get(id=current_student_id)
    student_name = student.full_name
    flag = 0
    no_course = 0
    participants = [
        (
            p.course,
            p.state,
            p.grade,
            p.course_id,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.id
        ) for p in models.Participant.objects.filter(user=current_student_id)]

    for p in participants:
        no_course = no_course + 1
        if p[4] != 'Instructor approved':
            flag = flag + 1

    context = {
	    'student_id': current_student_id,
        'student_name': student_name,
        'adviser_full_name': student.adviser.full_name,
        'program': student.program,
        'sr_no': student.sr_no,
	    'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now()+timedelta(days=100)),
        'flag': flag,
        'no_course': no_course,
    }
    return render(request, 'coursereg/student_details_dcc.html', context)

@login_required
def participant_dcc_act(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    current_student    = models.User.objects.get(id=request.POST['student_id'])
    ## Collect the course page context and pass it back to the course page
    current_course  = models.Course.objects.get(id=request.POST['course_id'])

    student_name = current_student.full_name

    assert participant.user_id == current_student.id
    if participant.state == models.Participant.STATE_INSTRUCTOR_DONE:
        participant.state = models.Participant.STATE_FINAL_APPROVED
        req_info = str(current_student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'DCC approved the request of %s.' % req_info)
    elif participant.state == models.Participant.STATE_ADV_AUDIT_DONE:
        participant.state = models.Participant.STATE_DCC_AUDIT_DONE
        req_info = str(current_student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'DCC approved the audit request of %s.' % req_info)
    elif participant.state == models.Participant.STATE_ADV_CREDIT_DONE:
        participant.state = models.Participant.STATE_DCC_CREDIT_DONE
        req_info = str(current_student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'DCC approved the credit request of %s.' % req_info)
    elif participant.state == models.Participant.STATE_ADV_DROP_DONE:
        participant.state = models.Participant.STATE_DCC_DROP_DONE
        req_info = str(current_student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'DCC approved the drop request of %s.' % req_info)
    else:
        messages.error(request, 'Unable to process request. Please contact admin')


    flag = 0
    no_course = 0

    participants = [
        (
            p.course,
            p.state,
            p.grade,
            p.course_id,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.id
        ) for p in models.Participant.objects.filter(user=current_student.id)]

    for p in participants:
        no_course = no_course + 1
        if p[4] != 'Instructor approved':
            flag = flag + 1

    context = {
        'student_id': current_student.id,
        'student_name': student_name,
        'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now() + timedelta(days=100)),
        'flag': flag,
        'no_course': no_course,
    }
    return render(request, 'coursereg/student_details_dcc.html', context)

@login_required
def participant_dcc_rej(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    current_student = models.User.objects.get(id=request.POST['student_id'])
    ## Collect the course page context and pass it back to the course page
    current_course = models.Course.objects.get(id=request.POST['course_id'])

    student_name = current_student.full_name

    assert participant.user_id == current_student.id
    if participant.state == models.Participant.STATE_INSTRUCTOR_DONE:
        participant.state = models.Participant.STATE_FINAL_DISAPPROVED
        req_info = str(current_student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.error(request, 'DCC rejected the enrolment request of %s.' % req_info)
    elif participant.state == models.Participant.STATE_ADV_AUDIT_DONE:
        participant.state = models.Participant.STATE_DCC_AUDIT_REJECT
        req_info = str(current_student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'DCC rejected the audit request of %s.' % req_info)
    elif participant.state == models.Participant.STATE_ADV_CREDIT_DONE:
        participant.state = models.Participant.STATE_DCC_CREDIT_REJECT
        req_info = str(current_student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'DCC rejected the credit request of %s.' % req_info)
    elif participant.state == models.Participant.STATE_ADV_DROP_DONE:
        participant.state = models.Participant.STATE_DCC_DROP_REJECT
        req_info = str(current_student.full_name) + ' for ' + str(participant.course)
        participant.save()
        messages.success(request, 'DCC rejected the drop request of %s.' % req_info)
    else:
        messages.error(request, 'Unable to process request. Please contact admin')
	
    flag = 0
    no_course = 0

    participants = [
        (
            p.course,
            p.state,
            p.grade,
            p.course_id,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.id
        ) for p in models.Participant.objects.filter(user=current_student.id)]

    for p in participants:
        no_course = no_course + 1
        if p[4] != 'Instructor approved':
            flag = flag + 1

    context = {
        'student_id': current_student.id,
        'student_name': student_name,
        'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now() + timedelta(days=100)),
        'flag': flag,
        'no_course': no_course,
    }
    return render(request, 'coursereg/student_details_dcc.html', context)

@login_required
def participant_dcc_act_all(request):
    assert request.method == 'POST'
    current_student = models.User.objects.get(id=request.POST['student_id'])
    ## Collect the course page context and pass it back to the course page
    participant = models.Participant.objects.filter(user_id=current_student.id)
    student_name = current_student.full_name

    flag = 1
    no_course = 0

    for p in participant:
        if p.state != models.Participant.STATE_INSTRUCTOR_DONE:
            messages.error(request, 'Unable to accept the enrolment request, please contact the admin.')
        else:
            p.state = models.Participant.STATE_FINAL_APPROVED
            req_info = str(student_name) + ' for ' + str(p.course)
            p.save()
            messages.success(request, 'Instructor Accepted the enrolment request of %s.' % req_info)

    participants = [
        (
            p.course,
            p.state,
            p.grade,
            p.course_id,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.id
        ) for p in models.Participant.objects.filter(user_id=current_student.id)]

    context = {
        'student_id': current_student.id,
        'student_name': student_name,
        'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now() + timedelta(days=100)),
        'flag': flag,
        'no_course': no_course,
    }
    return render(request, 'coursereg/student_details_dcc.html', context)

@login_required
def faq(request):
        context = {
            'user_email': request.user.email,
            'faqs': models.Faq.objects.filter(faq_for=models.Faq.FAQ_DCC),
        }
        return render(request, 'coursereg/dcc_faq.html', context)
