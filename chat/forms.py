from attr import fields
from django import forms
from .models import Profile
from accounts.models import User




class AvatarForm(forms.ModelForm):
    
    class Meta:
        model = Profile
        fields = [
            'avatar',
        ]

class UsernameForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            'username',
        ]
