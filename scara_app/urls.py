# scara_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.interface_view, name='interface'),
]