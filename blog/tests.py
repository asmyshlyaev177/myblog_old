from django.test import (TestCase, TransactionTestCase,
                         RequestFactory, Client, LiveServerTestCase)
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import AnonymousUser, User

from blog.views import (list, get_good_posts, login,
                        sidebar, get_cat_list, comments,
                        addComment, tags, signup, dashboard,
                        my_posts, edit_post, add_post, rate_elem,
                        single_post, password_change, get_cat_list)

import unittest, re, time, os, json
from django.core.cache import cache
from bs4 import BeautifulSoup
from splinter import Browser
from blog.models import myUser, Post
from blog.tasks import addPost

os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = '192.168.1.70:8092-9000'


class MyTest(LiveServerTestCase):
    fixtures = ['db.json']
    serialized_rollback = True
    cache.clear()

    def setUp(self): 	
        self.c = Browser('django')
         	
    def tearDown(self): 	
        self.c.quit() 
        
    def test_0_main_page_and_single_page(self):
        """
        Test for main page works correctly
        """
        print("Test main page")
        c = Client()
        self.resp = c.get('/')
        assert self.resp.status_code == 200
        assert b'<div class="post z-depth-1">' in self.resp.content
        assert b'<div class="sidebar col' in self.resp.content
        url = self.resp.context['posts'][0].get_absolute_url()
        self.resp = c.get(url)
        assert self.resp.status_code == 200
        b'<div class="post z-depth-1">' in self.resp.content
        b'<div id="Comments_title">' in self.resp.content
        b'<div class="post-sidebar z-depth-1">' in self.resp.content

    def test_1_categories(self):
        categories = get_cat_list().values_list('slug', flat=True)
        c = Client()
        for cat in categories:
            self.resp = c.get('/cat/{}'.format(cat))
            assert self.resp.context['posts'].count() == 3
            assert 'good_posts' in self.resp.context
            assert b'sidebar-inner' in self.resp.content

    def test_2_signup(self):
        print("Test signup")
        self.c.visit('/signup')
        self.c.fill('username', 'testuser')
        self.c.fill('email', 'test@mail.ru')
        self.c.fill('password1', 'Poison123')
        self.c.fill('password2', 'Poison123')
        self.c.find_by_value('Зарегистрироваться').click()
        assert self.c.status_code.code == 200
        assert "Вы успешно" in self.c.html
        assert myUser.objects.filter(email='test@mail.ru').exists()
        
        print("Test login")
        self.c.find_by_id('user-menu').click()
        self.c.find_by_id('login-link').click()
        self.c.fill('username', 'test@mail.ru')
        self.c.fill('password', 'Poison123')
        self.c.find_by_value('Login').click()
        assert self.c.status_code.code == 200
        userid = myUser.objects.get(email='test@mail.ru').id
        auth_str = '<p id="user_auth" style="display: none;" user="{}"></p>'.format(userid)
        assert auth_str in str(BeautifulSoup(self.c.html).find(id="user_auth"))
        myUser.objects.get(email='test@mail.ru').delete()
        
    def test_3_tags(self):
        print("Test tags list")
        self.c.visit('/tags.json')
        assert len(json.loads(self.c.html)) > 2
        
        
    def test_4_add_post(self):
        print("Test add post")
        user = myUser.objects.create(username="testuser", email = 'test@mail.ru')
        user.set_password('Poison123')
        user.save()
        self.c.visit('/')
        self.c.find_by_id('user-menu').click()
        self.c.find_by_id('login-link').click()
        self.c.fill('username', 'test@mail.ru')
        self.c.fill('password', 'Poison123')
        self.c.find_by_value('Login').click()
        self.c.find_by_id('user-menu').click()
        self.c.find_link_by_href('/add-post').click()
        assert '<input id="id_title" maxlength="150" name="title"' in self.c.html
        self.c.fill('title', 'testpost123')
        self.c.select('category', '1')
        self.c.attach_file('post_image', 'test_pic.jpg')
        self.c.fill('description', 'test description')
        self.c.fill('text', 'test text')
        self.c.fill('hidden_tags', 'test tag')
        self.c.find_by_value('Add Post').click()
        assert Post.objects.filter(title='testpost123').exists()
        postid = Post.objects.get(title='testpost123').id
        addPost(postid, ["test tag"], False)
        url = Post.objects.get(id=postid).get_absolute_url()
        self.c.visit(url)
        assert self.c.status_code.code == 200
        assert '<div class="post z-depth-1">' in self.c.html
        assert '<div id="Comments_title">' in self.c.html
        assert '<div class="post-sidebar z-depth-1">' in self.c.html
        assert 'testpost123' in self.c.html
        assert 'test description' in self.c.html
        assert 'test text' in self.c.html
        assert 'test tag' in self.c.html
        s = re.findall(r"/media/[\d]{4}/[\d]{1,2}/[\d]{1,2}/test_pic_(.*)-(1366|800|480).jpg", self.c.html)
        assert len(s) > 0 
        
    """def test_5_edit_post(self):
        self.post = Post.objects.first()
        self.user = myUser.objects.create(username="testuser", email = 'test@mail.ru')
        self.user.set_password('Poison123')
        self.user.moderator_of_categories = [self.post.category]
        self.user.save()
        
        self.c.visit('/')
        self.c.find_by_id('user-menu').click()
        self.c.find_by_id('login-link').click()
        self.c.fill('username', 'test@mail.ru')
        self.c.fill('password', 'Poison123')
        self.c.find_by_value('Login').click()
        time.sleep(2)
        
        url = '/edit-post-{}'.format(self.post.id)
        self.c.visit(url)
        self.c.fill('title', 'testpost456')
        self.c.select('category', '2')
        self.c.fill('description', 'test description2')
        self.c.fill('text', 'test text2')
        self.c.fill('hidden_tags', 'test tag2')
        self.c.find_by_value('Save').click()
        
        assert Post.objects.filter(title='testpost456').exists()
        postid = Post.objects.get(title='testpost456').id
        addPost(postid, ["test tag2"], False)
        url = Post.objects.get(id=postid).get_absolute_url()
        
        self.c.visit(url)
        assert self.c.status_code.code == 200
        assert '<div class="post z-depth-1">' in self.c.html
        assert '<div id="Comments_title">' in self.c.html
        assert '<div class="post-sidebar z-depth-1">' in self.c.html
        assert 'testpost456' in self.c.html
        assert 'test description2' in self.c.html
        assert 'test text2' in self.c.html
        assert 'test tag2' in self.c.html"""