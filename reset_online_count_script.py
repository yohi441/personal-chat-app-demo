import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()


from chat.models import Profile, User, Thread

users = User.objects.all()
for user in users:
    try:
        profile = Profile.objects.get(user=user)
        profile.online_status_count = 0
        print(profile.user.username, "counter reset to 0")
        profile.save()
    except:
        print(f"no profile in user: ", user)

threads = Thread.objects.all()

for thread in threads:
 
    thread.view_count = 0
    thread.save()
    print(f"user {thread.user.username} thread count is reset to 0")
 
        


