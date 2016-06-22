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
    active_students = []

    for u in models.User.objects.filter(department=request.user.department):
        if (u.user_type==1):
            req = (
                u.full_name,
                u.id,
                u.email,
            )
            students.append(req)


    dcc_action = 0

    for u in students:
        participants = [
            (
                p.course,
                p.state,
                p.grade,
                p.course_id,
                models.Participant.STATE_CHOICES[p.state][1],
                models.Participant.GRADE_CHOICES[p.grade][1],
                p.id
            ) for p in models.Participant.objects.filter(user=u[1])]

        for p in participants:
            if (p[4] == 'Instructor approved') or (p[4] == 'Advisor approved drop'):
                dcc_action = 1

        if dcc_action == 1 :
            active_students.append(u)

        dcc_action = 0

    active_students.sort()

    context = {
        'user_email': request.user.email,
        'active_students' : active_students,
    }
    return render(request, 'coursereg/dcc.html', context)

def dcc_approved(request):
    students = []
    notactive_students = []

    for u in models.User.objects.filter(department=request.user.department):
        if (u.user_type==1):
            req = (
                u.full_name,
                u.id,
                u.email,
            )
            students.append(req)


    dcc_action = 0

    for u in students:
        participants = [
            (
                p.course,
                p.state,
                p.grade,
                p.course_id,
                models.Participant.STATE_CHOICES[p.state][1],
                models.Participant.GRADE_CHOICES[p.grade][1],
                p.id
            ) for p in models.Participant.objects.filter(user=u[1])]

        for p in participants:
            if (p[4] == 'Instructor approved') or (p[4] == 'Advisor approved drop'):
                dcc_action = 1

        if dcc_action == 0 :
            notactive_students.append(u)

        dcc_action = 0

    notactive_students.sort()

    context = {
        'user_email': request.user.email,
        'not_active_students': notactive_students,
    }
    return render(request, 'coursereg/dcc_approved.html', context)

def send_remainder(request):
    try:
        smtpObj = smtplib.SMTP('www.ece.iisc.ernet.in', 25)
        dcc_email_id = 'dcc@ece.iisc.ernet.in'
    except:
        messages.error(request, 'Unable to connect to the  e-mail server. Cannot send remainder emails. Please fix connectivity issues')
        return dcc(request)
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
    failed_recipients = []               
    for adviser in adviser_list:
                mail_text =  'Subject: Course Registration Remainder:Pending Tasks - Adviser Approval\nDear Prof. '+str(adviser.full_name)+',\n\nThere are course enrolment/drop requests from your advisees in the Course Registration portal pending your approval.\nKindly login to the Course Registration portal and Accept/Reject these requests. \n\n\nSincerely,\nDCC Chair.'
                try:
                    smtpObj.sendmail(dcc_email_id, str(adviser), mail_text)                
                except:
                    failed_recipients.append(str(adviser))
    for advisee in advisee_list:
                mail_text =  'Subject: Course Registration Remainder:Pending Tasks - Adviser Approval\nDear '+str(advisee.full_name)+',\n\nYour Course enrolment/drop request is pending an approval from your adviser in the Course Registration portal.\nKindly follow up with your adviser. \n\n\nSincerely,\nDCC Chair.'
                try:
                    smtpObj.sendmail(dcc_email_id, str(advisee), mail_text)
                except:
                    failed_recipients.append(str(advisee))
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
                mail_text =  'Subject: Course Registration Remainder:Pending Tasks - Instructor Approval\nDear Prof. '+str(instructor.full_name)+',\n\nThere are course enrolment requests from students pending your approval in the Course Registration portal.\nKindly login to the Course Registration portal and Accept/Reject these requests. \n\n\nSincerely,\nDCC Chair.'
                try:
                    smtpObj.sendmail( dcc_email_id, str(instructor), mail_text)
                except:
                    failed_recipients.append(str(instructor))                    
    for student in student_list:
                mail_text =  'Subject: Course Registration Remainder:Pending Tasks - Instructor Approval\nDear '+str(student.full_name)+',\n\nYour course enrolment request is pending an approval from the course instructor in the Course Registration portal.\nKindly follow up with the instructor. \n\n\nSincerely,\nDCC Chair.'
                try:
                    smtpObj.sendmail( dcc_email_id, str(student), mail_text)
                except:
                    failed_recipients.append(str(student))                    
    if (len(failed_recipients) > 0):
        error_str = 'Email alerts to the following IDs could not be sent : ' +  str(failed_recipients)
        messages.error(request, error_str )

    return dcc(request)


def student_details_dcc(request):
    assert request.method == 'GET'
    current_student_id = request.GET['student_id']
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
        if (p[4] != 'Instructor approved' and p[4] != 'Instructor rejected'):
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
        'remarks': student.dcc_remarks,
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
        if p.state == models.Participant.STATE_INSTRUCTOR_DONE:
            p.state = models.Participant.STATE_FINAL_APPROVED
            req_info = str(student_name) + ' for ' + str(p.course)
            p.save()
            messages.success(request, 'DCC Accepted the enrolment request of %s.' % req_info)

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

    current_student.dcc_remarks = ''
    current_student.save()

    context = {
        'student_id': current_student.id,
        'student_name': student_name,
        'adviser_full_name': current_student.adviser.full_name,
        'program': current_student.program,
        'sr_no': current_student.sr_no,
        'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now() + timedelta(days=100)),
        'flag': flag,
        'no_course': no_course,
        'remarks': current_student.dcc_remarks
    }
    return render(request, 'coursereg/student_details_dcc.html', context)

@login_required
def participant_meet_dcc(request):
    assert request.method == 'POST'
    current_student = models.User.objects.get(id=request.POST['student_id'])
    ## Collect the course page context and pass it back to the course page
    participant = models.Participant.objects.filter(user_id=current_student.id)
    student_name = current_student.full_name

    flag = 0
    no_course = 1

    remarks = request.POST['myTextBox']
    current_student.dcc_remarks = remarks
    current_student.save()

    try:
        smtpObj = smtplib.SMTP('www.ece.iisc.ernet.in', 25)
        dcc_email_id = 'dcc@ece.iisc.ernet.in'
        mail_text =  'Subject: Course Registration Update:Meet DCC for Approval\nDear '+str(current_student.full_name)+',\n\nYour course plan for this term is pending an approval from the DCC.\n Kindly meet the DCC for follow up.\n\n DCC Remarks:\n'+str(remarks)+'\n\n\nSincerely,\nDCC Chair.'
        smtpObj.sendmail( dcc_email_id, str(current_student), mail_text)
    except:
        messages.error(request, 'Unable to send e-mail. But the remarks will be visible on this website.')


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
        'adviser_full_name': current_student.adviser.full_name,
        'program': current_student.program,
        'sr_no': current_student.sr_no,
        'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now() + timedelta(days=100)),
        'flag': flag,
        'no_course': no_course,
        'remarks': current_student.dcc_remarks
    }
    return render(request, 'coursereg/student_details_dcc.html', context)

@login_required
def faq(request):
        context = {
            'user_email': request.user.email,
            'faqs': models.Faq.objects.filter(faq_for=models.Faq.FAQ_DCC),
        }
        return render(request, 'coursereg/dcc_faq.html', context)

@login_required
def profile(request):
    context = {
		'user_email': request.user.email,
        'user_full_name': request.user.full_name,
        'user_id': request.user.id,
        'department': request.user.department,
    }
    return render(request, 'coursereg/dcc_profile.html', context)
