from django.conf.urls import url
from . import views

app_name = 'coursereg'
urlpatterns = [
    url(r'^signin/$', views.signin, name='signin'),
    url(r'^signout/$', views.signout, name='signout'),
    url(r'^participant/new/$', views.participant_create, name='participant_create'),
    url(r'^participant/delete/$', views.participant_delete, name='participant_delete'),
    url(r'^$', views.index, name='index'),
]
