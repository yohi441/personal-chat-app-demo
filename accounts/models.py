from django.db import models

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    updated = models.DateTimeField(auto_now=True)
