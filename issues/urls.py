from django.urls import path

from . import views

urlpatterns = [
    path('reporters/', views.reporters, name='reporters'),
    path('issues/', views.issues, name='issues'),
]
