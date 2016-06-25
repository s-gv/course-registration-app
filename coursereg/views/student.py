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

def index(request):
    if not request.user.adviser:
        messages.error(request, 'Adviser not assigned. Contact the administrator.')
        return redirect('coursereg:fatal')

    context = {
        'user_type': 'student',
        'nav_active': 'home',
		'user_email': request.user.email,
        'user_id': request.user.id,
        'participants': None,
        'courses': models.Course.objects.filter(last_reg_date__gte=timezone.now(),
                                                last_reg_date__lte=timezone.now()+timedelta(days=100)),
        'remarks': request.user.dcc_remarks,
    }
    return render(request, 'coursereg/student.html', context)
