from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'comment')
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'}, format=('%Y-%m-%d'))
        }
    


class UserForm(forms.ModelForm):
    class Meta:
        model= User
        fields = ('first_name', 'last_name', 'username', 'email')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
