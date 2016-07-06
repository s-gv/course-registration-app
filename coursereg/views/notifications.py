from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models
import maillib

@login_required
def dismiss(request):
    assert request.method == 'POST'
    user = models.User.objects.get(id=request.POST['id'])
    assert user is not None
    if request.user.user_type == models.User.USER_TYPE_STUDENT:
        assert user == request.user
        models.Notification.objects.filter(user=user).update(is_student_acknowledged=True)
    if request.user.user_type == models.User.USER_TYPE_DCC:
        assert user.department == request.user.department
        models.Notification.objects.filter(user=user).update(is_dcc_acknowledged=True)
    elif request.user.user_type == models.User.USER_TYPE_FACULTY:
        assert user.adviser == request.user
        models.Notification.objects.filter(user=user).update(is_adviser_acknowledged=True)
    return redirect(request.POST.get('next', reverse('coursereg:index')))

@login_required
def notify(request):
    assert request.method == 'POST'
    assert request.user.user_type == models.User.USER_TYPE_DCC
    user = models.User.objects.get(id=request.POST['id'])
    assert user is not None
    assert user.department == request.user.department
    user.is_dcc_review_pending = True
    user.save()
    models.Notification.objects.create(
        user=user,
        origin=models.Notification.ORIGIN_DCC,
        message=request.POST['message'],
    )
    if not maillib.send_email(request.user.email, [user.email, user.adviser.email], 'Coursereg notification', request.POST['message']):
        messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
    else:
        messages.success(request, '%s has been notified.' % user.full_name)
    return redirect(request.POST.get('next', reverse('coursereg:index')))
