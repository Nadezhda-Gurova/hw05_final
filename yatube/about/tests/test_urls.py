from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.about_author = 'about:author'
        self.about_tech = 'about:tech'

    def test_about_url_exists_at_desired_location(self):
        response = self.guest_client.get(reverse(self.about_author))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        response = self.guest_client.get(reverse(self.about_author))
        self.assertTemplateUsed(response, 'about/author.html')

    def test_tech_url_exists_at_desired_location(self):
        response = self.guest_client.get(reverse(self.about_tech))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech_url_uses_correct_template(self):
        response = self.guest_client.get(reverse(self.about_tech))
        self.assertTemplateUsed(response, 'about/tech.html')
