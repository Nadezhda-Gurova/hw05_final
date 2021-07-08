import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TaskPagesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.home_page = 'index'
        self.group_page = 'group'
        self.new_post_page = 'new_post'
        self.post_page = 'posts'
        self.post_edit_page = 'post_edit'
        self.profile = 'profile'
        self.test_slug = 'test-slug'
        self.test_slug_2 = 'test-slug-2'
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.image = SimpleUploadedFile("pic.gif", self.small_gif,
                                        content_type="image/gif")
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=self.test_slug,
            description='Тестовое описание группы')
        self.post = Post.objects.create(author=self.user,
                                        text='Тестовый текст поста',
                                        group=self.group,
                                        image=self.image)
        self.group_2 = Group.objects.create(
            title='Тестовый заголовок 2',
            slug=self.test_slug_2,
            description='Тестовое описание группы 2')
        self.post_2 = Post.objects.create(author=self.user,
                                          text='Тестовый текст поста 2',
                                          group=self.group_2,
                                          image=self.image)

    def test_pages_use_correct_template(self):
        """Функция проверяет шаблон при обращении к view-классам."""
        templates_pages_names = {
            'misc/index.html': reverse(self.home_page),
            'posts/group.html': (
                reverse(self.group_page, kwargs={'slug': self.test_slug})
            ),
            'posts/new.html': reverse(self.new_post_page),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_shows_correct_context(self):
        """Функция проверяет словарь контекста главной страницы."""
        response = self.authorized_client.get(reverse(self.home_page))
        first_object = response.context['page'][0]
        post_id = first_object.id
        post_text = first_object.text
        post_author = first_object.author
        post_group = first_object.group
        post_img = first_object.image
        self.assertEqual(post_id, self.post_2.id)
        self.assertEqual(post_text, self.post_2.text)
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_group, self.group_2)
        self.assertEqual(post_img, self.post_2.image)

    def test_group_page_shows_correct_context(self):
        """Функция проверяет словарь контекста страницы группы."""
        response = self.authorized_client.get(
            reverse(self.group_page, kwargs={'slug': self.test_slug}))
        test_group = response.context[self.group_page]
        test_post = response.context['page'][0]
        post_img = test_post.image
        self.assertEqual(test_group.title, self.group.title)
        self.assertEqual(test_post.text, self.post.text)
        self.assertEqual(post_img, self.post.image)

    def test_post_page_shows_correct_context(self):
        """Функция проверяет словарь контекста страницы поста."""
        response = self.authorized_client.get(reverse(self.post_page, kwargs={
            'username': self.user.username, 'post_id': self.post.id}))
        profile = {'author': self.post.author,
                   'number_of_posts': self.user.posts.count(),
                   'post': self.post}
        for value, expect in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expect)
        self.assertTrue(response.context['post'].image, self.image)

    def test_new_post_page_shows_correct_context(self):
        """Функция проверяет форму страницы создания поста."""
        response = self.authorized_client.get(reverse(self.new_post_page))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_shows_correct_context(self):
        """Функция проверяет форму страницы редактирования поста."""
        response = self.authorized_client.get(
            reverse(self.post_edit_page,
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id
                    }
                    ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_page_shows_correct_context(self):
        """Функция проверяет форму страницы пользователя."""
        response = self.authorized_client.get(reverse(self.profile, kwargs={
            'username': self.user.username}))
        test_post = response.context['page'][0]
        post_text = test_post.text
        post_author = test_post.author
        post_group = test_post.group
        post_img = test_post.image
        profile = {'author': self.user,
                   'number_of_posts': self.user.posts.count(),
                   }
        for value, expect in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expect)
        self.assertEqual(post_text, self.post_2.text)
        self.assertEqual(post_author, self.post_2.author)
        self.assertEqual(post_group, self.post_2.group)
        self.assertEqual(post_img, self.post_2.image)

    def test_post_on_page_index(self):
        """Функция проверяет, что при создании поста, он появляется на главной
        странице."""
        response = self.authorized_client.get(reverse(self.home_page))
        first_object = response.context['page'][0]
        post_text = first_object.text
        post_author = first_object.author
        post_group = first_object.group
        self.assertEqual(post_text, self.post_2.text)
        self.assertEqual(post_author, self.post_2.author)
        self.assertEqual(post_group, self.post_2.group)

    def test_post_on_page_group(self):
        """Функция проверяет, что при создании поста,
        он появляется странице группы."""
        response = self.authorized_client.get(
            reverse(self.group_page, kwargs={'slug': self.test_slug}))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)

    def test_post_on_other_page(self):
        """Функция проверяет, что созданный пост не попал в группу,
        для которой не был предназначен"""
        response = self.authorized_client.get(
            reverse(self.group_page, kwargs={'slug': self.test_slug_2}))
        first_object = response.context['page'][0]
        self.assertNotEqual(first_object, self.post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.home_page = 'index'
        cls.group_page = 'group'
        cls.profile = 'profile'
        cls.test_slug = 'test-slug'
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=cls.test_slug,
            description='Тестовое описание группы'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text=f'Тестовый пост номер - {i}',
                author=cls.user,
                group=cls.group,

            )

    def test_index_first_page_contains_ten_records(self):
        cache.clear()
        response = self.client.get(reverse(self.home_page))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context.get('page')), 10)

    def test_index_second_page_contains_three_records(self):
        cache.clear()
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse(self.home_page) + '?page=2')
        self.assertEqual(len(response.context.get('page')), 3)

    def test_group_first_page_contains_ten_records(self):
        cache.clear()
        response = self.client.get(
            reverse(self.group_page, kwargs={'slug': self.test_slug}))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context.get('page')), 10)

    def test_group_second_page_contains_three_records(self):
        cache.clear()
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(
            reverse(self.group_page, kwargs={'slug': self.test_slug})
            + '?page=2')
        self.assertEqual(len(response.context.get('page')), 3)

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(reverse(self.profile, kwargs={
            'username': self.user.username}))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context.get('page')), 10)

    def test_profile_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse(self.profile, kwargs={
            'username': self.user.username}) + '?page=2')
        self.assertEqual(len(response.context.get('page')), 3)


class CacheTest(TaskPagesTests, TestCase):

    def test_cache_index_check(self):
        cache.clear()
        response = self.client.get(reverse(self.home_page))
        page = response.context['page']
        paginator = page.paginator
        self.assertEqual(paginator.num_pages, 1)
        self.assertEqual(page[0].text, self.post_2.text)
        self.assertEqual(page[0].author, self.post_2.author)
        self.post_2.delete()
        response_2 = self.authorized_client.get(reverse(self.home_page))
        self.assertEqual(response.content, response_2.content)
        self.assertEqual(response_2.context, None)
        cache.clear()
        response_3 = self.authorized_client.get(reverse(self.home_page))
        self.assertNotEqual(response_3.context, None)
        self.assertEqual(response_3.context['page'][0].text, self.post.text)


class SubscriptionToAuthors(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_2 = User.objects.create_user(username='BorisKrasov')
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        self.user_3 = User.objects.create_user(username='Lars von Trier')
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(self.user_3)
        self.user_4 = User.objects.create_user(username='Jehanne Darc')
        self.authorized_client_4 = Client()
        self.authorized_client_4.force_login(self.user_4)
        self.follow_page = 'follow_index'
        self.post = Post.objects.create(author=self.user,
                                        text='Тестовый текст поста', )
        self.post_2 = Post.objects.create(author=self.user_4,
                                          text='Тестовый текст поста 4', )
        self.url_comment = reverse('add_comment', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id})

    def test_subscribe_to_user(self):
        Follow.objects.get_or_create(author=self.user, user=self.user_4)
        response = self.authorized_client_4.get(reverse(self.follow_page))
        following_author_posts = response.context['page']
        self.assertEqual(len(following_author_posts), self.user.posts.count())
        self.assertEqual(following_author_posts[0].text, self.post.text)
        self.assertEqual(following_author_posts[0].author, self.post.author)

    def test_unsubscribe_to_user(self):
        Follow.objects.filter(author=self.user).delete()
        response = self.authorized_client_4.get(reverse(self.follow_page))
        following_author_posts = response.context['page']
        self.assertEqual(len(following_author_posts), 0)

    def test_new_post_visible_to_subscribers(self):
        Follow.objects.get_or_create(author=self.user, user=self.user_2)
        Follow.objects.get_or_create(author=self.user, user=self.user_3)
        new_post = Post.objects.create(author=self.user,
                                       text='Создали новый пост')
        response = self.authorized_client_2.get(reverse(self.follow_page))
        following_author_post = response.context['page'][0]
        self.assertEqual(following_author_post.text, new_post.text)
        self.assertEqual(following_author_post.author, new_post.author)
        response_2 = self.authorized_client_3.get(reverse(self.follow_page))
        following_author_posts = response_2.context['page'][0]
        self.assertEqual(following_author_posts.text, new_post.text)
        self.assertEqual(following_author_posts.author, new_post.author)
        response_3 = self.authorized_client_4.get(reverse(self.follow_page))
        following_author_posts = response_3.context['page']
        self.assertEqual(len(following_author_posts), 0)

    def test_comments_authorized_user(self):
        reverse('add_comment', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id})
        form_data = {
            'text': 'Оставили новый комментарий',
        }
        response_2 = self.authorized_client.post(self.url_comment, follow=True,
                                                 data=form_data)
        self.assertContains(response_2, form_data['text'])
