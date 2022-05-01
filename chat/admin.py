from django.contrib import admin

from .models import Profile, ChatMessage, Thread


admin.site.register(Profile)
admin.site.register(ChatMessage)
admin.site.register(Thread)
