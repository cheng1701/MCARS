#!/usr/bin/env python
"""
Script to create the Chapter Manager group and assign permissions.
Run this after creating the chapter app and running migrations.

Usage:
python manage.py shell < scripts/create_chapter_manager_group.py
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from chapter.models import Chapter, Position, ChapterMembership

# Create Chapter Manager group
chapter_manager_group, created = Group.objects.get_or_create(name='chapter_manager')

if created:
    print("Created 'chapter_manager' group")
else:
    print("'chapter_manager' group already exists")

# Get content types for chapter models
chapter_ct = ContentType.objects.get_for_model(Chapter)
position_ct = ContentType.objects.get_for_model(Position)
membership_ct = ContentType.objects.get_for_model(ChapterMembership)

# Define permissions for chapter managers
permissions_to_add = [
    # Chapter permissions
    Permission.objects.get(content_type=chapter_ct, codename='add_chapter'),
    Permission.objects.get(content_type=chapter_ct, codename='change_chapter'),
    Permission.objects.get(content_type=chapter_ct, codename='delete_chapter'),
    Permission.objects.get(content_type=chapter_ct, codename='view_chapter'),

    # Position permissions
    Permission.objects.get(content_type=position_ct, codename='add_position'),
    Permission.objects.get(content_type=position_ct, codename='change_position'),
    Permission.objects.get(content_type=position_ct, codename='delete_position'),
    Permission.objects.get(content_type=position_ct, codename='view_position'),

    # Membership permissions
    Permission.objects.get(content_type=membership_ct, codename='add_chaptermembership'),
    Permission.objects.get(content_type=membership_ct, codename='change_chaptermembership'),
    Permission.objects.get(content_type=membership_ct, codename='delete_chaptermembership'),
    Permission.objects.get(content_type=membership_ct, codename='view_chaptermembership'),
]

# Add permissions to the group
for permission in permissions_to_add:
    chapter_manager_group.permissions.add(permission)

print(f"Added {len(permissions_to_add)} permissions to chapter_manager group")

# Print instructions for adding users to the group
print("\nTo add users to the chapter_manager group:")
print("1. Go to Django Admin")
print("2. Navigate to Users")
print("3. Select a user and edit")
print("4. In the 'Groups' section, add 'chapter_manager'")
print("5. Save the user")

print("\nSetup complete!")
