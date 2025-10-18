from django.contrib import admin
from .models import Unit, Position, UnitMembership


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'hull', 'type', 'commanding_officer', 'parent')
    list_filter = ('type',)
    search_fields = ('name', 'hull')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'order', 'max_members')
    list_filter = ('unit',)
    search_fields = ('name',)


@admin.register(UnitMembership)
class UnitMembershipAdmin(admin.ModelAdmin):
    list_display = ('unit', 'member', 'position', 'is_active', 'joined_date')
    list_filter = ('unit', 'is_active')
    search_fields = ('member__user__username', 'member__user__first_name', 'member__user__last_name')
