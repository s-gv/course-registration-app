from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from coursereg import models

@login_required
def dismiss(request):
    if request.user.user_type == models.User.USER_TYPE_STUDENT:
        models.Notification.objects.filter(user=request.user).update(is_student_acknowledged=True)
    return redirect(request.GET.get('next', reverse('coursereg:index')))
