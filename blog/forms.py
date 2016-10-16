from django.contrib.auth.forms import (UserCreationForm,
                                       UserChangeForm,
                                       ReadOnlyPasswordHashField)
from django import forms
from blog.models import myUser, Post
from django.conf import settings
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

#forms for users
class SignupForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password',
                                widget=forms.PasswordInput)
    class Meta:
        model = myUser
        fields = ('username', 'email')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidateError("Password don't match")
        return password2

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

#forms for users
class MyUserChangeForm(forms.ModelForm):

    class Meta:
        model = myUser
        fields = ('username', 'email','avatar')

class AddPostForm(forms.ModelForm):
    tags_new = forms.CharField(label="new tags",required=False,
                               widget= forms.TextInput(
                                   attrs={'class': 'tm-input tm-input-typeahead tt-input'})
                               )
    hidden_tags_new = forms.CharField(required=False,
                                      widget= forms.HiddenInput(
                                          attrs={}
                                      ))

    class Meta:
        model = Post
        fields = ('title', 'post_image', 'category', 'description','text','tags',
                  'hidden_tags_new')
        widgets = {
            'text': SummernoteInplaceWidget(),
        }
    def save(self, commit=True):
        #self.instance.hidden_tags_new = self.cleaned_data['hidden_tags_new']
        # do something with self.cleaned_data['temp_id']
        return super(AddPostForm, self).save(commit=commit)
