from django.urls import path
from . import views

app_name = 'units'

urlpatterns = [
    path('', views.unit_list, name='unit_list'),
    path('org-chart/', views.unit_org_chart, name='unit_org_chart'),
    path('create/', views.unit_create, name='unit_create'),
    path('<int:pk>/', views.unit_detail, name='unit_detail'),
    path('<int:pk>/public/', views.unit_public, name='unit_public'),
    path('<int:pk>/edit/', views.unit_edit, name='unit_edit'),
    path('<int:pk>/add-member/', views.add_member, name='add_member'),
    path('<int:pk>/assign-position/<int:membership_id>/', views.assign_position, name='assign_position'),
    path('<int:pk>/positions/', views.manage_positions, name='manage_positions'),
    path('<int:pk>/change-commander/', views.change_commander, name='change_commander'),
    path('<int:pk>/departments/', views.manage_departments, name='manage_departments'),
    path('<int:pk>/departments/<int:dept_id>/', views.manage_department, name='manage_department'),
]
