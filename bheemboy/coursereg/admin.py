from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User, Course, Participant
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserAdmin(UserAdmin):
    # The forms to add and change user instances

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference the removed 'username' field
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'user_type', 'adviser', 'program', 'sr_no')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'user_type', 'adviser', 'program', 'sr_no', 'date_joined')}
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('email', 'full_name', 'user_type', 'sr_no')
    search_fields = ('email', 'full_name')
    raw_id_fields = ('adviser',)
    ordering = ('email',)

class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    can_delete = False
    show_change_link = True
    raw_id_fields = ('user',)
    fields = ('user', 'participant_type', 'state')
    ordering = ('-participant_type',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('num', 'title', 'department', 'last_reg_date')
    ordering = ('-last_reg_date',)
    search_fields = ('title', 'num', 'department')
    inlines = [ParticipantInline]

class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'participant_type', 'state', 'grade')
    ordering = ('-course__last_reg_date',)
    search_fields = ('user__email', 'course__title', 'course__num')
    raw_id_fields = ('user', 'course')
    list_filter = ('participant_type', 'state')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Participant, ParticipantAdmin)
