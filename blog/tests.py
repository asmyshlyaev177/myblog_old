from django.test import (TestCase, TransactionTestCase,
                         RequestFactory, Client, LiveServerTestCase)
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import AnonymousUser, User

from blog.views import (list, get_good_posts, login,
                        sidebar, get_cat_list, comments,
                        addComment, tags, signup, dashboard,
                        my_posts, edit_post, add_post, rate_elem,
                        single_post, password_change, get_cat_list)

import unittest, re, time, os, json, random
from django.core.cache import cache
from bs4 import BeautifulSoup
from splinter import Browser
from blog.models import myUser, Post, Category, Tag
from blog.tasks import addPost

os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = '192.168.1.70:8092-9000'

def create_posts(self, from_num=1, to_num=20, private=False):
        self.cats = (self.cat1, self.cat2)
        self.tags = (self.tag1, self.tag2)
        for i in range(from_num, to_num+1):
            self.cat = random.choice(self.cats)
            self.tag = random.choice(self.tags)
            p = Post.objects.create(title = "post{}".format(str(i)),
                    description = "post description {}".format(str(i)),
                    status = "P", rating = float(i),
                    category = self.cat, author = self.user,
                    text = "post text {}".format(str(i)),
                    main_tag = self.tag, private=private,
                    url= self.tag.url)
            p.tags.add(self.tag)
            p.save()
                
class Test_pages_anon(TestCase):
    #serialized_rollback = True
    cache.clear()
    allow_database_queries = True
                
    @classmethod
    def setUpClass(cls):
        super(Test_pages_anon, cls).setUpClass()
        cache.clear()
        cls.user = myUser.objects.create(username='testuser', email='testmail@mail.ru')
        cls.user.set_password = 'testpass'
        cls.user.save()
        cls.cat1 = Category.objects.create(name="cat1", order=1,
						              description="cat1 desc")
        cls.cat2 = Category.objects.create(name="cat2", order=2,
						              description="cat2 desc")
        
        cls.tag1 = Tag.objects.create(name="tag1", url="tag1",
						      description="tag1 desc", category=cls.cat1)
        cls.tag2 = Tag.objects.create(name="tag2", url="tag2",
						      description="tag2 desc", category=cls.cat1)
        create_posts(cls, from_num=1, to_num=20)
        create_posts(cls, from_num=1, to_num=20, private=True)
    
    @classmethod
    def tearDownClass(cls):
        cache.clear()
        super(Test_pages_anon, cls).tearDownClass()
        
    def setUp(self):
        client = Client()
        

    
    def test_0_posts_created(self):
        assert Post.objects.all().count() == 40
        
    def page_content(self, category=None, best=False, tag=None):
        assert self.resp.status_code == 200
        assert self.cat1 in self.resp.context['cat_list']
        assert self.cat2 in self.resp.context['cat_list']
        self.good_posts = self.resp.context['good_posts']
        self.posts = self.resp.context['posts']
        assert len(self.posts) > 0
        assert len(self.good_posts) == 4
        if category:
            assert len(self.posts) == len([post for post in self.posts if post.category == category])
            assert len(self.good_posts) == len([post for post in self.good_posts if post.category == category])
        if tag:
            assert len(self.posts) == len([post for post in self.posts if tag in post.tags.all()])
        assert len([post for post in self.good_posts if post.rating > 5]) \
                == len(self.good_posts)
        if best:
            assert len([post for post in self.posts if post.rating > 3]) \
                    == len(self.posts)
        return True
    
    def test_1_list_root(self):
        self.resp = self.client.get('/')
        assert self.page_content() == True
        
    def test_2_list_cat1(self):
        self.resp = self.client.get('/cat/{}'.format(self.cat1.slug))
        assert self.page_content(self.cat1) == True
        
    def test_3_list_cat1_new(self):
        self.resp = self.client.get('/cat/{}/pop-all'.format(self.cat1.slug))
        assert self.page_content(self.cat1) == True
        
    def test_4_list_cat1_best(self):
        self.resp = self.client.get('/cat/{}/pop-best'.format(self.cat1.slug))
        assert self.page_content(self.cat1, best=True) == True
        
    def test_5_list_cat2(self):
        self.resp = self.client.get('/cat/{}'.format(self.cat2.slug))
        assert self.page_content(self.cat2) == True
        
    def test_6_list_cat2_new(self):
        self.resp = self.client.get('/cat/{}/pop-all'.format(self.cat2.slug))
        assert self.page_content(self.cat2) == True
        
    def test_7_list_cat2_best(self):
        self.resp = self.client.get('/cat/{}/pop-best'.format(self.cat2.slug))
        assert self.page_content(self.cat2, best=True) == True
        
    def test_8_tag1(self):
        self.resp = self.client.get('/{}'.format(self.tag1.url))
        assert self.page_content(tag=self.tag1) == True
        
    def test_9_tag2(self):
        self.resp = self.client.get('/{}'.format(self.tag2.url))
        assert self.page_content(tag=self.tag2) == True

    def test_10_single(self):
        post = random.choice(Post.objects.all())
        self.resp = self.client.get('/{}'.format(str(post.get_absolute_url())))
        assert self.resp.status_code == 200
        
    def test_11_signup_page(self):
        self.resp = self.client.get('/signup')
        assert self.resp.status_code == 200
        
    def test_11_login_page(self):
        self.resp = self.client.get('/login')
        assert self.resp.status_code == 200
        
    def test_12_pagination(self):
        self.resp = self.client.get('/?page=2')
        assert self.page_content() == True
        
    #def_test_20_list_private
    
    #Post.objects.all.delete()
    #create_posts(cls, from_num=1, to_num=2)
    #create_posts(cls, from_num=1, to_num=2, private=True)
    """      

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
        """