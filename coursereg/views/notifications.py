from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import timedelta
from coursereg import models
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

@require_POST
@login_required
def dismiss(request):
    user = models.User.objects.get(id=request.POST['id'])
    if not user: raise PermissionDenied
    if request.user.user_type == models.User.USER_TYPE_STUDENT:
        if not user == request.user: raise PermissionDenied
        models.Notification.objects.filter(user=user).update(is_student_acknowledged=True)
    if request.user.user_type == models.User.USER_TYPE_DCC:
        if not user.department == request.user.department: raise PermissionDenied
        models.Notification.objects.filter(user=user).update(is_dcc_acknowledged=True)
    elif request.user.user_type == models.User.USER_TYPE_FACULTY:
        if not user.adviser == request.user: raise PermissionDenied
        models.Notification.objects.filter(user=user).update(is_adviser_acknowledged=True)
    return redirect(request.POST.get('next', reverse('coursereg:index')))

@require_POST
@login_required
def notify(request):
    if not request.user.user_type == models.User.USER_TYPE_DCC:
        raise PermissionDenied
    user = models.User.objects.get(id=request.POST['id'])
    if not user or user.department != request.user.department:
        raise PermissionDenied
    user.is_dcc_review_pending = True
    user.is_dcc_sent_notification = True
    user.save()
    models.Notification.objects.create(
        user=user,
        origin=models.Notification.ORIGIN_DCC,
        message=request.POST['message'],
    )
    try:
        send_mail('Coursereg notification', request.POST['message'], settings.DEFAULT_FROM_EMAIL, [user.email, user.adviser.email])
    except:
        messages.warning(request, 'Error sending e-mail. But a notification has been created on this website.')
    return redirect(request.POST.get('next', reverse('coursereg:index')))
