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
import re
import os
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
	main_tag = models.CharField(max_length=33, blank=True)
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
		cat_url = slugify(self.main_tag)
		#post_url = slugify(unidecode(self.title))
		return "/%s/%s-%i/" % (cat_url, self.url, self.id)
	def get_category(self):
		return self.category.get_url
	def get_tags_list(self):
		#return self.tags.values_list('name', flat=True)
		return self.tags.all()
	def save(self, force_insert=False, force_update=False):
		"""Resize img if it is bigger than thumb"""
		soup = BeautifulSoup(self.text) #текст поста
		img_links = soup.find_all("img") #ищем все картинки

		if len(img_links) != 0:
			for i in img_links: # для каждой
				# находим ссылку и файл и вых. файл
				del i['style'] #удаляем стиль
				link = re.search(r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*)\.(?P<ext>\w*)", str(i))
				file = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}.{}'\
				.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
				file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-thumbnail.{}'\
				.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
				if os.path.isfile(file):
					# если файл существует
					#img_class = []
					#for j in i['class']:
					'''if i.has_attr('class'):
						img_class.append(i['class']) #находим классы картинки
					#всё кроме того что надо добавить или заменить
					img_class = [item for item in img_class if not item.startswith('img-responsive')]
					img_class.append('img-responsive') #добавляем нужный класс'''
					#i['class'] = img_class # присваиваем
					i['class'] = 'responsive-img'
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
		if len(img_links) != 0:
			for i in ifr_links:
				for j in i['class']:
					ifr_class.append(j)
				ifr_class = [item for item in ifr_class if not item.startswith('center-align')]
				ifr_class.append('center-align')
				i['class'] = ifr_class

		#text = ""
		#for i in soup.body:
		#	text += str(i)
		#self.text = text
		soup.html.unwrap()
		soup.head.unwrap()
		soup.body.unwrap()
		self.text = soup.prettify()

		#image from url
		if self.image_url:
			today = datetime.date.today()
			upload_path1 = '/root/myblog/myblog/blog/static/media/' + \
			str(today.year)+'/' +str(today.month)+'/'+str(today.day)+'/'
			upload_path = str(today.year)+'/' +str(today.month)+'/'+str(today.day)+'/'
			filename = urlparse(self.image_url).path.split('/')[-1]
			save_path = os.path.join(upload_path1, filename)
			user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
			headers = { 'User-Agent' : user_agent }
			values = {'name' : 'Alex',
          				'location' : 'Moscow',}
			data = urlencode(values)
			data = data.encode('ascii')
			try:
				req = Request(self.image_url, data, headers)
				os.makedirs(os.path.dirname(save_path), exist_ok=True)
				with urlopen(req, timeout=3) as response, open(save_path, 'wb') as out_file:
					data = response.read()
					out_file.write(data)
				self.post_image = os.path.join(upload_path, filename)
			except:
				pass
			self.image_url = ""

		post_rating, _ = RatingPost.objects.get_or_create(post=self)
		post_rating.post = self
		post_rating.rating = 0.0
		post_rating.save()

		super(Post, self).save(force_insert, force_update)

@receiver(models.signals.post_delete, sender=Post)
def delete_image_and_thumb(sender, instance, **kwargs):
	# удаляем файлы картинок при удалении поста

	img_links = re.findall\
		(r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*.jpg)", instance.text)
	for img in img_links:
		img_path = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}'.format(img[0], img[1],img[2],img[3])
		if os.path.isfile(img_path):
			os.remove(img_path)


	"""delete image when post deleted"""
	"""if instance.post_image:
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
				return False ##подозрительная хрень"""


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

		tag_rating, _ = RatingTag.objects.get_or_create(tag=self)
		tag_rating.tag = self
		tag_rating.rating = 0
		tag_rating.save()

		super(Tag, self).save(*args, **kwargs)
