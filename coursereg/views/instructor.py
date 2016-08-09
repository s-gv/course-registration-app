from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import date, timedelta
from django.utils import timezone
from coursereg import models
from django.core.exceptions import PermissionDenied
import re

@login_required
def index(request):
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    context = {
        'user_type': 'faculty',
        'nav_active': 'instructor',
        'user_email': request.user.email,
        'can_faculty_create_courses': models.Config.can_faculty_create_courses(),
        'courses': [p.course for p in models.Participant.objects.filter(user=request.user).order_by('-course__last_reg_date')]
    }
    return render(request, 'coursereg/instructor.html', context)

@login_required
def detail(request, course_id):
    course = models.Course.objects.get(id=course_id)
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    if not models.Participant.objects.filter(course=course,
            user=request.user, participant_type=models.Participant.PARTICIPANT_INSTRUCTOR):
        raise PermissionDenied
    reg_requests = [
        (p.is_credit, p.id, p.user)
        for p in models.Participant.objects.filter(course=course,
                                                   is_adviser_approved=True,
                                                   is_instructor_approved=False)]
    crediting = models.Participant.objects.filter(course=course,
                                                  is_credit=True,
                                                  is_drop=False,
                                                  is_adviser_approved=True,
                                                  is_instructor_approved=True)
    auditing = models.Participant.objects.filter(course=course,
                                                 is_credit=False,
                                                 is_drop=False,
                                                 is_adviser_approved=True,
                                                 is_instructor_approved=True)
    dropped = models.Participant.objects.filter(course=course,
                                                is_drop=True,
                                                is_adviser_approved=True,
                                                is_instructor_approved=True)

    context = {
        'user_type': 'faculty',
        'nav_active': 'instructor',
        'user_email': request.user.email,
        'course': course,
        'can_faculty_create_courses': models.Config.can_faculty_create_courses(),
        'registration_requests': reg_requests,
        'crediting': crediting,
        'auditing': auditing,
        'dropped': dropped,
        'grades': models.Grade.objects.filter(is_active=True).order_by('-points'),
        'participants_for_export': models.Participant.objects.filter(course=course,
                                        is_adviser_approved=True,
                                        is_instructor_approved=True).order_by('is_drop', '-is_credit')
    }
    return render(request, 'coursereg/instructor_detail.html', context)

def replace_year(dt, new_year, min_dt):
    new_dt = None
    new_year = int(new_year)
    try:
        new_dt = dt.replace(year=new_year)
    except ValueError:
        new_dt = dt + (date(new_year, 1, 1) - date(d.year, 1, 1))
    if min_dt and new_dt < min_dt:
        return replace_year(dt, new_year+1, min_dt)
    return new_dt

def get_total_credits(credit_label):
    return sum(int(c) for c in re.split(r'[^0-9]', credit_label) if c.isdigit())

@login_required
def course_new(request):
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    if not models.Config.can_faculty_create_courses():
        raise PermissionDenied

    if request.method == 'POST':
        term = models.Term.objects.get(id=request.POST['term'])
        year = str(request.POST['year'])
        num = request.POST['num']
        course = models.Course.objects.filter(num=num, term=term, year=year).first()
        if course:
            messages.error(request, "%s already exists." % course)
        else:
            last_reg_date = replace_year(term.default_last_reg_date, year, None)
            course = models.Course.objects.create(
                title=request.POST['name'],
                num=num,
                department=request.user.department,
                term=term,
                year=year,
                num_credits=get_total_credits(request.POST['credit_label']),
                credit_label=request.POST['credit_label'],
                auto_instructor_approve=request.POST.get('auto_instructor_approve', False),
                last_reg_date=last_reg_date,
                last_adviser_approval_date=replace_year(term.default_last_adviser_approval_date, year, last_reg_date),
                last_instructor_approval_date=replace_year(term.default_last_instructor_approval_date, year, last_reg_date),
                last_conversion_date=replace_year(term.default_last_conversion_date, year, last_reg_date),
                last_drop_date=replace_year(term.default_last_drop_date, year, last_reg_date),
                last_grade_date=replace_year(term.default_last_grade_date, year, last_reg_date)
            )
            models.Participant.objects.create(user=request.user, course=course, participant_type=models.Participant.PARTICIPANT_INSTRUCTOR)
            for coinstructor_id in request.POST.getlist('coinstructor'):
                if coinstructor_id:
                    coinstructor = models.User.objects.get(id=coinstructor_id)
                    models.Participant.objects.create(
                        user=coinstructor,
                        course=course,
                        participant_type=models.Participant.PARTICIPANT_INSTRUCTOR)
            messages.success(request, '%s created.' % course)
        return redirect('coursereg:instructor')
    else:
        context = {
            'user_type': 'faculty',
            'nav_active': 'instructor',
            'user_email': request.user.email,
            'terms': models.Term.objects.filter(is_active=True),
            'recent_courses': models.Course.objects.filter(
                department=request.user.department,
                last_reg_date__gte=timezone.now()-timedelta(days=800)),
            'instructors': models.User.objects.filter(
                is_active=True,
                user_type=models.User.USER_TYPE_FACULTY).exclude(email=request.user.email).order_by('full_name'),
        }
        return render(request, 'coursereg/course_new.html', context)

@login_required
def course_update(request, course_id):
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    if not models.Config.can_faculty_create_courses():
        raise PermissionDenied
    course = models.Course.objects.get(id=course_id)
    if not models.Participant.objects.filter(
            course=course,
            user=request.user,
            participant_type=models.Participant.PARTICIPANT_INSTRUCTOR):
        raise PermissionDenied

    if request.method == 'POST':
        term = models.Term.objects.get(id=request.POST['term'])
        year = str(request.POST['year'])
        num = request.POST['num']
        last_reg_date = replace_year(term.default_last_reg_date, year, None)
        models.Course.objects.filter(id=course_id).update(
            title=request.POST['name'],
            num=num,
            term=term,
            year=year,
            num_credits=get_total_credits(request.POST['credit_label']),
            credit_label=request.POST['credit_label'],
            auto_instructor_approve=request.POST.get('auto_instructor_approve', False),
            last_reg_date=last_reg_date,
            last_adviser_approval_date=replace_year(term.default_last_adviser_approval_date, year, last_reg_date),
            last_instructor_approval_date=replace_year(term.default_last_instructor_approval_date, year, last_reg_date),
            last_conversion_date=replace_year(term.default_last_conversion_date, year, last_reg_date),
            last_drop_date=replace_year(term.default_last_drop_date, year, last_reg_date),
            last_grade_date=replace_year(term.default_last_grade_date, year, last_reg_date)
        )
        models.Participant.objects.filter(
            course=course,
            participant_type=models.Participant.PARTICIPANT_INSTRUCTOR).exclude(user=request.user).delete()
        for coinstructor_id in request.POST.getlist('coinstructor'):
            if coinstructor_id:
                coinstructor = models.User.objects.get(id=coinstructor_id)
                models.Participant.objects.create(
                    user=coinstructor,
                    course=course,
                    participant_type=models.Participant.PARTICIPANT_INSTRUCTOR)
        messages.success(request, 'Updated %s' % course)
        return redirect(reverse('coursereg:instructor_detail', args=[course.id]))
    else:
        coinstructor_ids = [p.user.id for p in models.Participant.objects.filter(
            course=course,
            participant_type=models.Participant.PARTICIPANT_INSTRUCTOR
        ).exclude(user=request.user)]
        context = {
            'user_type': 'faculty',
            'nav_active': 'instructor',
            'user_email': request.user.email,
            'course': course,
            'terms': models.Term.objects.filter(is_active=True),
            'coinstructor_ids': coinstructor_ids,
            'recent_courses': models.Course.objects.filter(
                department=request.user.department,
                last_reg_date__gte=timezone.now()-timedelta(days=800)),
            'instructors': models.User.objects.filter(
                is_active=True,
                user_type=models.User.USER_TYPE_FACULTY).exclude(email=request.user.email).order_by('full_name'),
        }
        return render(request, 'coursereg/course_update.html', context)
