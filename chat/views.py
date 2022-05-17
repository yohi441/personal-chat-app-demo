from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import View
from django.contrib.auth import get_user_model
from .models import ChatMessage, last_15_message
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile
from .forms import AvatarForm, UsernameForm
from accounts.models import User


# function to get the count of unread messages
# you can loop and compare to the list of user
def users_count(request, users):
    users_count = []
    for user in users:
        data_dict = {}
        if user.id > request.user.id:
            thread_name = f'chat_{user.id}-{request.user.id}'
        else:
            thread_name = f'chat_{request.user.id}-{user.id}'

        count = ChatMessage.objects.filter(
            sender=user, thread_name=thread_name, unread=True).count()

        data_dict["username"] = user.username
        data_dict["count"] = count

        users_count.append(data_dict)

    return users_count


class IndexView(LoginRequiredMixin, View):
    template_name = 'index.html'

    def get(self, request):
        users = User.objects.exclude(username=request.user.username)

        context = {
            'users': users,
            'users_count': users_count(request, users),
        }

        return render(request, self.template_name, context)


class PersonalChatView(LoginRequiredMixin, View):
    template_name = 'chat.html'

    def get(self, request, username):
        username = get_object_or_404(User, username=username)
        users = User.objects.exclude(username=request.user.username)
        user = User.objects.get(username=username)

        if request.user.id > username.id:
            thread_name = f'chat_{request.user.id}-{username.id}'
        else:
            thread_name = f'chat_{username.id}-{request.user.id}'

        messages = last_15_message(thread_name)

        unread_messages = ChatMessage.objects.filter(
            sender=user, thread_name=thread_name, unread=True)
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
        return render(request, self.template_name, context)


class ProfileView(LoginRequiredMixin, View):
    template_name = "profile.html"

    def get(self, request, username):
        user = User.objects.get(username=username)
        context = {
            'user': user
        }
        return render(request, self.template_name, context)


# helper method that returns profile instance
def profile_instance(username):
    user = User.objects.get(username=username)
    profile = Profile.objects.get(user=user)
    return profile


class EditAvatar(LoginRequiredMixin, View):

    def post(self, request, username):
        profile = profile_instance(username)
        form = AvatarForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(reverse('chat:profile', kwargs={'username': username}))
        return HttpResponse("form error")

    def get(self, request, username):
        return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


edit_avatar = EditAvatar.as_view()

# subclassing EditAvatar to inherit the get method and override the post method


class EditWorkplace(EditAvatar):

    def post(self, request, username):
        profile = profile_instance(username)
        workplace = request.POST.get('workplace')
        profile.workplace = workplace
        profile.save()
        return render(request, 'partials/workplace_cancel.html')


edit_workplace = EditWorkplace.as_view()


class EditEducation(EditWorkplace):

    def post(self, request, username):
        profile = profile_instance(username)
        education = request.POST.get('education')
        profile.education = education
        profile.save()
        return render(request, 'partials/education_cancel.html')


edit_education = EditEducation.as_view()


class EditBioSmall(EditWorkplace):
    template_name = 'partials/bioform_small_cancel.html'

    def post(self, request, username):

        profile = profile_instance(username)
        bio = request.POST.get('bio')
        profile.bio = bio
        profile.save()

        return render(request, self.template_name)


edit_bio_small = EditBioSmall.as_view()


class EditBio(EditBioSmall):
    template_name = 'partials/bioform_cancel.html'


edit_bio = EditBio.as_view()


class EditCurrentCity(EditWorkplace):

    def post(self, request, username):
        profile = profile_instance(username)
        current_city = request.POST.get('current_city')
        profile.current_city = current_city
        profile.save()

        return render(request, 'partials/current_city_cancel.html')


edit_current_city = EditCurrentCity.as_view()


class EditUsername(EditAvatar):
    def post(self, request, pk):
        user = User.objects.get(pk=pk)
        form = UsernameForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return render(request, 'partials/username_edit_cancel.html')

        return render(request, 'partials/username_edit.html', {'form': form})


edit_username = EditUsername.as_view()


def redirectionView(request):
    return redirect('/accounts/login')
