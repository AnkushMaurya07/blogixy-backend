from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_message_deleted_at_message_edited_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='dm_identity_public_key',
            field=models.CharField(
                blank=True,
                default='',
                max_length=128,
                help_text='Base64-encoded X25519 public key for optional client-side DM encryption.',
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='e2ee_envelope',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
