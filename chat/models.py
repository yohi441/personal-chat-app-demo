from asyncio import FastChildWatcher
from distutils.command.upload import upload
from email.policy import default
from sqlite3 import Timestamp
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(
        upload_to="avatar/", default="avatar/default.png")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    online_status_count = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

    @property
    def is_online(self):
        if self.online_status_count:
            return True
        return False

class Thread(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    view_count = models.IntegerField(default=0)


    def __str__(self):
        return f"{self.user.username}-{self.name}" 

    @property
    def is_view(self):
        if self.view_count:
            return True
        return False


class ChatMessage(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    thread_name = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    unread = models.BooleanField(default=True)

    def __str__(self):
        return self.message


def last_15_message(thread_name):
    messages = ChatMessage.objects.order_by(
        '-timestamp').filter(thread_name=thread_name)[:10]
    return messages
