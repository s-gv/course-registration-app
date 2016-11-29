from django.contrib import admin
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from .models import User, Course, Participant, Faq, Department, Degree, Notification, Grade, Term, RegistrationType
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from datetime import timedelta
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from django.utils.http import urlquote_plus, urlunquote_plus
from django.contrib.contenttypes.models import ContentType
from django.conf.urls import url, include
import csv
from django.utils.http import urlencode
from email.utils import parseaddr
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from coursereg import utils
from coursereg import models
from coursereg import views
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin import AdminSite
import coursereg.utils

class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    show_change_link = True
    raw_id_fields = ('user',)
    fields = ('user', 'participant_type', 'registration_type', 'is_drop', 'grade', 'should_count_towards_cgpa', 'lock_from_student')
    ordering = ('-participant_type',)

class CourseInline(admin.TabularInline):
    model = Participant
    verbose_name = "Course"
    verbose_name_plural = "Courses"
    extra = 0
    show_change_link = True
    raw_id_fields = ('course',)
    fields = ('course', 'participant_type', 'registration_type', 'is_drop', 'grade', 'should_count_towards_cgpa', 'lock_from_student')
    ordering = ('-course__term__last_reg_date',)

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password1'].help_text = 'Leave blank for random password'
        self.fields['password2'].required = False
        self.fields['password1'].widget.attrs['autocomplete'] = 'off'
        self.fields['password2'].widget.attrs['autocomplete'] = 'off'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 == '' and password2 == '':
            return User.objects.make_random_password()
        return UserCreationForm.clean_password2(self)

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.clean_password2())
        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (None, {'fields': ('full_name', 'department', 'user_type', 'adviser', 'degree', 'sr_no', 'cgpa', 'telephone', 'is_active', 'is_dcc_review_pending', 'is_dcc_sent_notification')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'department', 'user_type', 'adviser', 'degree', 'sr_no', 'telephone', 'date_joined')}
        ),
    )
    form = UserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('email', 'full_name', 'user_type', 'degree', 'department', 'telephone', 'date_joined', 'is_active', 'login_as')
    list_filter = ('is_active', 'user_type', 'degree', 'department')
    search_fields = ('email', 'full_name')
    raw_id_fields = ('adviser',)
    readonly_fields = ('cgpa',)
    ordering = ('-date_joined',)
    inlines = [CourseInline]
    actions = ['make_inactive', 'make_active', 'clear_dcc_review']
    #change_list_template = 'admin/coursereg/user/custom_user_changelist.html

    def get_urls(self):
        urls = super(CustomUserAdmin, self).get_urls()
        my_urls = [
            url(r'^bulkaddstudents$', self.admin_site.admin_view(self.bulk_add_students), name='coursereg_user_bulk_add_students'),
            url(r'^bulkaddfaculty$', self.admin_site.admin_view(self.bulk_add_faculty), name='coursereg_user_bulk_add_faculty'),
            url(r'^bulkdeactivate$', self.admin_site.admin_view(self.bulk_deactivate_students), name='coursereg_user_bulk_deactivate_students'),
            url(r'^login/(.+)$', self.admin_site.admin_view(self.sudo_login), name='coursereg_user_sudo_login'),
        ]
        return my_urls + urls

    def sudo_login(self, request, user_id):
        user = models.User.objects.get(id=user_id)
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        login(request, user)
        return redirect(reverse('coursereg:index'))

    def bulk_add_faculty(self, request):
        if request.method == 'POST':
            f = request.FILES['faculty_csv']
            faculty = []
            error = False
            for line_num, row in enumerate(csv.reader(f), start=1):
                error = True
                faculty.append({
                })
                try:
                    name, email, dept_abbr = [ele.strip() for ele in row]
                    faculty[-1]['name'] = name
                except:
                    messages.error(request, 'Number of fields incorrect in line %s. No records were added.' % line_num)
                    break
                if len(name) < 3:
                    messages.error(request, 'Name has less than 3 characters in line %s. No records were added.' % line_num)
                    break
                if '@' in parseaddr(email)[1]:
                    faculty[-1]['email'] = email
                else:
                    messages.error(request, 'Email invalid in line %s. No records were added.' % line_num)
                    break
                if User.objects.filter(email=email):
                    messages.error(request, 'Email in line %s already exists. No records were added.' % line_num)
                    break
                try:
                    faculty[-1]['dept'] = Department.objects.get(abbreviation=str(dept_abbr))
                except:
                    messages.error(request, 'Department in line %s not found. No records were added.' % line_num)
                    break
                error = False
            if not error:
                for fac in faculty:
                    User.objects.create_user(
                        email=fac['email'],
                        full_name=fac['name'],
                        user_type=User.USER_TYPE_FACULTY,
                        department=fac['dept']
                    )
                messages.success(request, "Successfully added %s faculty." % len(faculty))
                return redirect('admin:coursereg_user_changelist')
        context = dict(
           self.admin_site.each_context(request),
           title='Bulk load faculty'
        )
        return render(request, "admin/coursereg/user/bulk_add_faculty.html", context)

    def bulk_add_students(self, request):
        if request.method == 'POST':
            f = request.FILES['students_csv']
            students = []
            error = False
            for line_num, row in enumerate(csv.reader(f), start=1):
                error = True
                students.append({
                })
                try:
                    name, email, dept_abbr, phone, degree, sr_no, join_date, adviser_email = [ele.strip() for ele in row]
                    students[-1]['name'] = name
                except:
                    messages.error(request, 'Number of fields incorrect in line %s. No records were added.' % line_num)
                    break
                if len(name) < 3:
                    messages.error(request, 'Name has less than 3 characters in line %s. No records were added.' % line_num)
                    break
                if '@' in parseaddr(email)[1]:
                    students[-1]['email'] = email
                else:
                    messages.error(request, 'Email invalid in line %s. No records were added.' % line_num)
                    break
                if User.objects.filter(email=email):
                    messages.error(request, 'Email in line %s already exists. No records were added.' % line_num)
                    break
                try:
                    students[-1]['dept'] = Department.objects.get(abbreviation=str(dept_abbr))
                except:
                    messages.error(request, 'Department in line %s not found. No records were added.' % line_num)
                    break
                students[-1]['phone'] = phone
                try:
                    students[-1]['degree'] = Degree.objects.get(name=degree)
                except:
                    messages.error(request, 'Degree invalid in line %s. No records were added.' % line_num)
                    break
                students[-1]['sr_no'] = sr_no
                try:
                    students[-1]['join_date'] = datetime.strptime(join_date, '%d %b %Y')
                except:
                    messages.error(request, 'Date not in expected format (ex: 01 Aug 2011) in line %s. No records were added.' % line_num)
                    break
                try:
                    students[-1]['adviser'] = User.objects.get(email=adviser_email)
                except:
                    messages.error(request, 'Adviser email invalid in line %s. Nothing added.' % line_num)
                    break
                error = False
            if not error:
                for student in students:
                    User.objects.create_user(
                        email=student['email'],
                        full_name=student['name'],
                        user_type=User.USER_TYPE_STUDENT,
                        adviser=student['adviser'],
                        degree=student['degree'],
                        department=student['dept'],
                        sr_no=student['sr_no'],
                        telephone=student['phone'],
                        date_joined=student['join_date']
                    )
                messages.success(request, "Successfully added %s students." % len(students))
                return redirect('admin:coursereg_user_changelist')
        context = dict(
           self.admin_site.each_context(request),
           title='Bulk load students'
        )
        return render(request, "admin/coursereg/user/bulk_add_students.html", context)

    def bulk_deactivate_students(self, request):
        if request.method == 'POST':
            f = request.FILES['students_csv']
            students = []
            error = False
            for line_num, row in enumerate(csv.reader(f), start=1):
                error = True
                students.append({
                })
                try:
                    email = [ele.strip() for ele in row][0]
                    u = User.objects.get(email=email)
                    students[-1]['email'] = u.email
                except:
                    messages.error(request, 'Email in line %s not found. No records updated.' % line_num)
                    break
                if u.user_type != User.USER_TYPE_STUDENT:
                    messages.error(request, 'Email in line %s does not belong to a student. No records updated.' % line_num)
                    break
                error = False
            if not error:
                for student in students:
                    User.objects.filter(email=student['email']).update(is_active=False)
                messages.success(request, "Successfully de-activated %s students." % len(students))
                return redirect('admin:coursereg_user_changelist')
        context = dict(
           self.admin_site.each_context(request),
           title='Bulk deactivate students'
        )
        return render(request, "admin/coursereg/user/bulk_deactivate_students.html", context)

    def make_inactive(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, "%s users marked as inactive." % n)
    make_inactive.short_description = "Make selected users inactive"

    def make_active(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, "%s users marked as active." % n)
    make_active.short_description = "Make selected users active"

    def clear_dcc_review(self, request, queryset):
        n = queryset.update(is_dcc_review_pending=False)
        self.message_user(request, "DCC review cleared for %s users." % n)
    clear_dcc_review.short_description = "Clear DCC review"

    def login_as(self, user):
        return format_html("<a href='{url}'>Login</a>", url=reverse('admin:coursereg_user_sudo_login', args=[user.id]))

class CourseAdmin(admin.ModelAdmin):
    list_display = ('num', 'title', 'credits', 'term', 'department', 'should_count_towards_cgpa')
    ordering = ('-term__last_reg_date', 'department__name', 'num', 'title')
    search_fields = ('title', 'num', 'term__name', 'term__year')
    list_filter = ('department', 'should_count_towards_cgpa')
    raw_id_fields = ('term',)
    inlines = [ParticipantInline]

    def get_urls(self):
        urls = super(CourseAdmin, self).get_urls()
        my_urls = [
            url(r'^bulkaddcourses$', self.admin_site.admin_view(self.bulk_add_courses), name='coursereg_course_bulk_add_courses'),
        ]
        return my_urls + urls

    def bulk_add_courses(self, request):
        if request.method == 'POST':
            f = request.FILES['courses_csv']
            courses = []
            error = False
            for line_num, row in enumerate(csv.reader(f), start=1):
                error = True
                courses.append({})
                if len(row) < 9:
                    messages.error(request, 'Number of fields insufficient in line %s. No records were added.' % line_num)
                    break
                num, title, credits, term_name, term_year, dept_abbr, timings, description, should_count_towards_cgpa = [ele.strip() for ele in row[:9]]
                instructor_emails = [ele.strip() for ele in row[9:]]
                if len(num) > 1:
                    courses[-1]['num'] = num
                else:
                    messages.error(request, 'Course number in line %s is too short. No records were added.' % line_num)
                    break
                if len(title) > 3:
                    courses[-1]['title'] = title
                else:
                    messages.error(request, 'Course title in line %s is too short. No records were added.' % line_num)
                    break
                if len(credits) > 0:
                    courses[-1]['credits'] = credits
                else:
                    messages.error(request, 'Course credits in line %s is too short. No records were added.' % line_num)
                    break
                try:
                    courses[-1]['term'] = Term.objects.filter(name=term_name, year=term_year).first()
                    assert courses[-1]['term'] is not None
                except:
                    messages.error(request, 'Course term in line %s not found. No records were added.' % line_num)
                    break
                try:
                    courses[-1]['dept'] = Department.objects.get(abbreviation=dept_abbr)
                except:
                    messages.error(request, 'Department in line %s not found. No records were added.' % line_num)
                    break
                courses[-1]['timings'] = timings
                courses[-1]['description'] = description
                if should_count_towards_cgpa.lower() == 'true' or should_count_towards_cgpa == '1':
                    courses[-1]['should_count_towards_cgpa'] = True
                elif should_count_towards_cgpa.lower() == 'false' or should_count_towards_cgpa == '0':
                    courses[-1]['should_count_towards_cgpa'] = False
                else:
                    messages.error(request, 'Field should_count_towards_cgpa in line %s should be boolean (true/false). No records were added.' % line_num)
                    break
                if Course.objects.filter(num=num, title=title, credits=credits, term=courses[-1]['term'], department=courses[-1]['dept']):
                    messages.error(request, 'Course in line %s already exists. No records were added.' % line_num)
                    break
                courses[-1]['instructors'] = []
                try:
                    for instructor_email in instructor_emails:
                        if instructor_email:
                            instructor = User.objects.get(email=instructor_email)
                            courses[-1]['instructors'].append(instructor)
                except:
                    messages.error(request, "Instructor '%s' in line %s not found. No records were added." % (instructor_email, line_num))
                    break
                error = False
            if not error:
                for course in courses:
                    c = Course.objects.create(
                        num=course['num'],
                        title=course['title'],
                        credits=course['credits'],
                        department=course['dept'],
                        term=course['term'],
                        timings=course['timings'],
                        description=course['description'],
                        should_count_towards_cgpa=course['should_count_towards_cgpa']
                    )
                    for instructor in course['instructors']:
                        Participant.objects.create(
                            user=instructor,
                            course=c,
                            participant_type=Participant.PARTICIPANT_INSTRUCTOR
                        )
                messages.success(request, "Successfully added %s courses." % len(courses))
                return redirect('admin:coursereg_course_changelist')
        context = dict(
           self.admin_site.each_context(request),
           title='Bulk load courses'
        )
        return render(request, "admin/coursereg/course/bulk_add_courses.html", context)

class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'participant_type', 'registration_type', 'is_drop', 'should_count_towards_cgpa', 'lock_from_student', 'grade')
    ordering = ('-course__term__last_reg_date', 'user__full_name')
    search_fields = ('user__email', 'user__full_name', 'course__title', 'course__num', 'course__term__last_reg_date')
    raw_id_fields = ('user', 'course')
    list_filter = ('participant_type', 'registration_type', 'is_drop')

class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'faq_for')
    search_fields = ('question', 'answer')
    list_filter = ('faq_for',)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'is_active', 'report_link')
    search_fields = ('name', 'abbreviation')

    def get_urls(self):
        urls = super(DepartmentAdmin, self).get_urls()
        my_urls = [
            url(r'^report/(.+)$', self.admin_site.admin_view(self.report_view), name='coursereg_department_report'),
        ]
        return my_urls + urls

    def report_view(self, request, dept_id):
        dept = models.Department.objects.get(id=dept_id)
        from_date = timezone.now()
        to_date = timezone.now()
        if request.GET.get('from_date') and request.GET.get('to_date'):
            from_date = utils.parse_datetime_str(request.GET['from_date'])
            to_date = utils.parse_datetime_str(request.GET['to_date'])
        participants = [p for p in models.Participant.objects.filter(
            user__department=dept,
            user__user_type=models.User.USER_TYPE_STUDENT,
            course__term__last_reg_date__range=[from_date, to_date]
        ).order_by('user__degree', 'is_drop', 'registration_type', 'user__full_name')]
        context = dict(
           self.admin_site.each_context(request),
           title='Report',
           default_from_date=utils.datetime_to_str(from_date),
           default_to_date=utils.datetime_to_str(to_date),
           participants=participants,
           dept=dept
        )
        return render(request, 'admin/coursereg/department/report.html', context)

    def report_link(self, dept):
        return format_html("<a href='{url}'>Report</a>", url=reverse('admin:coursereg_department_report', args=[dept.id]))

class DegreeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name', )

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'origin', 'message', 'is_student_acknowledged', 'is_adviser_acknowledged', 'is_dcc_acknowledged', 'created_at')
    ordering = ('-created_at', 'user__full_name')
    search_fields = ('user', 'origin', 'message')
    list_filter = ('origin', 'is_student_acknowledged', 'is_adviser_acknowledged', 'is_dcc_acknowledged', 'created_at')
    raw_id_fields = ('user', )
    readonly_fields = ('created_at',)

class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'points', 'should_count_towards_cgpa', 'is_active')

class RegistrationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'should_count_towards_cgpa', 'is_active')

class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'last_reg_date', 'is_active')
    search_fields = ('name', 'year')
    actions = ['clone_terms_increment_year']

    def clone_terms_increment_year(self, request, queryset):
        def add_one_year(d):
            new_d = None
            try:
                new_d = d.replace(year=d.year+1)
            except ValueError:
                new_d = d + (date(d.year + 1, 1, 1) - date(d.year, 1, 1))
            return new_d
        n = 0
        for term in queryset:
            if not Term.objects.filter(name=term.name, year=str(int(term.year)+1)):
                n += 1
                old_term_id = term.id
                term.pk = None
                term.year = str(int(term.year)+1)
                term.start_reg_date = add_one_year(term.start_reg_date)
                term.last_reg_date = add_one_year(term.last_reg_date)
                term.last_adviser_approval_date = add_one_year(term.last_adviser_approval_date)
                term.last_instructor_approval_date = add_one_year(term.last_instructor_approval_date)
                term.last_cancellation_date = add_one_year(term.last_cancellation_date)
                term.last_conversion_date = add_one_year(term.last_conversion_date)
                term.last_drop_date = add_one_year(term.last_drop_date)
                term.last_grade_date = add_one_year(term.last_grade_date)
                term.save()
        self.message_user(request, "Cloned %s terms" % n)
    clone_terms_increment_year.short_description = "Clone selected terms and increment year"

def merge_selected_objects(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    ct = ContentType.objects.get_for_model(queryset.model)
    return redirect(reverse('admin:merge_objects') + '?' + urlencode({'ctpk': ct.pk, 'ids': ','.join(selected)}))
merge_selected_objects.short_description = "Merge selected objects"

class CustomAdminSite(AdminSite):
    site_header = 'Coursereg administration'

    def get_urls(self):
        urls = super(CustomAdminSite, self).get_urls()
        my_urls = [
            url(r'^logout/$', views.user.signout),
            url(r'^mergeobjects$', self.merge_objects, name='merge_objects')
        ]
        return my_urls + urls

    def merge_objects(self, request):
        ctpk = request.GET['ctpk']
        ids = request.GET['ids'].split(',')

        ct = ContentType.objects.get(pk=ctpk)
        model = ct.model_class()
        objs = model.objects.filter(id__in=ids)

        if len(ids) < 2:
            messages.error(request, "Select at least two objects to merge.")
            return redirect(reverse('admin:coursereg_%s_changelist' % ct.model))

        if request.method == 'POST':
            primary_id = request.POST['primary']
            primary_obj = model.objects.get(id=primary_id)
            alias_objs = list(model.objects.filter(id__in=ids).exclude(id=primary_id))
            coursereg.utils.merge_model_objects(primary_obj, alias_objs)
            messages.success(request, "Successfully merged %s objects." % len(ids))
            return redirect(reverse('admin:coursereg_%s_changelist' % ct.model))
        else:
            context = dict(
               self.each_context(request),
               title='Merge %s' % model._meta.verbose_name_plural.title().lower(),
               model_name=model._meta.verbose_name.title(),
               model_changelist_url=reverse('admin:coursereg_%s_changelist' % ct.model),
               objs_with_urls=[(reverse('admin:coursereg_%s_change' % ct.model, args=[obj.id]), obj) for obj in objs]
            )
            return render(request, "admin/coursereg/merge_objects.html", context)

admin_site = CustomAdminSite(name='customadmin')
admin_site.add_action(merge_selected_objects, 'merge_selected')

admin_site.register(User, CustomUserAdmin)
admin_site.register(Course, CourseAdmin)
admin_site.register(Participant, ParticipantAdmin)
admin_site.register(Faq, FaqAdmin)
admin_site.register(Department, DepartmentAdmin)
admin_site.register(Degree, DegreeAdmin)
admin_site.register(Notification, NotificationAdmin)
admin_site.register(Grade, GradeAdmin)
admin_site.register(Term, TermAdmin)
admin_site.register(RegistrationType, RegistrationTypeAdmin)
