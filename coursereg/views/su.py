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
    offset_str = date_str.split(' ')[5][-5:]
    offset_name = str(date_str.split(' ')[5][:-5])
    naive_dt = datetime.strptime(naive_date_str, '%a %b %d %Y %H:%M:%S')
    offset = int(offset_str[-4:-2])*60 + int(offset_str[-2:])
    if offset_str[0] == "-":
        offset = -offset
    return naive_dt.replace(tzinfo=timezone.FixedOffset(offset, offset_name))


def datetime_to_str(datetime):
    return datetime.strftime('%a %b %d %Y %H:%M:%S %z (%Z)')

@login_required
def course_date_change(request, courses):
    if not request.user.is_superuser: raise PermissionDenied
    course_ids = urlunquote_plus(courses).split('-')
    if request.method == 'POST':
        models.Course.objects.filter(pk__in=course_ids).update(
            term=request.POST['term'],
            year=request.POST['year'],
            last_reg_date=parse_datetime_str(request.POST['last_reg_date']),
            last_adviser_approval_date=parse_datetime_str(request.POST['last_adviser_approval_date']),
            last_instructor_approval_date=parse_datetime_str(request.POST['last_instructor_approval_date']),
            last_conversion_date=parse_datetime_str(request.POST['last_conversion_date']),
            last_drop_date=parse_datetime_str(request.POST['last_drop_date']),
            last_drop_with_mention_date=parse_datetime_str(request.POST['last_drop_with_mention_date']),
            last_grade_date=parse_datetime_str(request.POST['last_grade_date']),
        )
        messages.success(request, "The dates of %s courses were modified successfully." % len(course_ids))
        return redirect(reverse('admin:coursereg_course_changelist'))
    else:
        return render(request, 'admin/course_date_change.html', {
            'title': 'Change course dates',
            'terms': models.Term.objects.all(),
            'courses': models.Course.objects.filter(pk__in=course_ids),
            'default_term_id': models.get_recent_term(),
            'default_year': models.get_recent_year(),
            'default_last_reg_date': datetime_to_str(models.get_recent_last_reg_date()),
            'default_last_adviser_approval_date': datetime_to_str(models.get_recent_last_adviser_approval_date()),
            'default_last_instructor_approval_date': datetime_to_str(models.get_recent_last_instructor_approval_date()),
            'default_last_conversion_date': datetime_to_str(models.get_recent_last_conversion_date()),
            'default_last_drop_date': datetime_to_str(models.get_recent_last_drop_date()),
            'default_last_drop_with_mention_date': datetime_to_str(models.get_recent_last_drop_with_mention_date()),
            'default_last_grade_date': datetime_to_str(models.get_recent_last_grade_date()),
        })

@login_required
def dept_report(request, dept_id):
    if not request.user.is_superuser: raise PermissionDenied
    dept = models.Department.objects.get(id=dept_id)
    from_date = models.get_recent_last_reg_date()
    to_date = timezone.now()
    if request.GET.get('from_date') and request.GET.get('to_date'):
        from_date = parse_datetime_str(request.GET['from_date'])
        to_date = parse_datetime_str(request.GET['to_date'])
    participants = [p for p in models.Participant.objects.filter(
        user__department=dept,
        is_adviser_approved=True,
        is_instructor_approved=True,
        user__user_type=models.User.USER_TYPE_STUDENT,
        course__last_reg_date__range=[from_date, to_date]
    ).order_by('user__degree', 'user__full_name')]
    context = {
        'title': 'Report',
        'default_from_date': datetime_to_str(from_date),
        'default_to_date': datetime_to_str(to_date),
        'participants': participants,
        'dept': dept
    }
    return render(request, 'admin/dept_report.html', context)
