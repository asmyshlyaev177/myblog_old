from django.test import TestCase, TransactionTestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from django.test import Client

from blog.views import list

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
#  import unittest, time, re
import time, re
from blog.models import myUser

class SimpleTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        serialized_rollback = True

    def test_main_page(self):
        """
        Test for main page works correctly
        """

        request = self.factory.get('/')
        request.user = AnonymousUser()

        response = list(request)

        self.assertEqual(response.status_code, 200)

        # self.assertEqual(len(response.context['posts']), 3)

        str_resp1 = str.encode('<div class="post-thumbnail center-align">')
        str_resp2 = str.encode('<div class="flow-text post-description">')
        str_resp3 = str.encode('<a href="#" class="rate-icon rate-up" rate=1>')
        str_resp4 = str.encode('<div class="author">')
        str_resp5 = str.encode('<p>Sidebar 1</p>')
        self.assertIn(str_resp1, response.content)
        self.assertIn(str_resp2, response.content)
        self.assertIn(str_resp3, response.content)
        self.assertIn(str_resp4, response.content)
        self.assertIn(str_resp5, response.content)
