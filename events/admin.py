from django.contrib import admin
from .models import Event, EventAttendee


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'host', 'start_datetime', 'end_datetime')
    list_filter = ('unit', 'visibility_scope', 'start_datetime')
    search_fields = ('title', 'description')


@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ('event', 'member', 'status')
    list_filter = ('status',)
    search_fields = ('event__title', 'member__user__first_name', 'member__user__last_name')
