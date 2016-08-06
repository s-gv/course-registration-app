from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
from coursereg import models
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import PermissionDenied
from django.utils.http import urlquote_plus, urlunquote_plus

def parse_datetime_str(date_str):
    naive_date_str = ' '.join(date_str.split(' ')[:5])
    offset_str = date_str.split(' ')[5][3:]
    print offset_str
    naive_dt = datetime.strptime(naive_date_str, '%a %b %d %Y %H:%M:%S')
    offset = int(offset_str[-4:-2])*60 + int(offset_str[-2:])
    if offset_str[0] == "-":
        offset = -offset
    return naive_dt.replace(tzinfo=timezone.FixedOffset(offset))

@login_required
def course_date_change(request, courses):
    if not request.user.is_superuser: raise PermissionDenied
    if request.method == 'POST':
        course_ids = urlunquote_plus(courses).split(',')
        models.Course.objects.filter(pk__in=course_ids).update(
            term=request.POST['term'],
            year=request.POST['year'],
            last_reg_date=parse_datetime_str(request.POST['last_reg_date']),
            last_conversion_date=parse_datetime_str(request.POST['last_conversion_date']),
            last_drop_date=parse_datetime_str(request.POST['last_drop_date']),
            last_drop_with_mention_date=parse_datetime_str(request.POST['last_drop_with_mention_date']),
            last_grade_date=parse_datetime_str(request.POST['last_grade_date']),
        )
        messages.success(request, "The dates of %s courses were modified successfully." % len(course_ids))
        return redirect(reverse('admin:coursereg_course_changelist'))
    else:
        course_ids = urlunquote_plus(courses).split(',')
        return render(request, 'admin/course_date_change.html', {
            'title': 'Change course dates',
            'terms': models.Term.objects.all(),
            'courses': models.Course.objects.filter(pk__in=course_ids),
            'default_term_id': models.get_recent_term(),
            'default_year': models.get_recent_year(),
            'default_last_reg_date': models.get_recent_last_reg_date().strftime('%a %b %d %Y %H:%M:%S %z (%Z)'),
            'default_last_conversion_date': models.get_recent_last_conversion_date().strftime('%a %b %d %Y %H:%M:%S %z (%Z)'),
            'default_last_drop_date': models.get_recent_last_drop_date().strftime('%a %b %d %Y %H:%M:%S %z (%Z)'),
            'default_last_drop_with_mention_date': models.get_recent_last_drop_with_mention_date().strftime('%a %b %d %Y %H:%M:%S %z (%Z)'),
            'default_last_grade_date': models.get_recent_last_grade_date().strftime('%a %b %d %Y %H:%M:%S %z (%Z)'),
        })
