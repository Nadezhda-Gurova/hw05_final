from django.forms import ModelForm
from django.forms.widgets import Textarea

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': ('Оставить комментарий'),
        }
        widgets = {'text': Textarea(attrs={'cols': 80, 'rows': 20})}
