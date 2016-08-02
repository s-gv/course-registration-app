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

def get_desc(participant):
    if participant.is_drop:
        return 'Dropped this course'
    if not participant.is_adviser_approved:
        return 'Awaiting adviser review'
    if not participant.is_instructor_approved:
        return 'Adviser has approved. Awaiting instructor review'
    if participant.grade.id == models.get_default_grade():
        return 'Registered'
    else:
        return participant.grade
    return 'Unknown state'

@login_required
def index(request):
    if not request.user.user_type == models.User.USER_TYPE_STUDENT: raise PermissionDenied
    if not request.user.adviser:
        messages.error(request, 'Adviser not assigned.')
        return redirect('coursereg:fatal')

    participants = [(
        p.id,
        p.is_credit,
        not p.is_credit,
        p.is_drop,
        p.course, get_desc(p),
        not p.is_adviser_approved
    ) for p in models.Participant.objects.filter(user=request.user).order_by('-course__last_reg_date', 'course__title')]

    context = {
        'user_type': 'student',
        'nav_active': 'home',
		'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': participants,
        'notifications': [(n.created_at, models.Notification.ORIGIN_CHOICES[n.origin][1], n.message)
            for n in models.Notification.objects.filter(user=request.user, is_student_acknowledged=False).order_by('-created_at')],
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now()+timedelta(days=100))
    }
    return render(request, 'coursereg/student.html', context)
