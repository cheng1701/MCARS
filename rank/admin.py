from django.contrib import admin
from .models import Genre, Branch, Rank, Theme, RankImage, MemberRank, MemberRankHistory, RankSettings


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'description')
    search_fields = ('name', 'abbreviation')


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ('paygrade', 'short_name', 'long_name', 'order')
    list_filter = ('paygrade',)
    search_fields = ('paygrade', 'short_name', 'long_name')
    ordering = ('order',)


class RankImageInline(admin.TabularInline):
    model = RankImage
    extra = 1


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'genre', 'branch', 'is_active')
    list_filter = ('genre', 'branch', 'is_active')
    search_fields = ('name', 'description')
    inlines = [RankImageInline]


@admin.register(RankImage)
class RankImageAdmin(admin.ModelAdmin):
    list_display = ('rank', 'theme')
    list_filter = ('theme', 'rank')
    search_fields = ('rank__short_name', 'theme__name')


@admin.register(RankSettings)
class RankSettingsAdmin(admin.ModelAdmin):
    list_display = ('default_genre', 'default_branch', 'default_theme', 'default_paygrade')


@admin.register(MemberRank)
class MemberRankAdmin(admin.ModelAdmin):
    list_display = ('member', 'rank', 'preferred_theme', 'effective_date', 'assigned_by')
    list_filter = ('rank', 'preferred_theme', 'effective_date')
    search_fields = ('member__user__first_name', 'member__user__last_name', 'member__user__email')
    raw_id_fields = ('member', 'rank', 'assigned_by')


@admin.register(MemberRankHistory)
class MemberRankHistoryAdmin(admin.ModelAdmin):
    list_display = ('member', 'change_type', 'rank', 'previous_rank', 'theme', 'previous_theme', 'effective_date', 'assigned_by', 'created_at')
    list_filter = ('change_type', 'rank', 'theme', 'effective_date', 'created_at')
    search_fields = ('member__user__first_name', 'member__user__last_name', 'member__user__email', 'notes')
    raw_id_fields = ('member', 'rank', 'previous_rank', 'theme', 'previous_theme', 'assigned_by')
    readonly_fields = ('created_at',)
