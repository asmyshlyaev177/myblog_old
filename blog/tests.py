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

#os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = '192.168.1.70:8092-9000'

class MyTest(TestCase):
    fixtures = ['db.json']
    serialized_rollback = True
    cache.clear()
    
    def setUp(self):
        #remote_server_url = 'http://192.168.1.68:4444/wd/hub'
        #self.browser = Browser(driver_name="remote",
        #    url=remote_server_url,
        #    browser='firefox',
        #    platform="Windows 7")
        #self.browser.visit(self.live_server_url)
        #time.sleep(1)
        c = Client()
        

    #def tearDown(self):
        #self.browser.quit()


    def test_0_main_page(self):
        """
        Test for main page works correctly
        """
        print("Test main page")
        resp = c.get('/signup')
        assert resp.status_code == 200
        

    def test_4_signup_login(self):
        print("Test signup")
        
        

