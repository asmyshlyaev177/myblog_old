from django.contrib.auth.forms import (UserCreationForm,
                                       UserChangeForm,
                                       ReadOnlyPasswordHashField)
from django import forms
from blog.models import myUser, Post, Comment
from django.conf import settings
from froala_editor.widgets import FroalaEditor


class SignupForm(forms.ModelForm):
    """Форма регистрации"""
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
        user.save()
        return user


#
class MyUserChangeForm(forms.ModelForm):
    """ редактирование инфы о пользователе в дашборде"""
    class Meta:
        model = myUser
        fields = ('username', 'email', 'avatar')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text', )
        """widgets = {'text': FroalaEditor(
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
                        'clearFormatting'
                                        ],
                    'toolbarButtonsMD': [
                        'bold', 'italic',
                        'underline', 'strikeThrough',
                        'fontSize', '|', 'align',
                        'quote', '|', '-', 'insertLink',
                        'insertImage', 'insertVideo', '|',
                        'insertTable', '-', 'undo', 'redo',
                        'clearFormatting'
                    ],
                    'toolbarButtonsSM': [
                        'bold', 'italic',
                        'underline', 'strikeThrough',
                        '|', 'align',
                        'quote', 'insertLink',
                        'insertImage', 'insertVideo',
                        'undo', 'redo',
                        'clearFormatting'
                    ],
                    'toolbarButtonsXS': [
                        'align',
                        'quote', 'insertLink',
                        'insertImage', 'insertVideo',
                        'undo', 'redo',
                        'clearFormatting'
                    ]}
                    )}
                    )}"""


class AddPostForm(forms.ModelForm):
    """ форма добавления поста"""
    tags_new = forms.CharField(label="Тэги", required=False,
                               widget=forms.TextInput(
                                   attrs={'class': 'tm-input tm-input-typeahead tt-input'})
                               )

    class Meta:
        model = Post
        fields = ('title', 'post_image', 'image_url', 'category', 'private', 'description', 'text', 'locked', 'status')
        labels = {
            'title': ('Заголовок'),
            'post_image': ('Изображение для главной'),
            'category': ('Категория'),
            'description': ('Описание'),
            'text': ('Текст поста'),
            'private': ('Для взрослых/только для зарегистрированных'),
            'rateable': ('Голосование разрешено'),
            'comments': ('Комментирование разрешено'),
            'locked': ('Редактирование запрещено'),
        }

        """widgets = {
            'text': FroalaEditor(

                                options={'toolbarInline': False,
                                        'iframe': False,
                                        'toolbarSticky': False,
                                        'imageDefaultWidth': 800,
                                        'language': 'ru',
                                        'imageResize': 'false',
                                        'imagePasteProcess': 'true',
                                        'placeholderText': '''Напишите что-нибудь
                                        или перетащите изображение''',
                                        'imageMaxSize': 1024 * 1024 * 50,
                                        'pasteDeniedTags': ['script'],
                                        'charCounterMax': 2500,
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
                                            'clearFormatting'
                                                        ],
                                        'toolbarButtonsMD': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            'fontSize', '|', 'align',
                                            'quote', '|', '-', 'insertLink',
                                            'insertImage', 'insertVideo', '|',
                                            'insertTable', '-', 'undo', 'redo',
                                            'clearFormatting'
                                        ],
                                        'toolbarButtonsSM': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            '|', 'align',
                                            'quote', 'insertLink',
                                            'insertImage', 'insertVideo',
                                            'undo', 'redo',
                                            'clearFormatting'
                                        ],
                                        'toolbarButtonsXS': [
                                            'align',
                                            'quote', 'insertLink',
                                            'insertImage', 'insertVideo',
                                            'undo', 'redo',
                                            'clearFormatting'
                                        ]}),
            'description': FroalaEditor(
                                options={'toolbarInline': False,
                                        'iframe': False,
                                        'toolbarSticky': False,
                                        'language': 'ru',
                                        'imageResize': 'false',
                                        'imagePasteProcess': 'true',
                                        'placeholderText': '''Короткое описание
                                         для главной''',
                                        'charCounterCount': True,
                                        'charCounterMax': 500,
                                        'pasteDeniedTags': ['script'],
                                        'imageMaxSize': 1024 * 1024 * 50,

                                        'toolbarButtons': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            'fontSize', '|', 'align',
                                            'quote', '|', '-', 'insertLink',
                                            'insertVideo', '|',
                                            'insertTable', '-', 'undo', 'redo',
                                            'clearFormatting'
                                                        ],
                                        'toolbarButtonsMD': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            'fontSize', '|', 'align',
                                            'quote', '|', '-', 'insertLink',
                                            'insertVideo', '|',
                                            'insertTable', '-', 'undo', 'redo',
                                            'clearFormatting'
                                        ],
                                        'toolbarButtonsSM': [
                                            'bold', 'italic',
                                            'underline', 'strikeThrough',
                                            '|', 'align',
                                            'quote', 'insertLink',
                                            'insertVideo',
                                            'undo', 'redo',
                                            'clearFormatting'
                                        ],
                                        'toolbarButtonsXS': [
                                            'align',
                                            'quote', 'insertLink',
                                            'insertVideo',
                                            'undo', 'redo',
                                            'clearFormatting'
                                        ]})
        }"""
