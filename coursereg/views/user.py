from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from django.core.exceptions import PermissionDenied

def signin(request):
    if request.method == 'GET':
        context = { "next_url": request.GET.get('next', reverse('coursereg:index'))}
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

def forgot_passwd(request):
    if request.method == 'GET':
        return render(request, 'coursereg/forgotpass.html')
    else:
        user = models.User.objects.filter(email=request.POST['email']).first()
        if user:
            messages.success(request, 'Password recovery email sent.')
            return password_reset(request,
                template_name='coursereg/forgotpass.html',
                email_template_name='coursereg/forgotpass_email_body.html',
                subject_template_name='coursereg/forgotpass_email_subject.txt',
                post_reset_redirect=reverse('coursereg:signin')
            )
        else:
            messages.error(request, 'Unknown user.')
            return redirect(reverse('coursereg:forgot_passwd'))

def reset_passwd(request, uidb64=None, token=None):
    response = password_reset_confirm(request,
        uidb64=uidb64, token=token,
        template_name='coursereg/resetpass.html',
        post_reset_redirect=reverse('coursereg:signin')
    )
    if type(response) == HttpResponseRedirect:
        messages.success(request, 'Password changed.')
    return response

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

@login_required
def sudo_login(request, user_id):
    if not request.user.is_superuser: raise PermissionDenied
    user = models.User.objects.get(id=user_id)
    user.backend = settings.AUTHENTICATION_BACKENDS[0]
    login(request, user)
    return redirect(reverse('coursereg:index'))
