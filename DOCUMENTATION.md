# Documentation

This document serves as a technical reference for the Personal Chat App Demo. It explains how each feature is implemented, where the relevant code lives, and how the pieces fit together. Update this file whenever you add or change features.

---

## Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [Custom User Model](#2-custom-user-model)
3. [Authentication (django-allauth)](#3-authentication-django-allauth)
4. [User Profiles](#4-user-profiles)
5. [Real-Time Online Status](#5-real-time-online-status)
6. [Private Chat & WebSocket Messaging](#6-private-chat--websocket-messaging)
7. [Unread Message Counts](#7-unread-message-counts)
8. [HTMX Inline Profile Editing](#8-htmx-inline-profile-editing)
9. [Serving the App (ASGI / Daphne)](#9-serving-the-app-asgi--daphne)
10. [Channel Layers](#10-channel-layers)
11. [Static Files & Media (Cloudinary)](#11-static-files--media-cloudinary)
12. [URL Structure](#12-url-structure)
13. [Templates Overview](#13-templates-overview)

---

## 1. Project Architecture

### Stack

| Layer        | Technology                                         |
|-------------|----------------------------------------------------|
| Framework   | Django 3.2.13                                      |
| ASGI Server | Daphne 3.0.2                                       |
| Real-Time   | Django Channels 3.0.4, channels-redis 3.4.0        |
| Database    | SQLite (dev), PostgreSQL (prod)                    |
| Auth        | django-allauth 0.50.0 (email-based)                |
| Frontend    | Tailwind CSS 3, Alpine.js 3.10.2, HTMX 1.7.0      |
| Media       | Cloudinary (via django-cloudinary-storage)         |
| Config      | python-decouple 3.6                                |

### Directory Layout

```
mysite/                          # Django project package
  settings.py                    # All settings
  urls.py                        # Root URL config
  asgi.py                        # ASGI entry point (Channels routing)
  wsgi.py                        # WSGI entry point

accounts/                        # Custom user app
  models.py                      # User(AbstractUser) with `updated` field
  forms.py                       # CustomUserCreationForm
  admin.py                       # User admin registration

chat/                            # Main chat application
  models.py                      # Profile, Thread, ChatMessage
  views.py                       # IndexView, PersonalChatView, ProfileView, edit views
  views_htmx.py                  # HTMX partial view functions
  urls.py                        # URL patterns (normal + htmx)
  consumers.py                   # WebSocket consumers
  routing.py                     # WebSocket URL routing
  forms.py                       # AvatarForm, UsernameForm
  signals.py                     # Auto-create Profile on User creation
  apps.py                        # AppConfig, imports signals in ready()

templates/                       # All Django templates
static/                          # CSS, JS, vendor libs
```

---

## 2. Custom User Model

**File:** `accounts/models.py`

```python
class User(AbstractUser):
    updated = models.DateTimeField(auto_now=True)
```

- Replaces the default Django `User` model.
- Adds an `updated` timestamp that refreshes on every save.
- Must be set in `settings.py` before the first migration:

```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'
```

The custom `UserCreationForm` in `accounts/forms.py` extends Django's built-in form to include the `updated` field.

---

## 3. Authentication (django-allauth)

**File:** `mysite/settings.py` (lines 36-39, 197-216)

### Configuration

```python
INSTALLED_APPS = [
    ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = None
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = None
LOGIN_REDIRECT_URL = '/index/'
```

### Key Decisions

- **Email-based login** — users log in with their email, not username (`ACCOUNT_AUTHENTICATION_METHOD = "email"`).
- **No email verification** in development — `ACCOUNT_EMAIL_VERIFICATION = None`. Change to `"mandatory"` in production.
- **Login redirects** to `/index/` (the user list page).
- In `DEBUG` mode, emails print to console via `django.core.mail.backends.console.EmailBackend`.

### Templates

allauth templates are overridden in `templates/account/` (login, signup, logout, password reset, email confirmation, etc.).

### URL

```python
# mysite/urls.py
path('accounts/', include('allauth.urls')),
```

---

## 4. User Profiles

**File:** `chat/models.py` (class `Profile`)

### Model

```python
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to="avatar/", null=True, blank=True)
    bio = models.TextField(max_length=1000, null=True, blank=True)
    current_city = models.CharField(max_length=225, null=True, blank=True)
    workplace = models.CharField(max_length=225, null=True, blank=True)
    education = models.CharField(max_length=225, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    online_status_count = models.IntegerField(default=0)

    @property
    def is_online(self):
        return bool(self.online_status_count)
```

### Auto-Creation via Signal

**File:** `chat/signals.py`

```python
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
```

The signal is imported in `chat/apps.py`:

```python
class ChatConfig(AppConfig):
    def ready(self):
        import chat.signals
```

### Profile View

**File:** `chat/views.py` (class `ProfileView`)

Renders `profile.html` with the user's profile data. Only the logged-in user can edit their own profile fields (gated by `{% if user.username == request.user.username %}` in the template).

---

## 5. Real-Time Online Status

### Overview

Each user opens a persistent WebSocket connection (`ws/<user_id>/`) when they load any page. The `IndexConsumer` tracks how many browser tabs/windows each user has open via `online_status_count`. When this count goes from 0 to 1, the user appears online. When it drops to 0 (all tabs closed), they appear offline.

### WebSocket URL

**File:** `chat/routing.py`

```python
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/(?P<id>\d+)/$', consumers.IndexConsumer.as_asgi()),
]
```

### Consumer — `IndexConsumer`

**File:** `chat/consumers.py` (class `IndexConsumer`)

```python
class IndexConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.change_online_status(1)    # +1 on connect
        user_id = self.scope['url_route']['kwargs']['id']
        self.room_group_name = 'index'
        profile = await self.is_online(user_id)

        await self.channel_layer.group_add('index', self.channel_name)
        await self.accept()
        await self.channel_layer.group_send('index', {
            'type': 'send_online_status',
            'message': str(profile),
            'user_id': user_id
        })

    async def disconnect(self, code):
        await self.change_online_status(-1)   # -1 on disconnect
        user_id = self.scope['url_route']['kwargs']['id']
        profile = await self.is_online(user_id)
        await self.channel_layer.group_send('index', {
            'type': 'send_online_status',
            'message': str(profile),
            'user_id': user_id
        })
        return await super().disconnect(code)

    async def send_online_status(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user_id': event['user_id'],
        }))

    @database_sync_to_async
    def change_online_status(self, data):
        profile = Profile.objects.get(user=self.scope['user'])
        profile.online_status_count += int(data)
        profile.save()
```

### Client-Side — `online-status.js`

**File:** `static/js/online-status.js`

```javascript
const online_user_id = document.getElementById("online-user-id").textContent;
const url2 = `ws://${window.location.host}/ws/${online_user_id}/`;
const wSocket = new WebSocket(url2);

wSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    const status_id = data.user_id;
    const status = document.querySelector("#status" + CSS.escape(status_id));
    if (data.message === "True") {
        status.classList.remove("bg-gray-500");
        status.classList.add("bg-green-500");
    }
    if (data.message === "False") {
        status.classList.remove("bg-green-500");
        status.classList.add("bg-gray-500");
    }
};
```

### Template Integration

In `leftpane.html`, each user has a status dot:

```html
<p id="status{{user.id}}"
   class="{% if user.profile.is_online %}bg-green-500{% else %}bg-gray-500{% endif %}
          absolute p-1.5 rounded-full z-10 border-white border-2">
</p>
```

The `online-user-id` hidden element is rendered in `base_main.html` so every page connects:

```html
<p id="online-user-id" class="hidden">{{request.user.id}}</p>
```

### How It Works Step-by-Step

1. Page loads → `online-status.js` connects to `ws/<user_id>/`
2. `IndexConsumer.connect()` increments `online_status_count` by 1
3. If count > 0, `is_online` returns `True`, broadcast to `index` group
4. All connected clients receive the status update and toggle the CSS class on the status dot
5. On page close, `disconnect()` decrements the count and broadcasts the new status

---

## 6. Private Chat & WebSocket Messaging

### Overview

When a user clicks on another user in the list, they open a private chat room. The room name is deterministic: `chat_{smaller_id}-{larger_id}`. Both users connect to the same room and send/receive messages in real time.

### URL

```python
path('chat/<str:username>/', views.PersonalChatView.as_view(), name='chat'),
```

### View — `PersonalChatView`

**File:** `chat/views.py` (class `PersonalChatView`)

```python
class PersonalChatView(LoginRequiredMixin, View):
    template_name = 'chat.html'

    def get(self, request, username):
        username = get_object_or_404(User, username=username)
        users = User.objects.filter(is_superuser=False).exclude(username=request.user.username)
        user = User.objects.get(username=username)

        # Deterministic thread name
        if request.user.id > username.id:
            thread_name = f'chat_{request.user.id}-{username.id}'
        else:
            thread_name = f'chat_{username.id}-{request.user.id}'

        messages = last_15_message(thread_name)   # last 10 messages

        # Mark unread messages as read
        unread_messages = ChatMessage.objects.filter(sender=user, thread_name=thread_name, unread=True)
        for unread in unread_messages:
            unread.unread = False
            unread.save()

        context = {
            'username': username, 'users': users, 'user': user,
            'messages': messages, 'users_count': users_count(request, users)
        }
        return render(request, self.template_name, context)
```

The view also marks all messages from the other user in this thread as read when the chat is opened.

### WebSocket URL

```python
re_path(r'ws/chat/(?P<id>\d+)/$', consumers.ChatConsumer.as_asgi()),
```

The `id` parameter is the **other user's** ID. The room name is computed as `chat_{my_id}-{other_id}` or `chat_{other_id}-{my_id}` (always smaller first).

### Consumer — `ChatConsumer`

**File:** `chat/consumers.py` (class `ChatConsumer`)

```python
class ChatConsumer(AsyncWebsocketConsumer):

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
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        my_id = self.scope["user"].id
        await self.update_view_count(my_id, self.room_group_name, "decrease")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        other_user_id = text_data_json['id']

        await self.save_message(int(self.scope['user'].id), self.room_group_name, message)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': message,
            'other_user_id': other_user_id,
            'thread_name': self.room_group_name
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'other_user_id': event['other_user_id'],
            'thread_name': event['thread_name']
        }))

    @database_sync_to_async
    def save_message(self, sender, thread_name, message):
        user = User.objects.get(pk=sender)
        ChatMessage.objects.create(sender=user, thread_name=thread_name, message=message)
```

### Client-Side — `chat.js`

**File:** `static/js/chat.js`

```javascript
const id = JSON.parse(document.getElementById("username-id").textContent);
const userAvatar = document.getElementById("user-avatar").textContent;
const url = `ws://${window.location.host}/ws/chat/${id}/`;
const chatSocket = new WebSocket(url);

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    // Build message bubble — right-aligned (own) or left-aligned (other)
    if (data.other_user_id === id) {
        // Own message — right aligned
    } else {
        // Other's message — left aligned with avatar
    }
    ul.appendChild(li);
};

document.getElementById("chat-message-input").onkeyup = (e) => {
    if (e.keyCode === 13) { message(); }
};

function message() {
    const message = document.getElementById("chat-message-input");
    if (message.value.trim() !== "") {
        chatSocket.send(JSON.stringify({ message: message.value, id: id }));
    }
    message.value = "";
}
```

The `username-id` is injected into the page via Django's `json_script` template tag in `base_main.html`:

```html
{{ username.id|json_script:'username-id'}}
```

### Message Model

**File:** `chat/models.py` (class `ChatMessage`)

```python
class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    thread_name = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    unread = models.BooleanField(default=True)

def last_15_message(thread_name):
    messages = ChatMessage.objects.order_by('-timestamp').filter(thread_name=thread_name)[:10]
    return messages
```

### Thread Model

**File:** `chat/models.py` (class `Thread`)

```python
class Thread(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)      # e.g. chat_3-7
    view_count = models.IntegerField(default=0)

    @property
    def is_view(self):
        return bool(self.view_count)
```

Tracks how many tabs have the chat open. Used to know whether a user is currently viewing a conversation.

---

## 7. Unread Message Counts

**File:** `chat/views.py` (function `users_count`)

```python
def users_count(request, users):
    users_count = []
    for user in users:
        if user.id > request.user.id:
            thread_name = f'chat_{user.id}-{request.user.id}'
        else:
            thread_name = f'chat_{request.user.id}-{user.id}'

        count = ChatMessage.objects.filter(sender=user, thread_name=thread_name, unread=True).count()

        users_count.append({"username": user.username, "count": count})

    return users_count
```

This function is called in every view that renders `leftpane.html`. It counts unread messages from each user in their respective thread and passes the counts to the template.

In `leftpane.html`, the count badge is shown:

```html
{% for user_count in users_count %}
    {% if user.username == user_count.username and user_count.count > 0 %}
        <p class="absolute z-20 px-2 py-1 text-xs font-semibold text-white bg-red-600 border-4 border-white rounded-full -right-1 -top-2">
            {{ user_count.count }}
        </p>
    {% endif %}
{% endfor %}
```

When the user opens a chat (`PersonalChatView`), all unread messages from the other user in that thread are marked as read:

```python
unread_messages = ChatMessage.objects.filter(sender=user, thread_name=thread_name, unread=True)
for unread in unread_messages:
    unread.unread = False
    unread.save()
```

---

## 8. HTMX Inline Profile Editing

### Overview

Profile fields (avatar, bio, username, current city, workplace, education) are editable inline using HTMX partial swaps. The pattern for each field:

1. **Display state:** Shows the current value with an edit button
2. **Edit state:** HTMX replaces the display element with a form
3. **Submit:** Form POSTs to a Django view that saves and returns the display partial
4. **Cancel:** HTMX replaces the form with the original display partial

### URL Patterns

**File:** `chat/urls.py`

Two sets of URL patterns:
- **htmx_urlpatterns** — for GETting partials (edit buttons, cancel buttons)
- **main urlpatterns** — for POSTing form submissions

They are concatenated:

```python
urlpatterns += htmx_urlpatterns
```

### HTMX View Functions

**File:** `chat/views_htmx.py`

All HTMX views follow the same pattern:

```python
@login_required
def htmx_edit_bio(request):
    if request.htmx:
        return render(request, 'partials/bioform.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))
```

The `django_htmx` middleware (`HtmxMiddleware`) adds `request.htmx` which is `True` when the request comes from HTMX.

### Save Views

**File:** `chat/views.py`

Edit views inherit from `EditAvatar` (which provides the `get` redirect) and override `post`. Example:

```python
class EditWorkplace(EditAvatar):
    def post(self, request, username):
        profile = profile_instance(username)
        workplace = request.POST.get('workplace')
        profile.workplace = workplace
        profile.save()
        return render(request, 'partials/workplace_cancel.html')
```

Each save view returns the "cancel" partial (which renders the updated value in display mode) so HTMX swaps it back in.

### HTMX Partial Template Pattern

Each editable field has two partials:
- **`<field>.html`** — the edit form
- **`<field>_cancel.html`** — the display state (returned after save or cancel)

Example — `partials/current_city.html` (edit form):

```html
<form hx-post="{% url 'chat:current_city' username=user.username %}"
      hx-swap="innerHTML" hx-target="#current-city">
    <input name="current_city" type="text" placeholder="{{user.profile.current_city|title}}">
    <button type="submit">Submit</button>
</form>
```

Example — `partials/current_city_cancel.html` (display):

```html
<p>{{user.profile.current_city|title}}</p>
```

### Special Cases

- **Bio (large):** Uses `hx-swap-oob="true"` in `bioform_cancel.html` to update both the large bio panel and the small bio panel simultaneously.
- **Username:** Uses Django `UsernameForm` for validation; errors are rendered in `partials/username_edit.html`.
- **Avatar:** Uses `enctype="multipart/form-data"` and Django `AvatarForm` (a ModelForm with only the `avatar` field).

### Alpine.js Integration

Alpine.js manages button state (show/hide edit/cancel buttons). Each field uses:

```html
<div x-data="{edit:true, cancel:false}" x-on:current-city.window="edit=true, cancel=false">
```

When the user clicks edit, `edit=false, cancel=true` hides the edit button and shows the cancel button. When the form is submitted or cancelled, a custom event (`$dispatch('current-city')`) resets the state.

---

## 9. Serving the App (ASGI / Daphne)

**File:** `Procfile`

```
web: daphne -p $PORT -b 0.0.0.0 mysite.asgi:application
```

**File:** `mysite/asgi.py`

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
```

- HTTP requests go through Django's standard ASGI handler.
- WebSocket requests go through `AuthMiddlewareStack` (provides `self.scope['user']`) and then through the chat routing.
- Daphne is the production ASGI server. For development, you can use `python manage.py runserver` (HTTP only) or `daphne -p 8000 mysite.asgi:application` (full WebSocket support).

---

## 10. Channel Layers

**File:** `mysite/settings.py`

```python
ASGI_APPLICATION = 'mysite.asgi.application'

if DEBUG:
    CHANNEL_LAYERS = {
        "default": { "BACKEND": "channels.layers.InMemoryChannelLayer" }
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': { "hosts": [('127.0.0.1', 6379)] },
        },
    }
```

- **Development:** Uses in-memory channel layer — no Redis required.
- **Production:** Uses Redis as the channel layer backend for scaling across multiple worker processes.

---

## 11. Static Files & Media (Cloudinary)

### Static Files

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

- Whitenoise serves static files in production.
- Run `python manage.py collectstatic` to collect static files into `staticfiles/`.

### Media (Cloudinary)

```python
# settings.py
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUD_NAME'),
    'API_KEY': config('API_KEY'),
    'API_SECRET': config('API_SECRET'),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

- All uploaded images (avatars) are stored on Cloudinary.
- `django-cloudinary-storage` handles the upload transparently.

---

## 12. URL Structure

**File:** `mysite/urls.py`

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chat.urls')),
    path('accounts/', include('allauth.urls')),
]
```

**File:** `chat/urls.py`

| URL Pattern | View | Name | Method |
|---|---|---|---|
| `/` | `redirectionView` | — | GET |
| `/index/` | `IndexView` | `chat:index` | GET |
| `/chat/<username>/` | `PersonalChatView` | `chat:chat` | GET |
| `/profile/<username>/` | `ProfileView` | `chat:profile` | GET |
| `/edit/bio/<username>` | `edit_bio` | `chat:edit_bio` | POST |
| `/edit/bio_small/<username>` | `edit_bio_small` | `chat:edit_bio_small` | POST |
| `/edit/current_city/<username>` | `edit_current_city` | `chat:current_city` | POST |
| `ws/<id>/` | `IndexConsumer` | — | WebSocket |
| `ws/chat/<id>/` | `ChatConsumer` | — | WebSocket |

### HTMX-Specific URL Patterns

| URL Pattern | View | Name |
|---|---|---|
| `/edit_bio/` | `htmx_edit_bio` | `chat:htmx_edit_bio` |
| `/edit_bio_cancel` | `htmx_edit_bio_cancel` | `chat:htmx_edit_bio_cancel` |
| `/edit/avatar/` | `htmx_request_avatar` | `chat:htmx_edit_avatar` |
| `/edit/avatar_cancel/` | `htmx_avatar_cancel` | `chat:htmx_avatar_cancel` |
| `/edit/username/` | `htmx_edit_username` | `chat:htmx_edit_username` |
| `/edit/username_cancel/` | `htmx_edit_username_cancel` | `chat:htmx_edit_username_cancel` |
| `/edit/bio_small/` | `htmx_edit_bio_small` | `chat:htmx_edit_bio_small` |
| `/edit/bio_small_cancel/` | `htmx_edit_bio_small_cancel` | `chat:htmx_edit_bio_small_cancel` |
| `/edit/current_city/` | `htmx_edit_current_city` | `chat:htmx_edit_current_city` |
| `/edit/current_city_cancel/` | `htmx_edit_current_city_cancel` | `chat:htmx_edit_current_city_cancel` |
| `/edit/workplace/` | `htmx_edit_workplace` | `chat:htmx_edit_workplace` |
| `/edit/workplace_cancel/` | `htmx_edit_workplace_cancel` | `chat:htmx_edit_workplace_cancel` |
| `/edit/education/` | `htmx_edit_education` | `chat:htmx_edit_education` |
| `/edit/education_cancel/` | `htmx_edit_education_cancel` | `chat:htmx_edit_education_cancel` |
| `/edit/bio/<str:username>/` | `edit_bio` | `chat:edit_bio` |
| `/edit/current_city/<str:username>/` | `edit_current_city` | `chat:current_city` |
| `/edit/workplace/<str:username>/` | `edit_workplace` | `chat:workplace` |
| `/edit/education/<str:username>/` | `edit_education` | `chat:education` |
| `/edit/avatar/<str:username>/` | `edit_avatar` | `chat:avatar` |
| `/edit/username/<int:pk>/` | `edit_username` | `chat:username` |

---

## 13. Templates Overview

| Template | Extends | Purpose |
|---|---|---|
| `base.html` | — | Base for allauth pages (login, signup). Includes HTMX, Alpine, chat.js, online-status.js |
| `base_main.html` | — | Base for authenticated pages (app shell). Same includes as `base.html` |
| `login_page.html` | `base.html` | Login screen wrapper |
| `index.html` | `base_main.html` | User list (left pane + right user profile) |
| `chat.html` | `base_main.html` | Chat interface (left pane + right message pane) |
| `profile.html` | `base_main.html` | User profile with inline editing |
| `leftpane.html` | — | User list sidebar with status dots and unread counts |
| `rightpane.html` | — | Chat message area with message input |
| `user_profile.html` | — | Secondary profile view (right pane on index page) |
| `partials/*.html` | — | HTMX partials for inline editing forms and display states |
| `account/*.html` | — | allauth template overrides (login, signup, password, email) |

---

## Appendix: How to Add a New Feature (Checklist)

1. **Model** — Add to `chat/models.py`, run `makemigrations` + `migrate`
2. **View** — Add to `chat/views.py` (or `views_htmx.py` for HTMX endpoints)
3. **URL** — Add to `chat/urls.py`
4. **Template** — Add to `templates/` (or `templates/partials/` for HTMX)
5. **Consumer** — If real-time is needed, add to `chat/consumers.py` + `chat/routing.py`
6. **Form** — If form validation is needed, add to `chat/forms.py`
7. **Static files** — Add JS/CSS to `static/`
8. **Signal** — If auto-creation is needed, add to `chat/signals.py`
9. **Documentation** — Update this file
