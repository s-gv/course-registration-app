from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

@login_required
def index(request):
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
    return HttpResponse("Logged out")
