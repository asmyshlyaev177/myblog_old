# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager, PermissionsMixin)
from django.utils.text import slugify
from django.utils import timezone
import datetime, re, os, datetime, json
from time import gmtime, strftime
from imagekit.models import ImageSpecField, ProcessedImageField
from django.contrib.postgres.fields import JSONField
from imagekit.processors import ResizeToFit
from django.utils.safestring import mark_safe
from django.dispatch import receiver
from django.conf import settings
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, urlretrieve, Request
from django.conf import settings
from froala_editor.fields import FroalaField
from django.utils.encoding import uri_to_iri, iri_to_uri
from django.core.cache import cache
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import Group
from celery import Celery
from meta.models import ModelMeta
from blog.functions import (srcsets, findFile, findLink, saveImage,
                            srcsetThumb, deleteThumb, validate_post_image)
app = Celery('tasks', broker='pyamqp://guest@localhost//')
    
class MyUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('User must have unique email!')
        if not username:
            raise ValueError('User mush have unique username!')

        user = self.model(
            username=username.lower(),
            email=email.lower()
        )

        user.set_password(password)
        user.save(using=self._db)
        user_votes, _ = UserVotes.objects.get_or_create(user=user)
        user_votes.user = user
        user_votes.save()
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            username, email, password=password
        )
        user.is_superuser = True
        user.moderated = False
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_staff(self, username, email, password):
        user = self.create_user(
            username, email, password=password
        )
        user.is_staff = True
        user.moderated = False
        user.save(using.self._db)
        return user


class myUser(AbstractBaseUser, PermissionsMixin):
    index_together = [
        ["id", "username", "moderator"],
    ]
    username = models.CharField("Логин", max_length=30,
                                blank=False,
                                unique=True)
    rateable = models.BooleanField(default=True)

    def user_directory_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
        return 'avatars/{0}/{1}'.format(instance.username, filename)

    avatar = ProcessedImageField(upload_to=user_directory_path,
                                 processors=[ResizeToFit(64, 64)],
                                 format='JPEG',
                                 options={'quality': 90}, blank=True,
                                 verbose_name="Аватар")
    email = models.EmailField(unique=True, blank=False)
    # password = models.CharField("Password", max_length=230)
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Персонал", default=False)
    #is_superuser = models.BooleanField("Админ всего и вся", default=False)
    moderated = models.BooleanField("Модерируется", default=False)
    moderator = models.BooleanField("Модератор", default=False)
    moderator_of_tags = models.ManyToManyField('Tag', blank=True,
                verbose_name="Модерирует тэги")
    moderator_of_categories = models.ManyToManyField('Category', blank=True,
                verbose_name="Модерирует категории")
    user_last_login = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    REQUIRED_FIELDS = ['email', ]
    USERNAME_FIELD = 'username'
    VOTES_AMOUNT = (
                    ("U", "Unlimited"),
                    ("N", "Normal"),
                    ("B", "Blocked"),
    )
    can_post = models.BooleanField("Может добавлять посты", default=True)
    can_comment = models.BooleanField("Может комментировать", default=True)
    can_complain = models.BooleanField("Может жаловаться", default=True)
    rating = models.FloatField('Рейтинг', default=0.0)
    votes_amount = models.CharField(max_length=1, choices=VOTES_AMOUNT, default="N")
    objects = MyUserManager()

    def get_avatar(self):
        return mark_safe('<img src="%s" class ="responsive-img"/>'
                         % (self.avatar.url))
    get_avatar.short_description = 'Текущий аватар'

    def __str__(self):
        return self.username.lower()

    def get_full_name(self):
        return self.username.lower()

    def get_short_name(self):
        return self.username.lower()


    class Meta:
        verbose_name_plural = "Пользователи"

    #@property
    #def is_superuser(self):
    #    return self.is_superuser

    #@property
    #def is_staff(self):
    #    return self.is_staff

    def save(self, *args, **kwargs):

        super(myUser, self).save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=myUser)
def _post_delete(sender, instance, **kwargs):
    """Удаляем аватар когда удалён пользователь"""
    cache.delete_pattern("post_list_*")
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)


@app.task(name="deleteFile")
def deleteFile(file):
    try:
        os.remove(file)
    except:
        pass


@receiver(models.signals.pre_save, sender=myUser)
def _pre_save(sender, instance, **kwargs):
    """delete old file when avatar changed"""
    cache.delete_pattern("post_list_*")
    """if not instance.pk:
        return False

    try:
        old_file = myUser.objects.get(pk=instance.pk).avatar
    except myUser.DoesNotExist:
        return False

    new_file = instance.avatar
    if not str(old_file).split('/')[-1] == new_file and old_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
            #pass
            #deleteFile.apply_async((old_file.path,), countdown=1800)"""


class UserVotes(models.Model):
    """
    Количество голосов и их вес для юзера
    """
    votes_amount = models.IntegerField(default=10)
    weight = models.FloatField(default=0.25)
    VOTE_TYPE = (
                ("U", "Unlimited"),
                ("N", "Normal"),
                ("B", "Blocked"),
    )
    vote_type = models.CharField(max_length=1, choices=VOTE_TYPE, default="N")
    block_date = models.DateTimeField(blank=True, null=True)
    manual = models.BooleanField(default=False)
    user = models.ForeignKey('myUser', db_index=True)

    
class Post(ModelMeta, models.Model):
    """
    Модель поста
    """
    index_together = [
    ["id", "author", "category", "tags", "rating",
        "published", "private", "status", "main_tag"],
    ]
    title = models.CharField("Заголовок", max_length=150)
    private = models.BooleanField('NSFW', default=False)
    rateable = models.BooleanField("Разрешено голосовать", default=True)
    comments = models.BooleanField("Разрешено комментировать", default=True)
    can_complain = models.BooleanField("Разрешено жаловаться", default=True)
    locked = models.BooleanField("Не разрешать редактировать автору", default=False)
    def is_private(self):
        return self.private
    def is_rateable(self):
        return self.rateable
    def is_comments(self):
        return self.comments
    def is_locked(self):
        return self.locked
    description = models.TextField("Описание", max_length=700)
    text = models.TextField(max_length=3000)
    today = datetime.date.today()
    upload_path = str(today.year) + '/' + str(today.month)\
                                + '/' + str(today.day) + '/'
    post_image = models.FileField(upload_to=upload_path, blank=True,
                                   null=True, max_length=500,
                                  validators=[validate_post_image])
    post_image_gif = models.FileField(upload_to=upload_path, blank=True,
                                   null=True, max_length=500)
    image_url = models.URLField(null=True, blank=True, max_length=1000)
    main_image_srcset = models.TextField(null=True, blank=True,
                                        max_length=800)
    #main_image = JSONField(null = True, blank = True, max_length=1000)


    post_image.short_description = 'Image'
    post_thumbnail = models.ImageField(upload_to=upload_path,
                                       blank=True, null=True,
                                      max_length=500)
    post_thumb_ext = models.CharField(max_length = 6, blank = True, null = True)

    def get_image(self):
        return mark_safe('<img src="%s" class ="responsive-img center-align"/>'
                         % (self.post_thumbnail.url))
    get_image.short_description = 'Миниатюра'

    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)
    published = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               default=1,
                               on_delete=models.SET_DEFAULT)
    category = models.ForeignKey('Category')
    tags = models.ManyToManyField('Tag',
                            related_name='posts',
                            related_query_name='tag',
                            blank=True)
    rating = models.FloatField('Рейтинг', default=0.0)
    main_tag = models.ForeignKey('Tag', null=True, blank=True)
    url = models.CharField(max_length=330, blank=True)
    STATUS = (
                ("D", "Черновик/удалён"),
                ("P", "Опубликован"),
    )
    status = models.CharField("Статус", max_length=1, choices=STATUS, default="D")

    class Meta:
        ordering = ['-published']
        verbose_name_plural = "posts"

    _metadata = {
        'title': 'title',
        'description': 'description',
        'image': 'get_meta_image',
    }
    
    def get_meta_image(self):
        if self.post_image_gif:
            return self.post_image_gif.url
        elif self.post_image:
            return self.post_image.url
        else:
            return None

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return "/%s/%s-%i/" % (self.main_tag.url, self.url, self.id)

    def get_url(self):
        return "%s/%s-%i/" % (self.main_tag.url, self.url, self.id)

    def get_category(self):
        return self.category.get_url

    def get_tags_list(self):
        # return self.tags.values_list('name', flat=True)
        return self.tags.all()

    #def save(self, *args, **kwargs):
    #    super(Post, self).save(*args, **kwargs)


@receiver(models.signals.pre_delete, sender=Post)
def _post_delete(sender, instance, **kwargs):
    cache_str = "post_single_" + str(instance.id)
    cache.delete(cache_str)
    cache_str = "page_" + str(instance.category) + "*"
    cache.delete_pattern(cache_str)
    cache.delete_pattern("page_None_*")


@receiver(models.signals.pre_save, sender=Post)
def _post_save(sender, instance, **kwargs):
    cache_str = "post_single_" + str(instance.id)
    cache.delete_pattern(cache_str)
    cache_str = "page_" + str(instance.category) + "_*"
    cache.delete_pattern(cache_str)



class Category(models.Model):
    """
    Категории
    """
    index_together = [
        ["id", "name", "slug"],
    ]
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(max_length=400)
    slug = models.CharField("URL", blank=True, max_length=250)
    order = models.SmallIntegerField(blank=True, default=1)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['order']

    def __str__(self):
        return self.name

    def get_url(self):
        cat_url = slugify(self.name.lower(), allow_unicode=True)
        return "/%s/" % (cat_url)

    @classmethod
    def list(self):
        cat_list = self.objects.all().only("name", "order", "slug")
        return cat_list

    def save(self, *args, **kwargs):
        # if not self.slug:
        #self.slug = slugify(self.name.lower(), allow_unicode=True)
        super(Category, self).save(*args, **kwargs)


@receiver(models.signals.pre_delete, sender=Category)
def _post_delete(sender, instance, **kwargs):
    cache.delete("cat_list")


@receiver(models.signals.post_save, sender=Category)
def _post_save(sender, instance, **kwargs):
    cache.delete("cat_list")


class Tag(models.Model):
    """
    Тэги
    """
    index_together = [
        ["id", "name", "rating"],
    ]
    name = models.CharField(max_length=40, unique=True)
    url = models.CharField(max_length=140, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    private = models.BooleanField(default=False)
    rateable = models.BooleanField(default=True)
    description = models.TextField(max_length=700, blank=True, null=True)
    rating = models.FloatField('Рейтинг', default=0.0)

    class Meta:
        verbose_name_plural = "Тэги"
        ordering = ['name']

    def __str__(self):
        return self.name

    # def save(self, *args, **kwargs):
    #    if not self.url:
    #        self.url = slugify(self.name.lower())

    #    super(Tag, self).save(*args, **kwargs)


@receiver(models.signals.pre_delete, sender=Tag)
def post_delete(sender, instance, **kwargs):
    cache.delete("taglist")

class Comment(MPTTModel):
    """
    Комментарии
    """
    index_together = [
        ["id", "post", "rating", "author"],
    ]
    text = models.TextField(max_length=3700)
    author = models.ForeignKey('myUser', blank=True, null=True)
    post = models.ForeignKey('Post', blank=True, null=True)
    removed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children')
    rating = models.FloatField('Рейтинг', default=0.0)
    can_complain = models.BooleanField("Разрешено жаловаться", default=True)

    def __str__(self):
        return self.text

    class MPTTMeta:
        order_insertion_by = ['created']
        verbose_name_plural = "Comments"


@receiver(models.signals.pre_delete, sender=Comment)
def _post_delete(sender, instance, **kwargs):
    cache_str = "comment_" + str(instance.post.id)
    cache.delete(cache_str)


class Complain(models.Model):
    """
    Жалоба на пост или коммент
    """
    index_together = [
        ['score', 'users_complained']
    ]
    edited = models.DateTimeField(auto_now=True)
    post = models.ForeignKey('Post', blank=True, null=True,
                            on_delete=models.SET_NULL)
    comment = models.ForeignKey('Comment', blank=True, null=True,
                               on_delete=models.SET_NULL)
    score = models.FloatField(default=0, blank=True, null=True)
    users_complained = models.TextField(default='{}', max_length=2000, blank=True, null=True)
    
    def did_user_vote(self, user):
        if user.email in self.users_complained:
            return True
        else:
            return False

    class Meta:
        verbose_name_plural = "Жалобы"
        ordering = ['edited']
        
    def __str__(self):
        if self.post:
            return "{} - {}".format(self.post, self.id,)
        else:
            return "{} - {}".format(self.comment, self.id)
    