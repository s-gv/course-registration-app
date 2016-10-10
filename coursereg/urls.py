from django.conf.urls import url, include
from . import views

app_name = 'coursereg'
urlpatterns = [
    url(r'^signin$', views.user.signin, name='signin'),
    url(r'^signout$', views.user.signout, name='signout'),
    url(r'^changepasswd$', views.user.change_passwd, name='change_passwd'),
    url(r'^forgotpasswd$', views.user.forgot_passwd, name='forgot_passwd'),
    url(r'^resetpasswd/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$', views.user.reset_passwd, name='reset_passwd'),

    url(r'^faq$', views.common.faq, name='faq'),
    url(r'^fatal$', views.common.fatal_error, name='fatal'),
    url(r'^profile$', views.common.profile, name='profile'),
    url(r'^$', views.common.index, name='index'),

    url(r'^participants/create$', views.participants.create, name='participants_create'),
    url(r'^participants/([0-9]+)/update$', views.participants.update, name='participants_update'),
    url(r'^participants/([0-9]+)/delete$', views.participants.delete, name='participants_delete'),

    url(r'^notifications/dismiss$', views.notifications.dismiss, name='notifications_dismiss'),
    url(r'^notifications/create$', views.notifications.notify, name='notify'),

    url(r'^instructor$', views.instructor.index, name='instructor'),
    url(r'^instructor/([0-9]+)$', views.instructor.detail, name='instructor_detail'),
    url(r'^instructor/new$', views.instructor.course_new, name='instructor_new_course'),
    url(r'^instructor/([0-9]+)/update$', views.instructor.course_update, name='instructor_update_course'),

    url(r'^adviser$', views.adviser.index, name='adviser'),
    url(r'^adviser/([0-9]+)$', views.adviser.detail, name='adviser_detail'),

    url(r'^dcc/report$', views.dcc.report, name='dcc_report'),
    url(r'^dcc/review$', views.dcc.review, name='dcc_review'),
    url(r'^dcc/([0-9]+)$', views.dcc.detail, name='dcc_detail'),
    url(r'^dcc/([0-9]+)/approve$', views.dcc.approve, name='dcc_approve'),
    url(r'^dcc/remind$', views.dcc.remind, name='dcc_remind'),
]
