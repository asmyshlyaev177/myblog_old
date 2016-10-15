from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager)
from django.utils.text import slugify
from django.utils import timezone
import datetime
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFit
from django.utils.safestring import mark_safe
import re
import os
from django.dispatch import receiver
from django.conf import settings
from bs4 import BeautifulSoup
from PIL import Image

thumb_img_size = 640, 480

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
    ["id", "username", "avatar"],
    ]
    username = models.CharField("Username", max_length=30,
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
    moderated = models.BooleanField("Moderated", default=True)
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

@receiver(models.signals.post_delete, sender=myUser)
def delete_avatar(sender, instance, **kwargs):
    """delete avatar when delete user"""
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)

@receiver(models.signals.pre_save, sender=myUser)
def delete_old_avatar(sender, instance, **kwargs):
    """delete old file when avatar changed"""
    if not instance.pk:
        return False

    try:
        old_file = myUser.objects.get(pk=instance.pk).avatar
    except myUser.DoesNotExist:
        return False

    new_file = instance.avatar
    if not old_file == new_file and old_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

class Post(models.Model):
    index_together = [
    ["title", "description", "post_thumbnail", "author", "category",
     "url", "published", "status"],
    ]
    title = models.CharField(max_length=150)
    #description = RichTextField(max_length = 500, config_name = "description",
    #                            blank=True)
    description = models.CharField(max_length=150)
    #text = RichTextUploadingField(config_name = "post")
    text = models.TextField()
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
                                        related_query_name='tag',
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
    def get_tags_list(self):
        return self.tags.values_list('name', flat=True)
    def save(self, force_insert=False, force_update=False):
        """Resize img if it is bigger than thumb"""
        soup = BeautifulSoup(self.text) #текст поста
        img_links = soup.find_all("img") #ищем все картинки

        for i in img_links: # для каждой
        	# находим ссылку и файл и вых. файл
        	link = re.search(r"/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<file>\S*)\.(?P<ext>\w*)", str(i))
        	file = 'c:\\django\\python3\\myblog\\blog\\static\\media\\{}\\{}\\{}\\{}.{}'\
        	.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
        	file_out = 'c:\\django\\python3\\myblog\\blog\\static\\media\\{}\\{}\\{}\\{}-thumbnail.{}'\
        	.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
        	if os.path.isfile(file):
        		# если файл существует
        		img_class = []
        		for j in i['class']:
        			img_class.append(j) #находим классы картинки
        		#всё кроме того что надо добавить или заменить
        		img_class = [item for item in img_class if not item.startswith('img-responsive')]
        		img_class.append('img-responsive') #добавляем нужный класс
        		i['class'] = img_class # присваиваем
        		# если картинка больше нужного размера создаём миниатюру
        		w,h = Image.open(file).size
        		if w > thumb_img_size[0]:
        			img = Image.open(file)
        			img.thumbnail(thumb_img_size)
        			img.save(file_out) # сохраняем
        			i['src'] = '/media/{}/{}/{}/{}-thumbnail.{}'.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
        			a_tag = soup.new_tag("a")
        			# оборачиваем в ссылку на оригинал
        			a_tag['href'] = '/media/{}/{}/{}/{}.{}'.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
        			a_tag['data-gallery'] = ""
        			i = i.wrap(a_tag)

        # выравниваем видео по центру
        ifr_links = soup.find_all("iframe")
        ifr_class = []
        for i in ifr_links:
            for j in i['class']:
                ifr_class.append(j)
            ifr_class = [item for item in ifr_class if not item.startswith('center-block')]
            ifr_class.append('center-block') 
            i['class'] = ifr_class

        self.text = str(soup.body.next)

        super(Post, self).save(force_insert, force_update)

@receiver(models.signals.post_delete, sender=Post)
def delete_image_and_thumb(sender, instance, **kwargs):
    # удаляем файлы картинок при удалении поста

    img_links = re.findall\
        (r"/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<file>\S*.jpg)", instance.text)
    for img in img_links:
        img_path = 'c:\\django\\python3\\myblog\\blog\\static\\media\\{}\\{}\\{}\\{}'.format(img[0], img[1],img[2],img[3])
        if os.path.isfile(img_path):
            os.remove(img_path)


    """delete image when post deleted"""
    if instance.post_image:
        if os.path.isfile(instance.post_image.path):
            try:
                os.remove(instance.post_image.path)
            except FileNotFoundError:
                return False
    if instance.post_thumbnail:
        if os.path.isfile(instance.post_thumbnail.path):
            try:
                os.remove(instance.post_thumbnail.path)
            except FileNotFoundError:
                return False ##подозрительная хрень


@receiver(models.signals.pre_save, sender=Post)
def delete_old_image_and_thumb(sender, instance, **kwargs):
    """delete old file when thumbnail changed"""
    if not instance.pk:
        return False

    try:
        old_file = Post.objects.get(pk=instance.pk).post_image
    except Post.DoesNotExist:
        return False

    new_file = instance.post_image

    if not old_file == new_file and old_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

    try:
        old_file = Post.objects.get(pk=instance.pk).post_thumbnail
    except Post.DoesNotExist:
        return False

    new_file = instance.post_thumbnail
    if not old_file == new_file and old_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

class Category(models.Model):
    index_together = [
    ["id","name", "order", "slug"],
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
        cat_list = self.objects.all().only("name","order")\
            .order_by('order','name')
        return cat_list
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Category,self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    def __str__(self):
        return self.name
