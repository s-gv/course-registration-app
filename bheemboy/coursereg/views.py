from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from . import models
import ast # Added by Arthi

#Added by Arthi
def admin(request):
	participants = [
        (
            p.course,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.state == models.Participant.STATE_REQUESTED,
            p.id
        ) for p in models.Participant.objects.filter(user=request.user)]
	context = {
        'user_full_name': request.user.full_name,
        'user_id': request.user.id,
        'adviser_full_name': 'nil',
        'program': 'models.User.PROGRAM_CHOICES[request.user.program][1]',
        'sr_no': 1,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now()),
    	}
	return render(request, 'coursereg/admin.html', context)

def student(request):
    participants = [
        (
            p.course,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
            p.state == models.Participant.STATE_REQUESTED,
            p.id
        ) for p in models.Participant.objects.filter(user=request.user)]
    context = {
        'user_full_name': request.user.full_name,
        'user_id': request.user.id,
        'adviser_full_name': request.user.adviser.full_name,
        'program': models.User.PROGRAM_CHOICES[request.user.program][1],
        'sr_no': request.user.sr_no,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now()+timedelta(days=100)),
    }
    return render(request, 'coursereg/student.html', context)

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
                p.state == models.Participant.STATE_REQUESTED,
                p.id
            ) for p in models.Participant.objects.filter(user=advisee[0])]
        advisee_requests = advisee_requests + advisee_reqs
    context = {
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
        if( ( p.participant_type == 0 or  p.participant_type == 1) and p.state == models.Participant.STATE_ADVISOR_DONE) :
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



@login_required
def participant_advisor_act(request):
    assert request.method == 'POST'
    participant = models.Participant.objects.get(id=request.POST['participant_id'])
    advisee     = models.User.objects.get(id=request.POST['advisee_id'])
    assert participant.user_id == advisee.id
    if participant.state != models.Participant.STATE_REQUESTED:
        messages.error(request, 'Unable Accept the enrolment request, please contact the admin.')
    else:
        participant.state = models.Participant.STATE_ADVISOR_DONE
        participant.save()
        req_info = str(advisee.full_name) + ' for ' + str(participant.course)
        messages.success(request, 'Accepted the enrolment request of %s.' % req_info)
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
    for p in models.Participant.objects.filter(course=current_course):
        if( ( p.participant_type == 0 or  p.participant_type == 1) and p.state == models.Participant.STATE_ADVISOR_DONE) :
                req = (p.user.id,
                    p.user.full_name,
                    p.user.program,
                    models.Participant.STATE_CHOICES[p.state][1],
                    models.Participant.GRADE_CHOICES[p.grade][1],
                    p.state == models.Participant.STATE_ADVISOR_DONE,
                    p.id)
                students.append(req)

    context = {
        'course_id': current_course.id,
        'course_name': current_course,
        'course_credits': current_course.credits,
        'students': students,
    }
    return render(request, 'coursereg/course.html', context)

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

#Added by Arthi
@login_required
def adduser(request):

    assert request.method == 'POST'
    full_name = request.POST['full_name']
    password = request.POST['password']
    email = request.POST['email']
    is_superuser_text = request.POST['is_superuser']
    is_superuser = ast.literal_eval(is_superuser_text)
    user_type = request.POST['user_type']
    program = request.POST['program']
    date_joined = request.POST['date_joined']
    sr_no = request.POST['sr_no']
    adviser_id = request.POST['adviser_id']
    is_staff_text = request.POST['is_staff']
    is_staff = ast.literal_eval(is_staff_text)
    is_active_text = request.POST['is_active']
    is_active = ast.literal_eval(is_active_text)
    user_id = request.POST['user_id']
    if models.User.objects.filter(user__id=user_id):
        messages.error(request, 'Already registered for %s.' % course)
    else:
	models.User.objects.create(
		full_name = full_name,
		password = password,
		email = email,
		is_superuser = is_superuser,
		user_type = user_type,
		program = program,
		date_joined = date_joined,
		sr_no = sr_no,
		is_staff = is_staff,
		adviser_id = adviser_id,
		is_active = is_active,
	)
	#messages.success(request, 'Successfully applied for %s.' % course)
    return redirect('coursereg:index')

@login_required
def index(request):
    if request.user.user_type == models.User.USER_TYPE_STUDENT:
        return student(request)
    elif request.user.user_type == models.User.USER_TYPE_FACULTY:
        return faculty(request)
        #return HttpResponse("Logged in. TODO: Faculty view.")
    elif request.user.user_type == 2:
        return admin(request)
    else:
        return HttpResponse("Logged in. Nothing to show because you are neither student nor faculty.")

def signin(request):
    if request.method == 'GET':
        context = {'signin_url': request.get_full_path()}
        return render(request, 'coursereg/signin.html', context)
    else:
        user = authenticate(email=request.POST['email'], password=request.POST['password'])
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', reverse('coursereg:index')))
        else:
            messages.error(request, 'E-mail or password is incorrect.')
            return redirect(request.get_full_path())


def signout(request):
    logout(request)
    return redirect(reverse('coursereg:index'))
