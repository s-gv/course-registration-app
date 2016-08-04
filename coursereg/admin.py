from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User, Course, Participant, Faq, Department, Degree, Notification, Config, Grade, Term
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from datetime import timedelta
from django.core.urlresolvers import reverse
from django.utils.html import format_html

class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    show_change_link = True
    raw_id_fields = ('user',)
    fields = ('user', 'participant_type', 'is_credit', 'is_drop', 'is_drop_mentioned', 'is_adviser_approved', 'is_instructor_approved', 'grade', 'should_count_towards_cgpa')
    ordering = ('-participant_type',)

class CourseInline(admin.TabularInline):
    model = Participant
    verbose_name = "Course"
    verbose_name_plural = "Courses"
    extra = 0
    show_change_link = True
    raw_id_fields = ('course',)
    fields = ('course', 'participant_type', 'is_credit', 'is_drop', 'is_drop_mentioned', 'is_adviser_approved', 'is_instructor_approved', 'grade', 'should_count_towards_cgpa')
    ordering = ('-course__last_reg_date',)

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
        (None, {'fields': ('full_name', 'department', 'user_type', 'adviser', 'degree', 'sr_no', 'cgpa', 'telephone', 'is_active', 'is_dcc_review_pending')}),
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
    list_display = ('email', 'full_name', 'user_type', 'degree', 'department', 'telephone', 'cgpa', 'date_joined', 'is_active', 'login_as')
    list_filter = ('is_active', 'user_type', 'degree', 'is_dcc_review_pending')
    search_fields = ('email', 'full_name')
    raw_id_fields = ('adviser',)
    readonly_fields = ('cgpa',)
    ordering = ('-date_joined',)
    inlines = [CourseInline]
    actions = ['make_inactive', 'make_active', 'clear_dcc_review']

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Make selected users inactive"

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Make selected users active"

    def clear_dcc_review(self, request, queryset):
        queryset.update(is_dcc_review_pending=False)
    clear_dcc_review.short_description = "Clear DCC review"

    def login_as(self, user):
        return format_html("<a href='{url}'>Login</a>", url=reverse('coursereg:sudo_login', args=[user.id]))

class CourseAdmin(admin.ModelAdmin):
    list_display = ('num', 'title', 'department', 'last_reg_date', 'num_credits', 'should_count_towards_cgpa', 'auto_instructor_approve')
    ordering = ('-last_reg_date', 'department__name', 'num', 'title')
    search_fields = ('title', 'num', 'last_reg_date')
    inlines = [ParticipantInline]
    actions = ['clone_courses_increment_year']

    def clone_courses_increment_year(self, request, queryset):
        def add_one_year(d):
            new_d = None
            try:
                new_d = d.replace(year=d.year+1)
            except ValueError:
                new_d = d + (date(d.year + 1, 1, 1) - date(d.year, 1, 1))
            return new_d
        for course in queryset:
            if not Course.objects.filter(num=course.num,
                    last_reg_date__gte=add_one_year(course.last_reg_date)-timedelta(days=15),
                    last_reg_date__lte=add_one_year(course.last_reg_date)+timedelta(days=15)):
                old_course_id = course.id
                course.pk = None
                course.last_reg_date = add_one_year(course.last_reg_date)
                course.last_conversion_date = add_one_year(course.last_conversion_date)
                course.last_drop_date = add_one_year(course.last_drop_date)
                course.last_drop_with_mention_date = add_one_year(course.last_drop_with_mention_date)
                course.last_grade_date = add_one_year(course.last_grade_date)
                course.save()
                for participant in Participant.objects.filter(course__id=old_course_id, participant_type=Participant.PARTICIPANT_INSTRUCTOR):
                    Participant.objects.create(
                        user=participant.user,
                        course=course,
                        participant_type=participant.participant_type
                    )
    clone_courses_increment_year.short_description = "Clone selected courses and increment year"


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'participant_type', 'is_credit', 'is_drop', 'is_drop_mentioned', 'is_adviser_approved', 'is_instructor_approved', 'should_count_towards_cgpa', 'grade')
    ordering = ('-course__last_reg_date', 'user__full_name')
    search_fields = ('user__email', 'user__full_name', 'course__title', 'course__num', 'course__last_reg_date')
    raw_id_fields = ('user', 'course')
    list_filter = ('participant_type', 'is_credit', 'is_drop', 'is_drop_mentioned', 'course__last_reg_date', 'is_adviser_approved', 'is_instructor_approved')
    actions = ['adviser_approve', 'instructor_approve']

    def adviser_approve(self, request, queryset):
        queryset.filter(participant_type=Participant.PARTICIPANT_STUDENT).update(is_adviser_approved=True)
    adviser_approve.short_description = 'Adviser approve selected students'

    def instructor_approve(self, request, queryset):
        queryset.filter(participant_type=Participant.PARTICIPANT_STUDENT).update(is_instructor_approved=True)
    instructor_approve.short_description = 'Instructor approve selected students'

class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'faq_for')
    search_fields = ('question', 'answer')
    list_filter = ('faq_for',)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')

class DegreeAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'origin', 'message', 'is_student_acknowledged', 'is_adviser_acknowledged', 'is_dcc_acknowledged', 'created_at')
    ordering = ('-created_at', 'user__full_name')
    search_fields = ('user', 'origin', 'message')
    list_filter = ('origin', 'is_student_acknowledged', 'is_adviser_acknowledged', 'is_dcc_acknowledged', 'created_at')
    raw_id_fields = ('user', )
    readonly_fields = ('created_at',)

class ConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)

class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'points', 'should_count_towards_cgpa')

class TermAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Faq, FaqAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Degree, DegreeAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(Term, TermAdmin)
