from django.test import (TestCase, TransactionTestCase, 
                         RequestFactory, Client, LiveServerTestCase)
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import AnonymousUser, User

from blog.views import (list, get_good_posts, login,
                        sidebar, get_cat_list, comments,
                        addComment, tags, signup, dashboard,
                        my_posts, edit_post, add_post, rate_elem,
                        single_post, password_change, get_cat_list)

import unittest, re, time, os
from django.core.cache import cache
#from selenium import webdriver, selenium
from splinter import Browser
from blog.models import myUser

os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = '192.168.1.70:8092-9000'

class MyTest(LiveServerTestCase):
    fixtures = ['db.json']
    serialized_rollback = True
    cache.clear()
    
    def setUp(self):
        remote_server_url = 'http://192.168.1.68:4444/wd/hub'
        self.browser = Browser(driver_name="remote",
            url=remote_server_url,
            browser='firefox',
            platform="Windows 7")
        self.browser.visit(self.live_server_url)
        time.sleep(1)
        

    def tearDown(self):
        self.browser.quit()


    def test_0_pages(self):
        """
        Test for main page works correctly
        """
        print("Test main page")
        assert self.browser.status_code.code == 200
        assert '<div class="content">' in self.browser.html
        assert '<div class="post z-depth-1">' in self.browser.html
        assert '<div class="sidebar col' in self.browser.html
        self.browser.find_by_css('.rate-up').click()
        time.sleep(1)
        assert self.browser.is_element_present_by_id('id_username')
        
        print("Test categories")
        self.browser.visit(self.live_server_url)
        categories = get_cat_list().values_list('slug', flat=True)
        for cat in categories:
            self.browser.click_link_by_href('/cat/'+str(cat))
            time.sleep(2)
            cat_str = '<a href="/cat/{}/" class="post-category'\
                        .format(cat)
            assert cat_str in self.browser.html
            assert '<div class="content">' in self.browser.html
            assert '<div class="sidebar col' in self.browser.html
            self.browser.click_link_by_id('pop-all')
            time.sleep(1)
            assert '<div class="post z-depth-1">' in self.browser.html
            self.browser.click_link_by_id('pop-best')
            time.sleep(1)
            assert '<div class="post z-depth-1">' in self.browser.html
        
        print("Test single page")
        self.browser.visit(self.live_server_url)
        self.browser.click_link_by_href('/others/test-6518/')
        time.sleep(2)
        assert '<div class="content">' in self.browser.html
        assert '<div class="sidebar col' in self.browser.html
        assert 'asda' in self.browser.html
        assert '<div class="card-content comment_text">' in self.browser.html
        assert '<h1 class="center-align post-title">' in self.browser.html
        
        print("Test page link from sidebar")
        self.browser.visit(self.live_server_url)
        self.browser.find_by_css('body div.row div.sidebar.col.l4.offset-l1.hide-on-med-and-down\
                                div.sidebar-inner div:nth-child(2) a').click()
        time.sleep(2)
        assert '<div class="content">' in self.browser.html
        assert '<div class="sidebar col' in self.browser.html
        assert '<h1 class="center-align post-title">' in self.browser.html
        

    def test_4_signup_login(self):
        print("Test signup")
        self.browser.find_by_id('user-menu').click()
        self.browser.find_link_by_href('/signup').click()
        time.sleep(2)
        self.browser.fill('username', 'testuser')
        self.browser.fill('email', 'testmail@mail.ru')
        self.browser.fill('password1', 'Poison123')
        self.browser.fill('password2', 'Poison123')
        self.browser.find_by_value('Зарегистрироваться').click()
        time.sleep(2)
        assert self.browser.is_text_present('Вы успешно зарегистрировались!')
        
        print("Test login")
        self.browser.find_by_id('user-menu').click()
        self.browser.find_by_id('login-link').click()
        self.browser.fill('username', 'testmail@mail.ru')
        self.browser.fill('password', 'Poison123')
        self.browser.find_by_value('Login').click()
        time.sleep(2)
        assert self.browser.is_element_present_by_id('user_auth')
        

