from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import date, timedelta
from django.utils import timezone
from coursereg import models
from django.conf import settings
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
        'can_faculty_create_courses': settings.CAN_FACULTY_CREATE_COURSES,
        'courses': [p.course for p in models.Participant.objects.filter(user=request.user).order_by('-course__term__last_reg_date')]
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

    if settings.WARN_REVIEW_BEFORE_LAST_DATE and not course.is_last_adviser_approval_date_passed():
        messages.warning(request, 'Registration for this course is still open. Visit this page after the last application date.')

    context = {
        'user_type': 'faculty',
        'nav_active': 'instructor',
        'user_email': request.user.email,
        'course': course,
        'is_manual_faculty_review_enabled': settings.MANUAL_FACULTY_REVIEW,
        'can_faculty_create_courses': settings.CAN_FACULTY_CREATE_COURSES,
        'grades': models.Grade.objects.filter(is_active=True).order_by('-points'),
        'participants': list(models.Participant.objects.filter(course=course,
                            participant_type=models.Participant.PARTICIPANT_STUDENT).order_by('is_drop', '-registration_type', 'created_at'))
    }
    if not settings.MANUAL_FACULTY_REVIEW:
        models.Participant.objects.filter(course=course, user__user_type=models.User.USER_TYPE_STUDENT, is_instructor_reviewed=False).update(is_instructor_reviewed=True)
    return render(request, 'coursereg/instructor_detail.html', context)

@login_required
def course_new(request):
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    if settings.CAN_FACULTY_CREATE_COURSES:
        raise PermissionDenied

    if request.method == 'POST':
        term = models.Term.objects.get(id=request.POST['term'])
        num = request.POST['num']
        course = models.Course.objects.filter(num=num, term=term).first()
        if course:
            messages.error(request, "%s already exists." % course)
        else:
            course = models.Course.objects.create(
                title=request.POST['name'],
                num=num,
                department=request.user.department,
                term=term,
                credits=request.POST['credits'],
                should_count_towards_cgpa=request.POST.get('should_count_towards_cgpa', True)
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
            'terms': models.Term.objects.filter(is_active=True, year__in=[timezone.now().year, timezone.now().year+1]),
            'recent_courses': models.Course.objects.filter(
                department=request.user.department,
                term__last_reg_date__gte=timezone.now()-timedelta(days=800)),
            'instructors': models.User.objects.filter(
                is_active=True,
                user_type=models.User.USER_TYPE_FACULTY).exclude(email=request.user.email).order_by('full_name'),
        }
        return render(request, 'coursereg/course_new.html', context)

@login_required
def course_update(request, course_id):
    if not request.user.user_type == models.User.USER_TYPE_FACULTY:
        raise PermissionDenied
    if not settings.CAN_FACULTY_CREATE_COURSES:
        raise PermissionDenied
    course = models.Course.objects.get(id=course_id)
    if not models.Participant.objects.filter(
            course=course,
            user=request.user,
            participant_type=models.Participant.PARTICIPANT_INSTRUCTOR):
        raise PermissionDenied
    if course.is_last_grade_date_passed():
        raise PermissionDenied

    if request.method == 'POST':
        term = models.Term.objects.get(id=request.POST['term'])
        num = request.POST['num']
        models.Course.objects.filter(id=course_id).update(
            title=request.POST['name'],
            num=num,
            term=term,
            credits=request.POST['credits'],
            timings=request.POST['timings'],
            should_count_towards_cgpa=request.POST.get('should_count_towards_cgpa', True)
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
            'terms': models.Term.objects.filter(is_active=True, year__in=[timezone.now().year, timezone.now().year+1]),
            'coinstructor_ids': coinstructor_ids,
            'recent_courses': models.Course.objects.filter(
                department=request.user.department,
                term__last_reg_date__gte=timezone.now()-timedelta(days=800)),
            'instructors': models.User.objects.filter(
                is_active=True,
                user_type=models.User.USER_TYPE_FACULTY).exclude(email=request.user.email).order_by('full_name'),
        }
        return render(request, 'coursereg/course_update.html', context)
