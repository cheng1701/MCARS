from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Public calendar alias
    path('public/', views.calendar, name='public_calendar'),
    # Default calendar (inside/manager view also uses this route)
    path('', views.calendar, name='calendar'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/request/', views.request_attendance, name='request_attendance'),
    path('event/create/', views.event_create, name='event_create'),
    path('event/<int:event_id>/edit/', views.event_edit, name='event_edit'),
    path('event/<int:event_id>/delete/', views.event_delete, name='event_delete'),
]
