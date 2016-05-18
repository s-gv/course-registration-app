from django.conf.urls import url
from . import views

app_name = 'coursereg'
urlpatterns = [
    url(r'^signin/$', views.signin, name='signin'),
    url(r'^signout/$', views.signout, name='signout'),
    url(r'^changepasswd/$', views.change_passwd, name='change_passwd'),
    url(r'^participant/new/$', views.participant_create, name='participant_create'),
    url(r'^participant/delete/$', views.participant_delete, name='participant_delete'),
    url(r'^participant/advisor_act/$', views.participant_advisor_act, name='participant_advisor_act'),
    url(r'^participant/instr_act/$', views.participant_instr_act, name='participant_instr_act'),
    url(r'^student/profile/$', views.student_profile, name='student_profile'),
    url(r'^student/faq/$', views.student_faq, name='student_faq'),
    url(r'^course_page/$', views.course_page, name='course_page'),
    url(r'^$', views.index, name='index'),
    url(r'^user/new/$', views.adduser, name='adduser'), #Added by arthi
]
