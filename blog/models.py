# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager)
from slugify import slugify, SLUG_OK
from django.utils import timezone
import datetime, re, os, datetime
from time import gmtime, strftime
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFit
#from imagekit import ImageSpec, register
from django.utils.safestring import mark_safe
from django.dispatch import receiver
from django.conf import settings
from bs4 import BeautifulSoup
from PIL import Image
#from unidecode import unidecode
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, urlretrieve, Request
from blog.functions import srcsets, findFile, findLink, srcsetThumb,deleteThumb
from django.conf import settings
from blog.functions import findLink,findFile,saveImage,srcsets
from froala_editor.fields import FroalaField
from django.utils.encoding import uri_to_iri, iri_to_uri
from django.core.cache import cache
#import mptt
#from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import Group
#import socket #timeout just for test
#socket.setdefaulttimeout(10)
from celery import Celery
app = Celery('tasks', broker='pyamqp://guest@localhost//')

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

        user_rating, _ = RatingUser.objects.get_or_create(user=user)
        user_rating.user = user
        user_rating.rating = 0.0
        user_votes, _ = UserVotes.objects.get_or_create(user=user)
        user_votes.user = user
        user_rating.save()
        user_votes.save()
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
    ["id", "username", "avatar"],
    ]
    username = models.CharField("Username", max_length=30,
                                blank=False,
                                unique=True)
    rateable = models.BooleanField(default = True)
    def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
        return 'avatars/{0}/{1}'.format(instance.username, filename)

    avatar = ProcessedImageField(upload_to=user_directory_path,
                                 processors=[ResizeToFit(64, 64)],
                                 format='JPEG',
                                 options={'quality': 90}, blank=True)
    email = models.EmailField(unique=True, blank=False)
    #password = models.CharField("Password", max_length=230)
    is_active = models.BooleanField("Is active", default=True)
    is_it_staff = models.BooleanField("Is stuff", default=False)
    is_it_superuser = models.BooleanField("Is admin", default=False)
    moderated = models.BooleanField("Moderated", default=True)
    user_last_login = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    has_votes = models.BooleanField(default=True)
    REQUIRED_FIELDS = ['email',]
    USERNAME_FIELD = 'username'
    objects = MyUserManager()

    def get_avatar(self):
        return mark_safe('<img src="%s" class ="responsive-img"/>'\
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
    class Meta:
        verbose_name_plural = "users"

    @property
    def is_superuser(self):
        return self.is_it_superuser
    @property
    def is_staff(self):
        return self.is_it_staff

    def save(self, *args, **kwargs):

        super(myUser, self).save(*args, **kwargs)

@receiver(models.signals.post_delete, sender=myUser)
def _post_delete(sender, instance, **kwargs):
    """delete avatar when delete user"""
    cache.delete_pattern("post_list_*")
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)

@app.task(name="deleteFile")
def deleteFile(file):
	os.remove(file)

@receiver(models.signals.pre_save, sender=myUser)
def _pre_save(sender, instance, **kwargs):
    """delete old file when avatar changed"""
    cache.delete_pattern("post_list_*")
    if not instance.pk:
        return False

    try:
        old_file = myUser.objects.get(pk=instance.pk).avatar
    except myUser.DoesNotExist:
        return False

    new_file = instance.avatar
    #print("***********************")
    #print('old_file: ', old_file)
    #print('new_file: ', new_file)
    #print('old_file.path: ', old_file.path)
    if not str(old_file).split('/')[-1] == new_file and old_file:
        if os.path.isfile(old_file.path):
            #os.remove(old_file.path)
            deleteFile.apply_async((old_file.path,), countdown=3600)



class Rating(models.Model):
    #ratingid = models.IntegerField(unique = True)
    rating = models.FloatField(default=0.0)

    class Meta:
        abstract = True

class RatingPost(Rating):

    post = models.ForeignKey('Post')

class RatingTag(Rating):
    tag = models.ForeignKey('Tag', db_index=True)

class RatingUser(Rating):
    user = models.ForeignKey('myUser', db_index=True)

class RatingComment(Rating):
    user = models.ForeignKey('Comment', db_index=True)


class Vote(models.Model):
    #vote_id = models.IntegerField(blank = True, null = True)
    rate = models.BooleanField()
    score = models.FloatField(null = True, blank = True)
    created = models.DateTimeField(auto_now_add=True) #for celery
    counted = models.BooleanField(default=False)
    class Meta:
        abstract = True

class VotePost(Vote):
    post = models.ForeignKey('Post', db_index=True)

class UserVotes(models.Model):
    #userid = models.IntegerField(blank = True, null = True)
    votes = models.IntegerField(default = 10)
    weight = models.FloatField(default = 0.25)
    COUNT = (
                ("U", "Unlimited"),
                ("N","Normal"),
                ("B","Blocked"),
    )
    count = models.CharField(max_length=1, choices=COUNT, default="N")
    block_date = models.DateTimeField(blank=True, null=True)
    manual = models.BooleanField(default = False)
    user = models.ForeignKey('myUser',db_index=True)

"""class Thumbnail(ImageSpec):
    processors = [ResizeToFit(800, 600)]
    format = 'JPEG'
    options = {'quality': 100}

register.generator('blog:thumbnail', Thumbnail) """

class Post(models.Model):
    index_together = [
    ["title", "description", "post_thumbnail", "author", "category",
     "url", "published", "private", "status","main_tag"],
    ]
    title = models.CharField(max_length=100)
    #description = RichTextField(max_length = 500, config_name = "description",
    #                            blank=True)
    rateable = models.BooleanField(default = True)
    description = models.CharField(max_length=500)
    #text = RichTextUploadingField(config_name = "post")
    text = models.TextField()
    today = datetime.date.today()
    upload_path = str(today.year)+'/' +str(today.month)+'/'+str(today.day)+'/'
    post_image = models.ImageField(upload_to =
                        upload_path, blank=True)
    image_url = models.URLField(null=True, blank=True, max_length=500)

    def post_image_gif(self):
        if self.post_image:
            ext = []
            ext = self.post_image.path.split('.')
            if ext[-1] == "gif":
                return True
            else:
                return False
        else:
            return False

    post_image.short_description = 'Image'
    #post_thumbnail = ImageSpecField(source='post_image',
    #                            processors=[ResizeToFit(1366, 2000)],
    #                            format='JPEG',
    #                            options={'quality': 85})
    post_thumbnail = models.ImageField(upload_to =
                        upload_path, blank=True)
    def get_image(self):
        return mark_safe('<img src="%s" class ="responsive-img center-align"/>'\
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
                                        related_query_name='tag',
                                        blank=True)
    private = models.BooleanField(default=False)
    private.short_description = 'NSFW'
    #main_tag = models.CharField(max_length=33, blank=True)
    main_tag = models.ForeignKey('Tag', null=True, blank=True)
    url = models.CharField(max_length=330,blank=True)
    STATUS = (
                ("D", "Draft"),
                ("P","Published"),
    )
    status = models.CharField(max_length=1, choices=STATUS, default="D")


    class Meta:
        ordering = ['-published']
        verbose_name_plural = "posts"
    def __str__(self):
        return self.title

    def get_absolute_url(self):
        cat_url = self.main_tag.url
        #post_url = slugify(unidecode(self.title))
        return "/%s/%s-%i/" % (cat_url, self.url, self.id)
    def get_category(self):
        return self.category.get_url
    def get_tags_list(self):
        #return self.tags.values_list('name', flat=True)
        return self.tags.all()

    def save(self, *args, **kwargs):
        super(Post, self).save(*args, **kwargs)

@receiver(models.signals.pre_delete, sender=Post)
def _post_delete(sender, instance, **kwargs):

    deleteThumb(instance.text)
    deleteThumb(instance.image_url)

    cache_str = "post_list_" + str(instance.category).lower()+"_"+str(instance.private)
    cache.delete(cache_str)
    cache.delete("post_list_True")
    cache.delete("post_list_False")
    print("**********************************************")
    print("cache str :", str(cache_str))
    cache_str = "post_single_" + str(instance.id)
    cache.delete(cache_str)
    try:
        if instance.post_image:
            file = instance.post_image
            if os.path.isfile(file.path):
                os.remove(file.path)
    except:
        pass

@receiver(models.signals.pre_save, sender=Post)
def _post_save(sender, instance, **kwargs):
    """delete old file when thumbnail changed"""

    cache_str = "post_single_" + str(instance.id)
    cache.delete(cache_str)
    cache_str = "post_list_" + str(instance.category).lower()+"_"+str(instance.private)
    cache.delete(cache_str)
    cache.delete("post_list_True")
    cache.delete("post_list_False")
    if not instance.pk:
        return False

    try:
        old_file = Post.objects.get(pk=instance.pk).post_image
    except Post.DoesNotExist:
        return False

    new_file = instance.post_image

    if not old_file == new_file and old_file:
        if os.path.isfile(old_file.path):
            deleteThumb(instance.post_url)
            thumb = srcsetThumb(instance.post_image)
            instance.post_image = thumb
            os.remove(old_file.path)

    try:
        old_file = Post.objects.get(pk=instance.pk).post_thumbnail
    except Post.DoesNotExist:
        return False

    new_file = instance.post_thumbnail
    if not old_file == new_file and old_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

@receiver(models.signals.post_save, sender=Post)
def _post_save(sender, instance, **kwargs):
    #thumb for gifs
    if instance.post_image_gif():
        file= instance.post_image.path.split('.gif')[0]
        im = Image.open(instance.post_image.path).convert('RGB')
        size = ( im.width, im.height)
        im.thumbnail(size)
        im.save(file + "-thumbnail.jpeg", "JPEG")
        file_new = file.split(settings.MEDIA_ROOT)[1]+"-thumbnail"
        try:
            file_orig =  instance.post_thumbnail.path.split('.')[0].split(settings.MEDIA_ROOT)[1]
        except:
            file_orig = ""
        instance.post_thumbnail = file_new +".jpeg"

        if file_orig != file_new:
            instance.save()

class Category(models.Model):
    index_together = [
    ["id","name", "order", "slug"],
    ]
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(max_length=400)
    slug = models.CharField("URL",blank=True, max_length=250)
    order = models.SmallIntegerField(blank=True, default=1)
    class Meta:
        verbose_name_plural = "categories"
        ordering = ['order']
    def __str__(self):
        return self.name
    def get_url(self):
        cat_url = slugify(self.name.lower())
        return "/%s/" % (cat_url)
    @classmethod
    def list(self):
        cat_list = self.objects.all().only("name","order", "slug")
        return cat_list
    def save(self, *args, **kwargs):
        #if not self.slug:
        self.slug = slugify(self.name.lower())
        super(Category,self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=30)
    url = models.CharField(max_length=140, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    private = models.BooleanField(default=False)
    rateable = models.BooleanField(default = True)
    description = models.TextField(max_length=700, blank =True, null=True)

    category = models.ForeignKey('Category', blank=True, null=True)

    class Meta:
        verbose_name_plural = "tags"
    def __str__(self):
        return self.name

    #def save(self, *args, **kwargs):
    #    if not self.url:
    #        self.url = slugify(self.name.lower())

    #    super(Tag, self).save(*args, **kwargs)

@receiver(models.signals.pre_delete, sender=Tag)
def delete_image_and_thumb(sender, instance, **kwargs):
    cache.delete("taglist")
    deleteThumb(instance.description)

@receiver(models.signals.pre_save, sender=Tag)
def delete_old_image_and_thumb(sender, instance, **kwargs):
    """delete old file when thumbnail changed"""
    if not instance.pk:
        return False

    cache.delete("taglist")
    deleteThumb(instance.description)
    instance.description = str(srcsets(instance.description, False))

class Comment(MPTTModel):
    text = models.TextField(max_length=700)
    author = models.ForeignKey('myUser', blank=True, null=True)
    post = models.ForeignKey('Post', blank=True, null=True)
    removed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children', db_index=True)

    def __str__(self):
        return self.text

    class MPTTMeta:
        order_insertion_by = ['created']
        verbose_name_plural = "Comments"
