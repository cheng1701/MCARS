# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Members', '0001_initial'),  # Adjust this to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='profile_images/'),
        ),
    ]
