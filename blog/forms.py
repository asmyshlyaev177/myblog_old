from django.contrib.auth.forms import (UserCreationForm,
                                       UserChangeForm,
                                       ReadOnlyPasswordHashField)
from django import forms
from blog.models import myUser, Post, Comment
from django.conf import settings
from froala_editor.widgets import FroalaEditor


# forms for users
class SignupForm(forms.ModelForm):
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Пароль ещё раз',
                                widget=forms.PasswordInput)

    class Meta:
        model = myUser
        fields = ('username', 'email')
        labels = {
            'username': ('Имя пользователя(должно быть уникально)'),
            'email': ('E-mail'),
                }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# forms for users
class MyUserChangeForm(forms.ModelForm):

    class Meta:
        model = myUser
        fields = ('username', 'email', 'avatar')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text', )
        widgets = {'text': FroalaEditor(
            options={'toolbarInline': False,
                    'iframe': False,
                    'toolbarSticky': False,
                    'imageDefaultWidth': 800,
                    'language': 'ru',
                    'placeholderText': '''Напишите что-нибудь
                    или перетащите изображение''',
                    'imageMaxSize': 1024 * 1024 * 19,
                    'pasteDeniedTags': ['script'],
                    'imageEditButtons': [
                        'imageAlign', 'imageRemove',
                        '|', 'imageLink', 'linkOpen',
                        'linkEdit', 'linkRemove', '-',
                        'imageDisplay', 'imageStyle',
                        'imageAlt', 'imageSize'
                    ],
                    'toolbarButtons': [
                        'bold', 'italic',
                        'underline', 'strikeThrough',
                        'fontSize', '|', 'align',
                        'quote', '|', '-', 'insertLink',
                        'insertImage', 'insertVideo', '|',
                        'insertTable', '-', 'undo', 'redo',
                        'clearFormatting', 'fullscreen'
                                        ],
                    'toolbarButtonsMD': [
                        'bold', 'italic',
                        'underline', 'strikeThrough',
                        'fontSize', '|', 'align',
                        'quote', '|', '-', 'insertLink',
                        'insertImage', 'insertVideo', '|',
                        'insertTable', '-', 'undo', 'redo',
                        'clearFormatting', 'fullscreen'
                    ],
                    'toolbarButtonsSM': [
                        'bold', 'italic',
                        'underline', 'strikeThrough',
                        '|', 'align',
                        'quote', 'insertLink',
                        'insertImage', 'insertVideo',
                        'undo', 'redo',
                        'clearFormatting', 'fullscreen'
                    ],
                    'toolbarButtonsXS': [
                        'align',
                        'quote', 'insertLink',
                        'insertImage', 'insertVideo',
                        'undo', 'redo',
                        'clearFormatting', 'fullscreen'
                    ]}
                    )}


class AddPostForm(forms.ModelForm):
    tags_new = forms.CharField(label="Тэги", required=False,
                               widget=forms.TextInput(
                                   attrs={'class': 'tm-input tm-input-typeahead tt-input'})
                               )

    class Meta:
        model = Post
        fields = ('title', 'post_image', 'image_url', 'category', 'private',
                  'description', 'text', 'rateable', 'comments', 'locked',
                  'status')
        labels = {
            'title': ('Заголовок'),
            'post_image': ('Изображение для главной'),
            'category': ('Категория'),
            'description': ('Описание'),
            'text': ('Текст поста'),
            'private': ('Для взрослых/только для зарегистрированных'),
            'rateable': ('Голосование разрешено'),
            'comments': ('Комментирование разрешено'),
            'locked': ('Редактирование разрешено'),
        }

        widgets = {
            # 'text': SummernoteInplaceWidget(),
            'text': FroalaEditor(

                                options={'toolbarInline': False,
                                        'iframe': False,
                                        'toolbarSticky': False,
                                        'imageDefaultWidth': 800,
                                        'language': 'ru',
                                        'placeholderText': '''Напишите что-нибудь
                                        или перетащите изображение''',
                                        'imageMaxSize': 1024 * 1024 * 19,
                                        'pasteDeniedTags': ['script'],
                                        'imageEditButtons': [
                                            'imageAlign', 'imageRemove',
                                            '|', 'imageLink', 'linkOpen',
                                            'linkEdit', 'linkRemove', '-',
                                            'imageDisplay', 'imageStyle',
                                            'imageAlt', 'imageSize'
                                        ],
                                        'toolbarButtons': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            'fontSize', '|', 'align',
                                            'quote', '|', '-', 'insertLink',
                                            'insertImage', 'insertVideo', '|',
                                            'insertTable', '-', 'undo', 'redo',
                                            'clearFormatting', 'fullscreen'
                                                        ],
                                        'toolbarButtonsMD': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            'fontSize', '|', 'align',
                                            'quote', '|', '-', 'insertLink',
                                            'insertImage', 'insertVideo', '|',
                                            'insertTable', '-', 'undo', 'redo',
                                            'clearFormatting', 'fullscreen'
                                        ],
                                        'toolbarButtonsSM': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            '|', 'align',
                                            'quote', 'insertLink',
                                            'insertImage', 'insertVideo',
                                            'undo', 'redo',
                                            'clearFormatting', 'fullscreen'
                                        ],
                                        'toolbarButtonsXS': [
                                            'align',
                                            'quote', 'insertLink',
                                            'insertImage', 'insertVideo',
                                            'undo', 'redo',
                                            'clearFormatting', 'fullscreen'
                                        ]}),
            'description': FroalaEditor(
                                options={'toolbarInline': False,
                                        'iframe': False,
                                        'toolbarSticky': False,
                                        'language': 'ru',
                                        'placeholderText': '''Короткое описание
                                         для главной''',
                                        'charCounterCount': True,
                                        'charCounterMax': 500,
                                        'pasteDeniedTags': ['script'],
                                        'imageMaxSize': 1024 * 1024 * 19,

                                        'toolbarButtons': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            'fontSize', '|', 'align',
                                            'quote', '|', '-', 'insertLink',
                                            'insertVideo', '|',
                                            'insertTable', '-', 'undo', 'redo',
                                            'clearFormatting', 'fullscreen'
                                                        ],
                                        'toolbarButtonsMD': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            'fontSize', '|', 'align',
                                            'quote', '|', '-', 'insertLink',
                                            'insertVideo', '|',
                                            'insertTable', '-', 'undo', 'redo',
                                            'clearFormatting', 'fullscreen'
                                        ],
                                        'toolbarButtonsSM': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            '|', 'align',
                                            'quote', 'insertLink',
                                            'insertVideo',
                                            'undo', 'redo',
                                            'clearFormatting', 'fullscreen'
                                        ],
                                        'toolbarButtonsXS': [
                                            'align',
                                            'quote', 'insertLink',
                                            'insertVideo',
                                            'undo', 'redo',
                                            'clearFormatting', 'fullscreen'
                                        ]})
        }
    # def save(self, commit=True):
        # do something with self.cleaned_data['temp_id']
        # return super(AddPostForm, self).save(commit=commit)
