# Generated manually to fix missing fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_notificationsettings_quiet_hours_enabled_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationsettings',
            name='weekdays_only',
            field=models.BooleanField(default=False, verbose_name='Только по будням'),
        ),
        migrations.AddField(
            model_name='notificationsettings',
            name='weekend_only',
            field=models.BooleanField(default=False, verbose_name='Только по выходным'),
        ),
    ]