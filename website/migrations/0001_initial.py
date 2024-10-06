
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Administrator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.CharField(max_length=45, unique=True)),
                ('password', models.CharField(max_length=45, unique=True)),
            ],
            options={
                'db_table': 'administrator',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AdministratorOperateLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField()),
                ('page', models.CharField(max_length=45)),
                ('operation', models.CharField(max_length=500)),
            ],
            options={
                'db_table': 'administrator_operate_log',
                'managed': False,
            },
        ),
    ]
