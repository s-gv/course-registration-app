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
import ast

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
