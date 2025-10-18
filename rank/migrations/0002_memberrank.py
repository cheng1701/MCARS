from django.db import migrations


class Migration(migrations.Migration):
    # No-op migration to preserve numbering; actual MemberRank was created in 0001_initial
    dependencies = [
        ('rank', '0002_memberrank_preferred_theme'),
    ]

    operations = []
