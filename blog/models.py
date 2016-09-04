from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils.text import slugify
from django.utils import timezone
import datetime
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from django.utils.safestring import mark_safe
import re

class User(AbstractBaseUser):
    username = models.CharField("Username", max_length=20,
                                blank=False,
                                unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField("Is active?", default=True)
    is_staff = models.BooleanField("Is admin", default=False)
    last_login = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = 'email'
    def __str__(self):
        return self.username

class Post(models.Model):
    title = models.CharField(max_length=150)
    description = RichTextField(max_length = 500, config_name = "description",
                                blank=True)
    text = RichTextUploadingField(config_name = "post")
    today = datetime.date.today()
    post_image = models.ImageField(upload_to =
                        str(today.year)+'/'
                        +str(today.month)+'/'+str(today.day)+'/', blank=True)
    post_image.short_description = 'Image'
    def get_image(self):
        return mark_safe('<img src="%s" />' % (self.post_thumbnail.url))
    get_image.short_description = 'Thumbnail'
    post_thumbnail = ImageSpecField(source='post_image',
                                processors=[ResizeToFit(640, 480)],
                                format='JPEG',
                                options={'quality': 85})
    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)
    published = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey('User') ###
    category = models.ForeignKey('Category')
    tags = models.ManyToManyField('Tag',
                                        related_name='posts',
                                        related_query_name='post',
                                        blank=True)
    url = models.SlugField(blank=True)
    STATUS = (
                ("D", "Draft"),
                ("P","Published"),
    )
    status = models.CharField(max_length=1, choices=STATUS, default="D")
    ordering = ('-published',)
    def save(self, *args, **kwargs):
        self.description = re.sub(
            '\<img((\W+)|(\w+))*\ \/>', '', self.description)
        self.description = re.sub(
            '\<script((\W+)|(\w+))*\<\/script\>', '', self.description)
        self.description = re.sub(
            '\<iframe((\W+)|(\w+))*\<\/iframe\>', '', self.description)
        super(Post, self).save(*args, **kwargs) # Call the "real" save() method.

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        cat_url = slugify(self.category)
        post_url = slugify(self.title)
        return "/%s/%s-%i/" % (slugify(self.category), self.url, self.id)


class Category(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(max_length=250)
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    def __str__(self):
        return self.name
