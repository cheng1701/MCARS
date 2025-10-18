from django.db import migrations, models
import django.utils.timezone
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Members', '0007_child_child_id_child_created_at_child_profile_image_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('hull', models.CharField(blank=True, default='', max_length=50)),
                ('type', models.CharField(choices=[('FLEET_COMMANDER', 'Fleet Commander'), ('HEADQUARTERS', 'Headquarters'), ('QUADRANT', 'Quadrant'), ('SECTOR', 'Sector'), ('SHIP', 'Ship'), ('SHUTTLE', 'Shuttle')], max_length=32)),
                ('street_address', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('zip_code', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(blank=True, default='', max_length=100)),
                ('phone_number', models.CharField(blank=True, max_length=50)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('image', models.ImageField(blank=True, null=True, upload_to='unit_images/')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('commanding_officer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='units_commanded', to='Members.member')),
            ],
            options={
                'ordering': ['type', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('max_members', models.PositiveIntegerField(default=1)),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='units.unit')),
            ],
            options={
                'ordering': ['order', 'name'],
                'unique_together': {('unit', 'name')},
            },
        ),
        migrations.AddField(
            model_name='unit',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='units.unit'),
        ),
        migrations.CreateModel(
            name='UnitMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('joined_date', models.DateField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unit_memberships', to='Members.member')),
                ('position', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='memberships', to='units.position')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='units.unit')),
            ],
            options={
                'ordering': ['-joined_date'],
                'unique_together': {('unit', 'member', 'is_active')},
            },
        ),
    ]
