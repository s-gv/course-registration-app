from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from . import models

@login_required
def index(request):
    if request.user.user_type == models.User.USER_TYPE_STUDENT:
        context = {
            'user_full_name': request.user.full_name,
            'adviser_full_name': request.user.adviser.full_name,
            'program': models.User.PROGRAM_CHOICES[request.user.program][1],
            'sr_no': request.user.sr_no,
        }
        return render(request, 'coursereg/student.html', context)
    else:
        return HttpResponse("Logged in.")

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
