# Generated manually

from django.db import migrations, models
import Members.validators


class Migration(migrations.Migration):

    dependencies = [
        ('Members', '0001_initial'),  # Update this to your latest migration
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='profile_image',
            field=models.ImageField(blank=True, help_text='Upload a profile image (JPG, PNG, or GIF, max 5MB)', null=True, upload_to='profile_images/', validators=[Members.validators.validate_image_extension, Members.validators.validate_image_size]),
        ),
    ]
