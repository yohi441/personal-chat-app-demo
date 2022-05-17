from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import AvatarForm
from .forms import UsernameForm
from django.contrib.auth.decorators import login_required


@login_required
def htmx_edit_bio(request):
    if request.htmx:
        return render(request, 'partials/bioform.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_bio_cancel(request):
    if request.htmx:
        return render(request, 'partials/bioform_cancel.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_request_avatar(request):
    if request.htmx:
        form = AvatarForm(request.POST, request.FILES)
        return render(request, 'partials/avatar.html', {'form': form})
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_avatar_cancel(request):
    if request.htmx:
        return render(request, 'partials/avatar_cancel.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_username(request):
    if request.htmx:
        form = UsernameForm()
        return render(request, 'partials/username_edit.html', {'form': form})
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_username_cancel(request):
    if request.htmx:
        return render(request, 'partials/username_edit_cancel.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_bio_small(request):
    if request.htmx:
        return render(request, 'partials/bioform_small.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_bio_small_cancel(request):
    if request.htmx:
        return render(request, 'partials/bioform_small_cancel.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_current_city(request):
    if request.htmx:
        return render(request, 'partials/current_city.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_current_city_cancel(request):
    if request.htmx:
        return render(request, 'partials/current_city_cancel.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_workplace(request):
    if request.htmx:
        return render(request, 'partials/workplace.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_workplace_cancel(request):
    if request.htmx:
        return render(request, 'partials/workplace_cancel.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_education(request):
    if request.htmx:
        return render(request, 'partials/education.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))


@login_required
def htmx_edit_education_cancel(request):
    if request.htmx:
        return render(request, 'partials/education_cancel.html')
    return redirect(reverse('chat:profile', kwargs={'username': request.user.username}))
