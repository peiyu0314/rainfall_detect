from django.db import models


# Create your models here.

class Administrator(models.Model):
    account = models.CharField(unique=True, max_length=45)
    password = models.CharField(unique=True, max_length=45)

    class Meta:
        managed = False
        db_table = 'administrator'


class AdministratorOperateLog(models.Model):
    administrator = models.ForeignKey(Administrator, models.DO_NOTHING)
    time = models.DateTimeField()
    page = models.CharField(max_length=45)
    operation = models.CharField(max_length=500)

    class Meta:
        managed = False
        db_table = 'administrator_operate_log'
