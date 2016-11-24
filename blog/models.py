# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
										BaseUserManager)
from slugify import slugify, SLUG_OK
from django.utils import timezone
import datetime
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFit
from imagekit import ImageSpec, register
from django.utils.safestring import mark_safe
import re, os
from django.dispatch import receiver
from django.conf import settings
from bs4 import BeautifulSoup
from PIL import Image
#from unidecode import unidecode
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, urlretrieve, Request

from django.conf import settings
#import socket #timeout just for test
#socket.setdefaulttimeout(10)

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
	rateable = models.BooleanField(default = True)
	def user_directory_path(instance, filename):
	# file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
		return 'avatars/{0}/{1}'.format(instance.username, filename)

	avatar = ProcessedImageField(upload_to=user_directory_path,
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
		user_rating, _ = RatingUser.objects.get_or_create(user=self)
		user_rating.user = self
		user_rating.rating = 0.0
		user_votes, _ = UserVotes.objects.get_or_create(user=self)
		user_votes.user = self
		user_rating.save()
		user_votes.save()

		super(myUser, self).save(*args, **kwargs)

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

class Thumbnail(ImageSpec):
	processors = [ResizeToFit(640, 480)]
	format = 'JPEG'
	options = {'quality': 85}

register.generator('blog:thumbnail', Thumbnail)

class Rating(models.Model):
	#ratingid = models.IntegerField(unique = True)
	rating = models.FloatField(default=0.0)
	votes = models.IntegerField(default = 0)

	class Meta:
		abstract = True

class RatingPost(Rating):
	post = models.ForeignKey('Post')
	month = models.FloatField(blank = True, null = True)
	week = models.FloatField(blank = True, null = True)

class RatingTag(Rating):
	tag = models.ForeignKey('Tag')
	month = models.FloatField(blank = True, null = True)
	week = models.FloatField(blank = True, null = True)

class RatingUser(Rating):
	user = models.ForeignKey('myUser')


class Vote(models.Model):
	#vote_id = models.IntegerField(blank = True, null = True)
	rate = models.BooleanField()
	score = models.FloatField(null = True, blank = True)
	created = models.DateTimeField(auto_now_add=True) #for celery
	class Meta:
		abstract = True

class VotePost(Vote):
	post = models.ForeignKey('Post')

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
	user = models.ForeignKey('myUser')


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
	image_url = models.URLField(null=True, blank=True, max_length=300)

	def post_image_gif(self):
		if self.post_image.path != "":
			ext = []
			ext = self.post_image.path.split('.')
			if ext[-1] == "gif":
				return True
			else:
				return False

	post_image.short_description = 'Image'
	post_thumbnail = ImageSpecField(source='post_image',
								processors=[ResizeToFit(640, 480)],
								format='JPEG',
								options={'quality': 85})
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

@receiver(models.signals.post_delete, sender=Post)
def delete_image_and_thumb(sender, instance, **kwargs):
	# удаляем файлы картинок при удалении поста
	img_links = re.findall\
		(r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*.jpg)", instance.text)
	for img in img_links:
		img_path = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}'.format(img[0], img[1],img[2],img[3])
		if os.path.isfile(img_path):
			os.remove(img_path)



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

	class Meta:
		verbose_name_plural = "tags"
	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.url:
			self.url = slugify(self.name.lower())

		super(Tag, self).save(*args, **kwargs)
