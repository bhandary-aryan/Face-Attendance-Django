from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('admin', '0003_logentry_add_action_flag_choices'),
        ('authentication', '0001_initial'),  
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            -- Drop the existing constraint
            ALTER TABLE django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_user_id_c564eba6_fk_auth_user_id;
            -- Add new constraint referencing the custom user model
            ALTER TABLE django_admin_log ADD CONSTRAINT django_admin_log_user_id_custom_fk 
            FOREIGN KEY (user_id) REFERENCES authentication_user(id) DEFERRABLE INITIALLY DEFERRED;
            ''',
            reverse_sql='''
            -- This is a no-op in reverse as we don't want to restore the old constraint
            '''
        ),
    ]