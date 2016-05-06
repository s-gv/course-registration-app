from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from . import models

def student(request):
    participants = [
        (
            p.course,
            models.Participant.STATE_CHOICES[p.state][1],
            models.Participant.GRADE_CHOICES[p.grade][1],
        ) for p in models.Participant.objects.filter(user=request.user)]
    context = {
        'user_full_name': request.user.full_name,
        'user_id': request.user.id,
        'adviser_full_name': request.user.adviser.full_name,
        'program': models.User.PROGRAM_CHOICES[request.user.program][1],
        'sr_no': request.user.sr_no,
        'participants': participants,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now()),
    }
    return render(request, 'coursereg/student.html', context)

@login_required
def participant_create(request):
    assert request.method == 'POST'
    course_id = request.POST['course_id']
    user_id = request.POST['user_id']
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

@login_required
def index(request):
    if request.user.user_type == models.User.USER_TYPE_STUDENT:
        return student(request)
    elif request.user.user_type == models.User.USER_TYPE_FACULTY:
        return HttpResponse("Logged in. TODO: Faculty view.")
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
