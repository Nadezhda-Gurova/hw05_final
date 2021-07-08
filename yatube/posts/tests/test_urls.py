from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class TaskURLTests(TestCase):
    User = get_user_model()

    @classmethod
    def setUp(self):
        cache.clear()
        super().setUpClass()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='AndreyG')
        self.user_2 = User.objects.create_user(username='TatianaK')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client.force_login(self.user_2)
        self.homepage = '/'
        self.test_slug = 'test-slug'
        self.group_page = f'/group/{self.test_slug}/'
        self.new_page = '/new/'
        self.page_not_found = '/404/'
        self.page_server_error = '/500/'
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=self.test_slug,
            description='Тестовое описание группы'
        )
        self.post = Post.objects.create(author=self.user_2,
                                        text='Тестовый текст поста',
                                        group=self.group)

    def test_status_code_for_authorized_client(self):
        pages = {
            self.homepage: HTTPStatus.OK,
            self.group_page: HTTPStatus.OK,
            self.new_page: HTTPStatus.OK,
            f'/{self.user_2.username}/': HTTPStatus.OK,
            f'/{self.user_2.username}/{self.post.id}/': HTTPStatus.OK,
            f'/{self.user_2.username}/{self.post.id}/edit/': HTTPStatus.OK,
        }
        for url_address, response_code in pages.items():
            with self.subTest(address=url_address):
                response = self.authorized_client.get(url_address)
                self.assertEqual(response.status_code, response_code)

    def test_status_code_for_guest_client(self):
        pages = {
            self.homepage: HTTPStatus.OK,
            self.group_page: HTTPStatus.OK,
            self.new_page: HTTPStatus.FOUND,
            f'/{self.user_2.username}/': HTTPStatus.OK,
            f'/{self.user_2.username}/{self.post.id}/': HTTPStatus.OK,
            f'/{self.user_2.username}/{self.post.id}/edit/':
                HTTPStatus.FOUND,
            self.page_not_found: HTTPStatus.NOT_FOUND,
        }
        for url_address, response_code in pages.items():
            with self.subTest(address=url_address):
                response = self.guest_client.get(url_address)
                self.assertEqual(response.status_code, response_code)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'misc/index.html': self.homepage,
            'posts/group.html': self.group_page,
            'posts/new.html': self.new_page,
            'posts/post.html': f'/{self.user_2.username}/{self.post.id}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_edit_redirect_anonymous_on_post(self):
        response = self.guest_client.get(
            f'/{self.user_2.username}/{self.post.id}/edit/')
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{self.user_2.username}/{self.post.id}/edit/')
