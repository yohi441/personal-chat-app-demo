from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth import get_user_model
from .models import ChatMessage, last_15_message
from django.shortcuts import get_object_or_404

User = get_user_model()

def users_count(request, users):
    users_count = []
    for user in users:
        data_dict = {}
        if user.id > request.user.id:
            thread_name = f'chat_{user.id}-{request.user.id}'
        else:
            thread_name = f'chat_{request.user.id}-{user.id}'

        count = ChatMessage.objects.filter(sender=user, thread_name=thread_name, unread=True).count()

        data_dict["username"] = user.username
        data_dict["count"] = count
        
        users_count.append(data_dict)
    
    return users_count

class IndexView(View):

    def get(self, request):
        users = User.objects.exclude(username=request.user.username)
  
        context = {
            'users': users,
            'users_count': users_count(request, users),
        }

        return render(request, 'index.html', context)


class PersonalChatView(View):

    def get(self, request, username):
        username = get_object_or_404(User, username=username)
        users = User.objects.exclude(username=request.user.username)
        user = User.objects.get(username=username)

        

        if request.user.id > username.id:
            thread_name = f'chat_{request.user.id}-{username.id}'
        else:
            thread_name = f'chat_{username.id}-{request.user.id}'

        messages = last_15_message(thread_name)

        unread_messages = ChatMessage.objects.filter(sender=user, thread_name=thread_name, unread=True)
        for unread in unread_messages:
            unread.unread = False
            unread.save()
        

        context = {
            'username': username,
            'users': users,
            'user': user,
            'messages': messages,
            'users_count': users_count(request, users)

        }
        return render(request, 'chat.html', context)
