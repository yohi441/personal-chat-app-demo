# Generated by Django 3.2.13 on 2022-05-11 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_thread'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='current_city',
            field=models.CharField(blank=True, max_length=225, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='education',
            field=models.CharField(blank=True, max_length=225, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='workplace',
            field=models.CharField(blank=True, max_length=225, null=True),
        ),
    ]