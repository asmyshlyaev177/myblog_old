from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager)
from django.utils.text import slugify
from django.utils import timezone
import datetime
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFit
from django.utils.safestring import mark_safe
import re
from django.conf import settings



class MyUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('User must have unique email!')
        if not username:
            raise ValueError('User mush have unique username!')

        user = self.model(
            username = username.lower(),
            email = email.lower()
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            username, email, password=password
        )
        user.is_it_superuser = True
        user.is_it_staff = True
        user.save(using=self._db)
        return user
    def create_staff(self, username, email, password):
        user = self.create_user(
            username, email, password=password
        )
        user.is_staff = True
        user.save(using.self._db)
        return user

class myUser(AbstractBaseUser):
    index_together = [
    ["id", "username"],
    ]
    username = models.CharField("Username/email", max_length=30,
                                blank=False,
                                unique=True)
    avatar = ProcessedImageField(upload_to='avatars',
                                 processors=[ResizeToFit(50, 50)],
                                 format='JPEG',
                                 options={'quality': 90}, blank=True)
    email = models.EmailField(unique=True, blank=False)
    #password = models.CharField("Password", max_length=230)
    is_active = models.BooleanField("Is active", default=True)
    is_it_staff = models.BooleanField("Is stuff", default=False)
    is_it_superuser = models.BooleanField("Is admin", default=False)
    last_login = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    REQUIRED_FIELDS = ['email',]
    USERNAME_FIELD = 'username'
    objects = MyUserManager()

    def get_avatar(self):
        return mark_safe('<img src="%s" class ="img-responsive"/>'\
                         % (self.avatar.url))
    get_avatar.short_description = 'Current avatar'

    def __str__(self):
        return self.username.lower()
    def get_full_name(self):
        return self.username.lower()
    def get_short_name(self):
        return self.username.lower()
    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_superuser(self):
        return self.is_it_superuser
    @property
    def is_staff(self):
        return self.is_it_staff

class Post(models.Model):
    index_together = [
    ["title", "description", "post_thumbnail", "author", "category",
     "url", "published", "status"],
    ]
    title = models.CharField(max_length=150)
    description = RichTextField(max_length = 500, config_name = "description",
                                blank=True)
    text = RichTextUploadingField(config_name = "post")
    today = datetime.date.today()
    post_image = models.ImageField(upload_to =
                        str(today.year)+'/'
                        +str(today.month)+'/'+str(today.day)+'/', blank=True)
    post_image.short_description = 'Image'
    post_thumbnail = ImageSpecField(source='post_image',
                                processors=[ResizeToFit(640, 480)],
                                format='JPEG',
                                options={'quality': 85})
    def get_image(self):
        return mark_safe('<img src="%s" class ="img-responsive center-block"/>'\
                         % (self.post_thumbnail.url))
    get_image.short_description = 'Thumbnail'

    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)
    published = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               default = 1,
                               on_delete=models.SET_DEFAULT) ###
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
    #def save(self, *args, **kwargs):
    #    self.description = re.sub(
    #        '\<img((\W+)|(\w+))*\ \/>', '', self.description)
    #    self.description = re.sub(
    #        '\<script((\W+)|(\w+))*\<\/script\>', '', self.description)
    #    self.description = re.sub(
    #        '\<iframe((\W+)|(\w+))*\<\/iframe\>', '', self.description)
    #    super(Post, self).save(*args, **kwargs) # Call the "real" save() method.

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        cat_url = slugify(self.category)
        post_url = slugify(self.title)
        return "/%s/%s-%i/" % (cat_url, self.url, self.id)
    def get_category(self):
        return slugify(self.category)

class Category(models.Model):
    index_together = [
    ["id","name", "order"],
    ]
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(max_length=250)
    slug = models.SlugField("URL",blank=True, max_length=150)
    order = models.SmallIntegerField(blank=True, default=1)
    def __str__(self):
        return self.name
    def get_url(self):
        cat_url = slugify(self.name)
        return "/%s/" % (cat_url)
    @classmethod
    def list(self):
        cat_list = cat = self.objects.all().only("name","order")\
            .order_by('order','name')
        #cat = self.objects.all().order_by('order','name')
        #cat_list = list()
        #for c in cat:
            #cat_list.append(c.name)
        return cat_list
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Category,self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    def __str__(self):
        return self.name
