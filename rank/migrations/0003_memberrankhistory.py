from django.db import migrations


class Migration(migrations.Migration):
    # No-op migration to preserve numbering; MemberRankHistory is created later in 0009
    dependencies = [
        ('rank', '0002_memberrank_preferred_theme'),
    ]

    operations = []
