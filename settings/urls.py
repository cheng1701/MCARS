from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alt'),
    path('roles/', views.manage_roles, name='manage_roles'),
]
