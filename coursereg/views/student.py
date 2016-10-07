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
from django.core.exceptions import PermissionDenied
from coursereg import utils

@login_required
def index(request):
    if not request.user.user_type == models.User.USER_TYPE_STUDENT: raise PermissionDenied
    if not request.user.adviser:
        messages.error(request, 'Adviser not assigned.')
        return redirect('coursereg:fatal')

    context = {
        'user_type': 'student',
        'nav_active': 'home',
		'user_email': request.user.email,
        'reg_types': models.RegistrationType.objects.filter(is_active=True),
        'user_id': request.user.id,
        'participants': models.Participant.objects.filter(user=request.user).order_by('-course__term__last_reg_date', 'course__title'),
        'notifications': [(n.created_at, models.Notification.ORIGIN_CHOICES[n.origin][1], n.message)
            for n in models.Notification.objects.filter(user=request.user, is_student_acknowledged=False).order_by('-created_at')],
        'courses': models.Course.objects.filter(term__last_reg_date__gte=timezone.now(),
                                                term__last_reg_date__lte=timezone.now()+
                                                    timedelta(days=models.Config.num_days_before_last_reg_date_course_registerable()))
    }
    return render(request, 'coursereg/student.html', context)
