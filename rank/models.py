from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import os
import uuid
import datetime


class Genre(models.Model):
    """Genre model to categorize different types of rank systems"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    """Branch model for different military branches"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    abbreviation = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name


class Rank(models.Model):
    """Rank model for military rank information"""
    paygrade = models.CharField(
        max_length=10, 
        unique=True,
        validators=[RegexValidator(regex=r'^[A-Z]-\d+$', message='Paygrade must be in format X-Y (e.g. E-1, O-3)')]
    )
    short_name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(help_text="Order of rank for sorting purposes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Rank'
        verbose_name_plural = 'Ranks'

    def __str__(self):
        return f"{self.paygrade} - {self.short_name}"


class Theme(models.Model):
    """Theme model to store different visual themes for ranks"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name='themes')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='themes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'genre', 'branch']

    def __str__(self):
        return f"{self.name} ({self.genre}/{self.branch})"


class RankImage(models.Model):
    """RankImage model to store images for each rank within a theme"""
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE, related_name='images')
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='rank_images')
    image = models.ImageField(upload_to='rank_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['rank', 'theme']

    def __str__(self):
        return f"{self.rank} - {self.theme}"


class RankSettings(models.Model):
    """Settings model for rank system defaults"""
    default_paygrade = models.ForeignKey(Rank, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_settings')
    default_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_settings')
    default_genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_settings')
    default_theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_settings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rank Settings'
        verbose_name_plural = 'Rank Settings'

    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        if not self.pk and RankSettings.objects.exists():
            # Update existing settings instead of creating a new one
            existing_settings = RankSettings.objects.first()
            existing_settings.default_paygrade = self.default_paygrade
            existing_settings.default_branch = self.default_branch
            existing_settings.default_genre = self.default_genre
            existing_settings.default_theme = self.default_theme
            existing_settings.save()
            return existing_settings
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class MemberRank(models.Model):
    """Bridge model to associate members with ranks"""
    member = models.OneToOneField('Members.Member', on_delete=models.CASCADE, related_name='rank_association')
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE, related_name='member_associations')
    preferred_theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='member_preferences')
    effective_date = models.DateField(default=datetime.date.today)
    notes = models.TextField(blank=True)
    assigned_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='rank_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Member Rank'
        verbose_name_plural = 'Member Ranks'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.member.get_ranked_name()} - {self.rank}"

    def save(self, *args, **kwargs):
        # Check if this is an update to an existing rank
        is_update = self.pk is not None

        # If it's an update, get the old rank and theme before saving
        if is_update:
            try:
                old_instance = MemberRank.objects.get(pk=self.pk)
                old_rank = old_instance.rank
                old_theme = old_instance.preferred_theme

                # Determine what's changing
                rank_changed = old_rank != self.rank
                theme_changed = old_theme != self.preferred_theme

            except MemberRank.DoesNotExist:
                old_rank = None
                old_theme = None
                rank_changed = True
                theme_changed = True
                is_update = False
        else:
            old_rank = None
            old_theme = None
            rank_changed = True
            theme_changed = True

        # Save the instance
        super().save(*args, **kwargs)

        # If there's any change that needs to be tracked
        if not is_update or rank_changed or theme_changed:
            # Determine the change type
            if not is_update:
                change_type = 'initial'
            elif rank_changed and theme_changed:
                change_type = 'both'
            elif rank_changed:
                change_type = 'rank'
            else:  # theme_changed only
                change_type = 'theme'

            # Create history entry
            MemberRankHistory.objects.create(
                member=self.member,
                rank=self.rank,
                previous_rank=old_rank if (is_update and rank_changed) else None,
                theme=self.preferred_theme,
                previous_theme=old_theme if (is_update and theme_changed) else None,
                change_type=change_type,
                effective_date=self.effective_date,
                notes=self.notes,
                assigned_by=self.assigned_by
            )


class MemberRankHistory(models.Model):
    """Model to track the history of rank changes for members"""
    member = models.ForeignKey('Members.Member', on_delete=models.CASCADE, related_name='rank_history')
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE, related_name='rank_history')
    previous_rank = models.ForeignKey(Rank, on_delete=models.SET_NULL, null=True, blank=True, related_name='subsequent_rank_history')
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='theme_history')
    previous_theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='subsequent_theme_history')
    change_type = models.CharField(max_length=20, choices=[
        ('rank', 'Rank Change'),
        ('theme', 'Theme Change'),
        ('both', 'Rank & Theme Change'),
        ('initial', 'Initial Assignment')
    ], default='rank')
    effective_date = models.DateField(default=datetime.date.today)
    notes = models.TextField(blank=True)
    assigned_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='rank_history_assignments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Member Rank History'
        verbose_name_plural = 'Member Rank History'
        ordering = ['-effective_date', '-created_at']

    def __str__(self):
        if self.change_type == 'theme':
            return f"{self.member.get_full_name()} - Theme change: {self.previous_theme or 'None'} → {self.theme or 'None'}"
        else:
            return f"{self.member.get_full_name()} - {self.rank} (from {self.previous_rank or 'None'})"


class ChildRank(models.Model):
    """Bridge model to associate children with ranks"""
    child = models.OneToOneField('Members.Child', on_delete=models.CASCADE, related_name='child_rank_association')
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE, related_name='child_associations')
    preferred_theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='child_preferences')
    effective_date = models.DateField(default=datetime.date.today)
    notes = models.TextField(blank=True)
    assigned_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_rank_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Child Rank'
        verbose_name_plural = 'Child Ranks'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.child.get_ranked_name()} - {self.rank}"

    def save(self, *args, **kwargs):
        # Check if this is an update to an existing rank
        is_update = self.pk is not None

        # If it's an update, get the old rank and theme before saving
        if is_update:
            try:
                old_instance = ChildRank.objects.get(pk=self.pk)
                old_rank = old_instance.rank
                old_theme = old_instance.preferred_theme

                # Determine what's changing
                rank_changed = old_rank != self.rank
                theme_changed = old_theme != self.preferred_theme

            except ChildRank.DoesNotExist:
                old_rank = None
                old_theme = None
                rank_changed = True
                theme_changed = True
                is_update = False
        else:
            old_rank = None
            old_theme = None
            rank_changed = True
            theme_changed = True

        # Save the instance
        super().save(*args, **kwargs)

        # If there's any change that needs to be tracked
        if not is_update or rank_changed or theme_changed:
            # Determine the change type
            if not is_update:
                change_type = 'initial'
            elif rank_changed and theme_changed:
                change_type = 'both'
            elif rank_changed:
                change_type = 'rank'
            else:  # theme_changed only
                change_type = 'theme'

            # Create history entry
            ChildRankHistory.objects.create(
                child=self.child,
                rank=self.rank,
                previous_rank=old_rank if (is_update and rank_changed) else None,
                theme=self.preferred_theme,
                previous_theme=old_theme if (is_update and theme_changed) else None,
                change_type=change_type,
                effective_date=self.effective_date,
                notes=self.notes,
                assigned_by=self.assigned_by
            )


class ChildRankHistory(models.Model):
    """Model to track the history of rank changes for children"""
    child = models.ForeignKey('Members.Child', on_delete=models.CASCADE, related_name='rank_history')
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE, related_name='child_rank_history')
    previous_rank = models.ForeignKey(Rank, on_delete=models.SET_NULL, null=True, blank=True, related_name='subsequent_child_rank_history')
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='child_theme_history')
    previous_theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True, related_name='subsequent_child_theme_history')
    change_type = models.CharField(max_length=20, choices=[
        ('rank', 'Rank Change'),
        ('theme', 'Theme Change'),
        ('both', 'Rank & Theme Change'),
        ('initial', 'Initial Assignment')
    ], default='rank')
    effective_date = models.DateField(default=datetime.date.today)
    notes = models.TextField(blank=True)
    assigned_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_rank_history_assignments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Child Rank History'
        verbose_name_plural = 'Child Rank History'
        ordering = ['-effective_date', '-created_at']

    def __str__(self):
        if self.change_type == 'theme':
            return f"{self.child.get_full_name()} - Theme change: {self.previous_theme or 'None'} → {self.theme or 'None'}"
        else:
            return f"{self.child.get_full_name()} - {self.rank} (from {self.previous_rank or 'None'})"
