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

def signin(request):
    if request.method == 'GET':
        context = {'signin_url': request.get_full_path()}
        return render(request, 'coursereg/signin.html', context)
    else:
        user = authenticate(email=request.POST['email'], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(request.GET.get('next', reverse('coursereg:index')))
            else:
                messages.error(request, 'Account inactive.')
        else:
            messages.error(request, 'E-mail or password is incorrect.')
        return redirect(request.get_full_path())

def signout(request):
    logout(request)
    return redirect(reverse('coursereg:index'))

@login_required
def change_passwd(request):
	if request.method == 'POST':
		newpass = request.POST['newpasswd']
		u = request.user
		if authenticate(email=u.email, password=request.POST['passwd']):
			if newpass == request.POST['newpasswd2']:
				if len(newpass) >= 8:
					u.set_password(newpass)
					u.save()
					update_session_auth_hash(request, u)
					messages.success(request, 'Password changed successfully.')
				else:
					messages.error(request, 'New password must have at least 8 characters.')
			else:
				messages.error(request, 'New password does not match. Your new password must be confirmed by entering it twice.')
		else:
			messages.error(request, 'Current password is incorrect.')
		return redirect(request.POST.get('next', reverse('coursereg:index')))
