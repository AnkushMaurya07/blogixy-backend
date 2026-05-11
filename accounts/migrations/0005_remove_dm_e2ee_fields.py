from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_dm_identity_message_e2ee_envelope'),
    ]

    operations = [
        migrations.RemoveField(model_name='user', name='dm_identity_public_key'),
        migrations.RemoveField(model_name='message', name='e2ee_envelope'),
    ]
