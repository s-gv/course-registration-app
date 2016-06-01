from django.conf.urls import url
from . import views

app_name = 'coursereg'
urlpatterns = [
    url(r'^signin/$', views.user.signin, name='signin'),
    url(r'^signout/$', views.user.signout, name='signout'),
    url(r'^changepasswd/$', views.user.change_passwd, name='change_passwd'),

    url(r'^participant/new/$', views.student.participant_create, name='participant_create'),
    url(r'^participant/delete/$', views.student.participant_delete, name='participant_delete'),
    url(r'^student/faq/$', views.student.faq, name='student_faq'),
    url(r'^student/profile/$', views.student.profile, name='student_profile'),

    url(r'^participant/advisor_act/$', views.faculty.participant_advisor_act, name='participant_advisor_act'),
    url(r'^participant/advisor_rej/$', views.faculty.participant_advisor_rej, name='participant_advisor_rej'),

    url(r'^participant/instr_act/$', views.faculty.participant_instr_act, name='participant_instr_act'),
    url(r'^participant/instr_rej/$', views.faculty.participant_instr_rej, name='participant_instr_rej'),

    url(r'^course_page/$', views.faculty.course_page, name='course_page'),
    url(r'^student_details/$', views.faculty.student_details, name='student_details'),

    url(r'^fatal/$', views.misc.fatal_error, name='fatal'),
    url(r'^$', views.misc.index, name='index'),

    url(r'^user/new/$', views.light_admin.adduser, name='adduser'),
]
