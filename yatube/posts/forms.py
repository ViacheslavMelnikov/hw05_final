from django import forms
from django.forms import ModelForm, Select
from .models import Post, Comment


class PostForm(ModelForm):

    def _init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields["group"]

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        widgets = {"group": Select(attrs={'class': 'form-control',
                                          'id': 'id_group',
                                          'name': 'group'}),
                   "text": Select(attrs={'class': 'form-control',
                                         'required_id': 'id_text',
                                         'name': 'text',
                                         'cols': '40',
                                         'rows': '10'})}
        exclude = ['author']

    def clean_subject(self):
        data = self.changed_data['text']
        if data is None:
            raise forms.ValidationError()
        return data


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
