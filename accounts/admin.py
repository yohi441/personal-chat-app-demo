from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User
from chat.models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'

class CustomUserAdmin(UserAdmin):
    model = User
    inlines = (ProfileInline,)

   


    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('updated',)}),
    )
    readonly_fields = ['updated']


admin.site.register(User, CustomUserAdmin)
