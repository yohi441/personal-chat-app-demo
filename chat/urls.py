from django.urls import path

from . import views
from . import views_htmx

app_name = 'chat'

urlpatterns = [
    
    path('', views.redirectionView),
    path('index/', views.IndexView.as_view(), name='index'),
    path('chat/<str:username>/', views.PersonalChatView.as_view(), name='chat'),
    path('profile/<str:username>/', views.ProfileView.as_view(), name="profile"),
    path('accounts/password/change/', views.redirectionView),
    path('accounts/inactive/', views.redirectionView),
    path('accounts/email/', views.redirectionView),
    path('accounts/email/', views.redirectionView),
    path('edit/bio/<str:username>', views.edit_bio, name="edit_bio"),
    path('edit/bio_small/<str:username>', views.edit_bio_small, name="edit_bio_small"),
    path('edit/current_city/<str:username>', views.edit_current_city, name="current_city")
    
]


htmx_urlpatterns = [
    path('edit_bio/', views_htmx.htmx_edit_bio, name="htmx_edit_bio"),
    path('edit_bio_cancel', views_htmx.htmx_edit_bio_cancel, name="htmx_edit_bio_cancel"),
    path('edit/avatar/', views_htmx.htmx_request_avatar, name="htmx_edit_avatar"),
    path('edit/avatar_cancel/', views_htmx.htmx_avatar_cancel, name="htmx_avatar_cancel"),
    path('edit/username/', views_htmx.htmx_edit_username , name="htmx_edit_username"),
    path('edit/username_cancel/', views_htmx.htmx_edit_username_cancel , name="htmx_edit_username_cancel"),
    path('edit/bio_small/', views_htmx.htmx_edit_bio_small , name="htmx_edit_bio_small"),
    path('edit/bio_small_cancel/', views_htmx.htmx_edit_bio_small_cancel, name="htmx_edit_bio_small_cancel"),
    path('edit/current_city/', views_htmx.htmx_edit_current_city , name="htmx_edit_current_city"),
    path('edit/current_city_cancel/', views_htmx.htmx_edit_current_city_cancel , name="htmx_edit_current_city_cancel"),
    path('edit/workplace/', views_htmx.htmx_edit_workplace , name="htmx_edit_workplace"),
    path('edit/workplace_cancel/', views_htmx.htmx_edit_workplace_cancel , name="htmx_edit_workplace_cancel"),
    path('edit/education/', views_htmx.htmx_edit_education , name="htmx_edit_education"),
    path('edit/education_cancel/', views_htmx.htmx_edit_education_cancel, name="htmx_edit_education_cancel"),
    path('edit/bio/<str:username>/', views.edit_bio, name="edit_bio"),
    path('edit/current_city/<str:username>/', views.edit_current_city, name="current_city"),
    path('edit/workplace/<str:username>/', views.edit_workplace, name="workplace"),
    path('edit/education/<str:username>/', views.edit_education, name="education"),
    path('edit/avatar/<str:username>/', views.edit_avatar, name="avatar"),
    path('edit/username/<int:pk>/', views.edit_username, name="username"),
]

urlpatterns += htmx_urlpatterns