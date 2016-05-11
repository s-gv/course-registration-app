from django.conf.urls import url
from . import views

app_name = 'coursereg'
urlpatterns = [
    url(r'^signin/$', views.signin, name='signin'),
    url(r'^signout/$', views.signout, name='signout'),
    url(r'^participant/new/$', views.participant_create, name='participant_create'),
    url(r'^participant/delete/$', views.participant_delete, name='participant_delete'),
    url(r'^participant/advisor_act/$', views.participant_advisor_act, name='participant_advisor_act'),
    url(r'^participant/instr_act/$', views.participant_instr_act, name='participant_instr_act'),
    url(r'^course_page/$', views.course_page, name='course_page'),
    url(r'^fatal/$', views.fatal_error, name='fatal_error'),
    url(r'^$', views.index, name='index'),
]
