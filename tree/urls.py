from django.conf.urls import patterns, url

from tree import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       )
