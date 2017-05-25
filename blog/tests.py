import glob
import os
import random
import shutil
from django.conf import settings
from django.core.cache import cache
from django.test import (TestCase, Client)
from django.utils.encoding import iri_to_uri
from blog.models import MyUser, Post, Category, Tag
from blog.tasks import add_post

os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = '192.168.1.70:8092-9000'


def create_posts(self, from_num=1, to_num=20, private=False):
    self.cats = (self.cat1, self.cat2)
    self.tags = (self.tag1, self.tag2)
    for i in range(from_num, to_num + 1):
        self.cat = random.choice(self.cats)
        self.tag = random.choice(self.tags)
        p = Post.objects.create(title="post{}".format(str(i)),
                                description="post description {}".format(str(i)),
                                status="P", rating=float(i),
                                category=self.cat, author=self.user,
                                text="post text {}".format(str(i)),
                                main_tag=self.tag, private=private,
                                url=self.tag.url)
        p.tags.add(self.tag)
        p.save()


def create_category(self):
    self.cat1 = Category.objects.create(name="cat1", order=1,
                                        description="cat1 desc")
    self.cat2 = Category.objects.create(name="cat2", order=2,
                                        description="cat2 desc")


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
    assert len([post for post in self.good_posts if post.rating > 5]) == len(self.good_posts)
    if best:
        assert len([post for post in self.posts if post.rating > 3]) \
               == len(self.posts)
    return True


class BaseTestMixin(object):
    serialized_rollback = True
    allow_database_queries = True

    @classmethod
    def setUpTestData(cls):
        cache.clear()
        cls.client = Client()
        cls.user = MyUser.objects.create(username='testuser', email='testmail@mail.ru')
        cls.user.set_password('testpass')
        cls.user.save()
        cls.cat1 = Category.objects.create(name="cat1", order=1,
                                           description="cat1 desc",
                                           slug="cat1")
        cls.cat2 = Category.objects.create(name="cat2", order=2,
                                           description="cat2 desc",
                                           slug="cat2")

        cls.tag1 = Tag.objects.create(name="tag1", url="tag1",
                                      description="tag1 desc", category=cls.cat1)
        cls.tag2 = Tag.objects.create(name="tag2", url="tag2",
                                      description="tag2 desc", category=cls.cat1)
        create_posts(cls, from_num=1, to_num=20)
        create_posts(cls, from_num=1, to_num=20, private=True)

    @classmethod
    def tearDownClass(cls):
        cache.clear()
        super(BaseTestMixin, cls).tearDownClass()


class TestAnonPages(BaseTestMixin, TestCase):
    def test_0_data_exist(self):
        assert Post.objects.all().count() == 40
        assert Category.objects.filter(slug="cat1").exists()
        assert Category.objects.filter(slug="cat2").exists()
        assert MyUser.objects.filter(email="testmail@mail.ru").exists()
        assert Tag.objects.filter(url="tag1").exists()
        assert Tag.objects.filter(url="tag2").exists()

    def test_1_list_root(self):
        self.resp = self.client.get('/')
        assert page_content(self) is True

    def test_2_list_cat1(self):
        self.resp = self.client.get('/cat/{}'.format(self.cat1.slug))
        assert page_content(self, self.cat1) is True

    def test_3_list_cat1_new(self):
        self.resp = self.client.get('/cat/{}/pop-all'.format(self.cat1.slug))
        assert page_content(self, self.cat1) is True

    def test_4_list_cat1_best(self):
        self.resp = self.client.get('/cat/{}/pop-best'.format(self.cat1.slug))
        assert page_content(self, self.cat1, best=True) is True

    def test_5_list_cat2(self):
        self.resp = self.client.get('/cat/{}'.format(self.cat2.slug))
        assert page_content(self, self.cat2) is True

    def test_6_list_cat2_new(self):
        self.resp = self.client.get('/cat/{}/pop-all'.format(self.cat2.slug))
        assert page_content(self, self.cat2) is True

    def test_7_list_cat2_best(self):
        self.resp = self.client.get('/cat/{}/pop-best'.format(self.cat2.slug))
        assert page_content(self, self.cat2, best=True) is True

    def test_8_tag1(self):
        self.resp = self.client.get('/{}'.format(self.tag1.url))
        assert page_content(self, tag=self.tag1) is True

    def test_9_tag2(self):
        self.resp = self.client.get('/{}'.format(self.tag2.url))
        assert page_content(self, tag=self.tag2) is True

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
        assert page_content(self) is True
        page2 = self.resp.context['posts']
        self.resp = self.client.get('/?page=3')
        page3 = self.resp.context['posts']
        assert page2 != page3
        self.resp = self.client.get('/?page=20')
        assert self.resp.status_code == 404

    def test_13_private_anon(self):
        post = Post.objects.filter(private=True)[0]
        self.resp = self.client.get(post.get_absolute_url())
        assert self.resp.status_code == 404

    def test_14_edit_anon(self):
        post = Post.objects.first()
        self.resp = self.client.get('/edit-post-{}'.format(post.id))
        assert self.resp.status_code == 302

    def test_15_dasboard(self):
        self.resp = self.client.get('/dashboard')
        assert self.resp.status_code == 302

    def test_16_change_password(self):
        self.resp = self.client.get('/password_change')
        assert self.resp.status_code == 302

    def test_17_my_posts(self):
        self.resp = self.client.get('/dashboard/my-posts')
        assert self.resp.status_code == 302

    def test_18_signup(self):
        self.resp = self.client.post('/signup',
                                     {'username': 'test123', 'email': 'test123@mail.ru', 'password1': 'test123',
                                      'password2': 'test123'})
        assert self.resp.status_code == 302
        assert MyUser.objects.filter(email='test123@mail.ru').exists()


class TestUserLogin(BaseTestMixin, TestCase):
    def setUp(self):
        self.resp = self.client.post('/login', {'username': 'testmail@mail.ru', 'password': 'testpass'})

    def test_0_data_exist(self):
        assert Post.objects.all().count() == 40
        assert Category.objects.filter(slug="cat1").exists()
        assert Category.objects.filter(slug="cat2").exists()
        assert MyUser.objects.filter(email="testmail@mail.ru").exists()
        assert Tag.objects.filter(url="tag1").exists()
        assert Tag.objects.filter(url="tag2").exists()

    def test_0_login(self):
        self.resp = self.client.get('/')
        assert "user_auth" in self.resp.rendered_content

    def test_1_list_root(self):
        self.resp = self.client.get('/')
        assert page_content(self) is True

    def test_2_list_cat1(self):
        self.resp = self.client.get('/cat/{}'.format(self.cat1.slug))
        assert page_content(self, self.cat1) is True

    def test_3_list_cat1_new(self):
        self.resp = self.client.get('/cat/{}/pop-all'.format(self.cat1.slug))
        assert page_content(self, self.cat1) is True

    def test_4_list_cat1_best(self):
        self.resp = self.client.get('/cat/{}/pop-best'.format(self.cat1.slug))
        assert page_content(self, self.cat1, best=True) is True

    def test_5_list_cat2(self):
        self.resp = self.client.get('/cat/{}'.format(self.cat2.slug))
        assert page_content(self, self.cat2) is True

    def test_6_list_cat2_new(self):
        self.resp = self.client.get('/cat/{}/pop-all'.format(self.cat2.slug))
        assert page_content(self, self.cat2) is True

    def test_7_list_cat2_best(self):
        self.resp = self.client.get('/cat/{}/pop-best'.format(self.cat2.slug))
        assert page_content(self, self.cat2, best=True) is True

    def test_8_tag1(self):
        self.resp = self.client.get('/{}'.format(self.tag1.url))
        assert page_content(self, tag=self.tag1) is True

    def test_9_tag2(self):
        self.resp = self.client.get('/{}'.format(self.tag2.url))
        assert page_content(self, tag=self.tag2) is True

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
        assert page_content(self) is True
        page2 = self.resp.context['posts']
        self.resp = self.client.get('/?page=3')
        page3 = self.resp.context['posts']
        assert page2 != page3
        self.resp = self.client.get('/?page=20')
        assert self.resp.status_code == 404

    def test_13_private_post(self):
        post = Post.objects.filter(private=True)[0]
        self.resp = self.client.get(post.get_absolute_url())
        assert self.resp.status_code == 200

    def test_14_edit_post(self):
        post = Post.objects.first()
        self.resp = self.client.get('/edit-post-{}'.format(post.id))
        assert self.resp.status_code == 200

    def test_15_dasboard(self):
        self.resp = self.client.get('/dashboard')
        assert self.resp.status_code == 200

    def test_16_change_password(self):
        self.resp = self.client.get('/password_change')
        assert self.resp.status_code == 200

    def test_17_my_posts(self):
        self.resp = self.client.get('/dashboard/my-posts')
        assert self.resp.status_code == 200

    def test_18_add_post(self):
        self.resp = self.client.get('/add-post')
        assert self.resp.status_code == 200

    def test_19_logout(self):
        self.resp = self.client.get('/logout?next=/')
        assert self.resp.status_code == 302


class TestAddPost(TestCase):
    allow_database_queries = True
    serialized_rollback = True

    def setUp(self):
        cache.clear()
        self.user = MyUser.objects.create(username='testuser', email='testmail@mail.ru')
        self.user.set_password('testpass')
        self.user.save()
        create_category(self)
        self.client = Client()
        self.tag1 = Tag.objects.create(name="tag1", url="tag1",
                                       description="tag1 desc", category=self.cat1)
        self.tag2 = Tag.objects.create(name="tag2", url="tag2",
                                       description="tag2 desc", category=self.cat1)
        self.post = Post.objects.create(title="testpost", status="D",
                                        description="post desc",
                                        category=self.cat1, author=self.user,
                                        text="123", main_tag=self.tag1, url=self.tag1.url
                                        )
        self.post.tags = [self.tag1]
        self.post.save()
        for file in glob.glob(os.path.join('test_media', '*.*')):
            shutil.copy(file, 'blog/static/media/2017/1/1/')
            # management.call_command('makemigrations', interactive=False)
            # management.call_command('migrate', interactive=False)

    def tearDown(self):
        cache.clear()
        try:
            for file in glob.glob(os.path.join('blog/static/media/2017/1/1/', '*.*')):
                os.remove(file)
        except:
            pass

    def add_post(self):
        add_post(self.post.id, [self.tag1.name], False)
        self.post.refresh_from_db()
        assert self.post.status == "P"
        assert self.tag1 in self.post.tags.all()
        assert self.post.get_absolute_url() == "/{}/{}-{}/".format(self.post.main_tag.url, self.post.url, self.post.id)
        assert self.post.description == "post desc"
        assert "123" in self.post.text
        assert self.post.author == self.user
        assert self.post.title == "testpost"
        return True

    def test_0_add_post(self):
        self.client = Client()
        self.resp = self.client.post('/add-post', {'title': 'testpost1', 'status': 'D',
                                                   'description': 'post desc', 'category': str(self.cat1.id),
                                                   'text': '123', 'tag': str(self.tag1.name),
                                                   'hidden_tags': str(self.tag1.name)})
        assert self.resp.status_code == 302
        self.post = Post.objects.get(title="testpost")
        assert self.add_post()

    def test_1_add_post_jpg(self):
        self.post.post_image = "{}/blog/static/media/2017/1/1/test_pic.jpg".format(settings.BASE_DIR)
        self.post.save()
        assert self.add_post()
        self.resp = self.client.get(self.post.get_absolute_url())
        assert "test_pic-1366.jpg" in self.resp.rendered_content
        assert "test_pic-480.jpg" in self.resp.rendered_content
        assert "test_pic-800.jpg" in self.resp.rendered_content
        assert "test_pic.jpg" in self.resp.rendered_content

    def test_2_add_post_gif(self):
        self.post.post_image = "{}/blog/static/media/2017/1/1/гифка-девушка-азиаточка-3210229.gif".format(
            settings.BASE_DIR)
        self.post.save()
        assert self.add_post()
        self.resp = self.client.get(self.post.get_absolute_url())
        assert "гифка-девушка-азиаточка-3210229-3.webm" in self.resp.rendered_content
        assert os.path.isfile("blog/static/media/2017/1/1/гифка-девушка-азиаточка-3210229-3.webm")

    def test_3_add_post_webm(self):
        self.post.post_image = "{}/blog/static/media/2017/1/1/гифки-япония-3174994-6501.webm".format(settings.BASE_DIR)
        self.post.save()
        assert self.add_post()
        self.resp = self.client.get(self.post.get_absolute_url())
        assert iri_to_uri("гифки-япония-3174994-6501.webm") in self.resp.rendered_content
        assert os.path.isfile("blog/static/media/2017/1/1/гифки-япония-3174994-6501.webm")
