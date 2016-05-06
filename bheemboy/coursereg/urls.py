from django.conf.urls import url
from . import views

app_name = 'coursereg'
urlpatterns = [
    url(r'^signin/$', views.signin, name='signin'),
    url(r'^signout/$', views.signout, name='signout'),
    url(r'^$', views.index, name='index'),
]
