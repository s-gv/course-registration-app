from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User, Course, Participant
from .forms import CustomUserChangeForm, CustomUserCreationForm

class CustomUserAdmin(UserAdmin):
    # The forms to add and change user instances

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference the removed 'username' field
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'user_type', 'adviser', 'program', 'sr_no')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('email', 'full_name', 'user_type')
    search_fields = ('email', 'full_name')
    ordering = ('email',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('num', 'title', 'department', 'last_reg_date')
    ordering = ('-last_reg_date',)
    search_fields = ('title', 'num', 'department')

class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'participant_type', 'state', 'grade')
    ordering = ('-course__last_reg_date',)
    search_fields = ('user__email', 'course__title', 'course__num')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Participant, ParticipantAdmin)
