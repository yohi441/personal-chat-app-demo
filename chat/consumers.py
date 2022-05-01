import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model


from .models import ChatMessage, Profile, Thread

User = get_user_model()


class IndexConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def new_message_count(self, data):
        count = ChatMessage.objects.filter(
            thread_name=data, unread=True).count()
        return count

    @database_sync_to_async
    def is_view(self, user_id, name):
        user = User.objects.get(pk=user_id)
        thread = Thread.objects.filter(user=user, name=name).get()
        return thread.is_view

    @database_sync_to_async
    def update_unread_messages(self, name):
        messages = ChatMessage.objects.filter(thread_name=name, unread=True)
        for i in messages:
            i.unread = False
            i.save()
        return messages

    @database_sync_to_async
    def is_online(self, user_id):
        user = User.objects.get(pk=user_id)
        return user.profile.is_online

    async def connect(self):
        await self.change_online_status(1)
        user_id = self.scope['url_route']['kwargs']['id']
        self.room_group_name = 'index'
        profile = await self.is_online(user_id)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_online_status',
                'message': str(profile),
                'user_id': user_id
            }
        )

    async def disconnect(self, code):
        await self.change_online_status(-1)
        user_id = self.scope['url_route']['kwargs']['id']

        profile = await self.is_online(user_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_online_status',
                'message': str(profile),
                'user_id': user_id
            }
        )
        return await super().disconnect(code)

    async def send_online_status(self, event):
        # Send message to WebSocket
        message = event['message']
        user_id = event['user_id']
        await self.send(text_data=json.dumps({
            'message': message,
            'user_id': user_id,

        }))

    @database_sync_to_async
    def change_online_status(self, data):
        my_id = self.scope['user'].id
        user = User.objects.get(pk=my_id)
        profile = Profile.objects.get(user=user)
        profile.online_status_count += int(data)
        profile.save()


class ChatConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_or_create_thread_model(self, name, user_id):
        user = User.objects.get(pk=user_id)
        try:
            thread = Thread.objects.get(name=name, user=user)
            return True
        except ObjectDoesNotExist:
            thread = Thread.objects.create(name=name, user=user)
            return thread

    @database_sync_to_async
    def update_view_count(self, user_id, name, operation):
        user = User.objects.get(pk=user_id)
        thread = Thread.objects.filter(user=user, name=name).get()
        if operation == "increase":
            thread.view_count += 1
        else:
            thread.view_count -= 1

        thread.save()

        return thread.view_count

    async def connect(self):
        my_id = self.scope['user'].id
        other_user_id = self.scope['url_route']['kwargs']['id']

        if int(my_id) > int(other_user_id):
            self.room_name = f'{my_id}-{other_user_id}'
        else:
            self.room_name = f'{other_user_id}-{my_id}'

        self.room_group_name = 'chat_%s' % self.room_name

        await self.get_or_create_thread_model(self.room_group_name, my_id)
        await self.update_view_count(my_id, self.room_group_name, "increase")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        my_id = self.scope["user"].id

        await self.update_view_count(my_id, self.room_group_name, "decrease")

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):

        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        other_user_id = text_data_json['id']

        await self.save_message(int(self.scope['user'].id), self.room_group_name, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'other_user_id': other_user_id,
                'thread_name': self.room_group_name

            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        other_user_id = event['other_user_id']
        thread_name = event['thread_name']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'other_user_id': other_user_id,
            'thread_name': thread_name
        }))

    @database_sync_to_async
    def save_message(self, sender, thread_name, message):
        user = User.objects.get(pk=sender)
        ChatMessage.objects.create(
            sender=user, thread_name=thread_name, message=message)
