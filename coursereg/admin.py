from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User, Course, Participant, Faq, Department, Degree, Notification, Config
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from datetime import timedelta

class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    can_delete = False
    show_change_link = True
    raw_id_fields = ('user',)
    fields = ('user', 'participant_type', 'state', 'grade', 'is_adviser_approved', 'is_instructor_approved')
    ordering = ('-participant_type',)

class CourseInline(admin.TabularInline):
    model = Participant
    verbose_name = "Course"
    verbose_name_plural = "Courses"
    extra = 0
    can_delete = False
    show_change_link = True
    raw_id_fields = ('course',)
    fields = ('course', 'participant_type', 'state', 'grade', 'is_adviser_approved', 'is_instructor_approved')
    ordering = ('-course__last_reg_date',)

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (None, {'fields': ('full_name', 'department', 'user_type', 'adviser', 'degree', 'sr_no', 'is_active', 'is_dcc_review_pending')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'department', 'user_type', 'adviser', 'degree', 'sr_no', 'date_joined')}
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('email', 'full_name', 'user_type', 'degree', 'sr_no', 'is_active', 'is_dcc_review_pending')
    list_filter = ('is_active', 'user_type', 'degree', 'is_dcc_review_pending')
    search_fields = ('email', 'full_name')
    raw_id_fields = ('adviser',)
    ordering = ('-date_joined',)
    inlines = [CourseInline]
    actions = ['make_inactive', 'make_active', 'clear_dcc_review']

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Deactivate selected users"

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Activate selected users"

    def clear_dcc_review(self, request, queryset):
        queryset.update(is_dcc_review_pending=False)
    clear_dcc_review.short_description = "Clear DCC review"

class CourseAdmin(admin.ModelAdmin):
    list_display = ('num', 'title', 'department', 'last_reg_date', 'last_drop_date')
    ordering = ('-last_reg_date', 'department__name', 'num', 'title')
    search_fields = ('title', 'num', 'last_reg_date')
    inlines = [ParticipantInline]
    actions = ['clone_courses_increment_year']

    def clone_courses_increment_year(self, request, queryset):
        for course in queryset:
            d = course.last_reg_date
            try:
                new_last_reg_date = d.replace(year=d.year+1)
            except ValueError:
                new_last_reg_date = d + (date(d.year + 1, 1, 1) - date(d.year, 1, 1))
            if not Course.objects.filter(num=course.num,
                    last_reg_date__gte=new_last_reg_date-timedelta(days=30),
                    last_reg_date__lte=new_last_reg_date+timedelta(days=30)):
                new_course = Course.objects.create(
                    num=course.num,
                    title=course.title,
                    term=course.term,
                    last_reg_date=new_last_reg_date,
                    credits=course.credits,
                    department=course.department
                )
                for participant in Participant.objects.filter(course=course, participant_type=Participant.PARTICIPANT_INSTRUCTOR):
                    Participant.objects.create(
                        user=participant.user,
                        course=new_course,
                        participant_type=participant.participant_type,
                        state=participant.state,
                        grade=participant.grade,
                        is_adviser_approved=participant.is_adviser_approved,
                        is_instructor_approved=participant.is_instructor_approved
                    )
    clone_courses_increment_year.short_description = "Clone selected courses and increment year"


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'participant_type', 'state', 'grade', 'is_adviser_approved', 'is_instructor_approved')
    ordering = ('-course__last_reg_date', 'user__full_name')
    search_fields = ('user__email', 'user__full_name', 'course__title', 'course__num', 'course__last_reg_date')
    raw_id_fields = ('user', 'course')
    list_filter = ('participant_type', 'state', 'course__last_reg_date', 'is_adviser_approved', 'is_instructor_approved')

class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'faq_for')
    search_fields = ('question', 'answer')
    list_filter = ('faq_for',)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )

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

admin.site.register(User, CustomUserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Faq, FaqAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Degree, DegreeAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Config, ConfigAdmin)
