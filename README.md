# Personal Chat App Demo

A real-time private messaging chat application built with Django, Django Channels, and modern frontend tools. Users can register, manage their profile, and exchange messages in real time with other registered users.

## Features

- **Real-time messaging** via WebSockets (Django Channels)
- **Private conversations** — one-to-one threaded chat between any two users
- **Online/offline status** — see who's currently active
- **Unread message counts** per conversation
- **User profiles** with avatar, bio, current city, workplace, and education
- **Inline editing** of profile fields using HTMX partials (no full page reload)
- **Email-based authentication** via django-allauth
- **Cloudinary integration** for avatar image storage
- **Responsive design** with Tailwind CSS (mobile-friendly layout)
- **Heroku-ready** deployment (Procfile + runtime.txt + whitenoise)

## Tech Stack

| Layer        | Technology                                         |
|-------------|----------------------------------------------------|
| Backend     | Python 3.8, Django 3.2                            |
| Real-time   | Django Channels 3, Daphne (ASGI), Redis            |
| Database    | SQLite (development), PostgreSQL (production)       |
| Frontend    | Tailwind CSS 3, Alpine.js 3, HTMX 1.7              |
| Auth        | django-allauth (email-based login)                 |
| Media       | Cloudinary                                         |
| Config      | python-decouple (environment variables)            |

## Requirements

- Python 3.8+
- Node.js & npm (for Tailwind CSS compilation)
- Redis (optional in development — falls back to in-memory channel layer when `DEBUG=True`)

## Quick Start (Development)

### 1. Clone and set up Python environment

```bash
git clone <repo-url>
cd personal-chat-app-demo
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install frontend dependencies and build CSS

```bash
npm install
npm run build-css   # compiles input.css → static/css/style.css
```

### 3. Configure environment

Create a `.env` file in the project root (or export the variables directly). For development, only `SECRET_KEY` and `DEBUG=True` are required — the app will use SQLite and an in-memory Channels layer:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. Run database migrations

```bash
python manage.py migrate
```

### 5. Start the server

For HTTP-only access (no WebSockets):

```bash
python manage.py runserver
```

For full real-time WebSocket support:

```bash
daphne -p 8000 mysite.asgi:application
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and register an account.

## Production Deployment

### Environment Variables

| Variable             | Description                        |
|---------------------|------------------------------------|
| `SECRET_KEY`        | Django secret key                  |
| `DEBUG`             | Set to `False`                     |
| `ALLOWED_HOSTS`     | Comma-separated allowed hosts      |
| `CLOUD_NAME`        | Cloudinary cloud name              |
| `API_KEY`           | Cloudinary API key                 |
| `API_SECRET`        | Cloudinary API secret              |
| `DB_NAME`           | PostgreSQL database name           |
| `DB_USER`           | PostgreSQL user                    |
| `DB_PASSWORD`       | PostgreSQL password                |
| `DB_HOST`           | PostgreSQL host                    |
| `EMAIL_HOST`        | SMTP host                          |
| `EMAIL_HOST_USER`   | SMTP username                      |
| `EMAIL_HOST_PASSWORD` | SMTP password                    |
| `EMAIL_PORT`        | SMTP port                          |
| `EMAIL_USE_TLS`     | Set to `True`                      |

### Heroku

The project includes a `Procfile` and `runtime.txt` for Heroku deployment:

```
web: daphne -p $PORT -b 0.0.0.0 mysite.asgi:application
```

## Project Structure

```
personal-chat-app-demo/
├── manage.py
├── Procfile
├── runtime.txt
├── requirements.txt
├── package.json
├── tailwind.config.js
├── input.css
├── mysite/                  # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py              # ASGI application (Channels routing)
│   └── wsgi.py
├── accounts/                # Custom user model (allauth-based)
│   ├── models.py
│   ├── forms.py
│   └── migrations/
├── chat/                    # Main chat application
│   ├── models.py            # Profile, Thread, ChatMessage
│   ├── views.py             # IndexView, PersonalChatView, ProfileView
│   ├── views_htmx.py        # HTMX partial endpoints
│   ├── consumers.py         # WebSocket: IndexConsumer, ChatConsumer
│   ├── routing.py           # WebSocket URL routing
│   ├── forms.py
│   ├── signals.py
│   └── migrations/
├── templates/               # Django templates
│   ├── base.html
│   ├── base_main.html
│   ├── index.html
│   ├── chat.html
│   ├── profile.html
│   ├── account/             # django-allauth template overrides
│   └── partials/            # HTMX partial templates
├── static/
│   ├── css/style.css        # Compiled Tailwind CSS
│   └── js/
│       ├── chat.js          # WebSocket chat client
│       └── online-status.js # WebSocket online status
└── staticfiles/
```

## License

This project is for demonstration purposes.
