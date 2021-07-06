import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User
from django.conf import settings

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.text = 'Тестовый текст поста'
        cls.post = Post.objects.create(text=cls.text, author=cls.user)
        cls.group = Group.objects.create(title='Тестовый заголовок',
                                         slug='test-slug')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_form(self):
        post_count = Post.objects.count()
        form_data = {
            'text': self.text,
            'group': self.group.id,
            'image': self.image
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        cache.clear()
        self.authorized_client.post(reverse('new_post'), data=form_data)
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(text=form_data['text'],
                                            group=form_data['group'],
                                            image='posts/small.gif').exists())
        self.assertTrue(response.context['page'][0].image.name, self.image.name)

    def test_post_edit(self):
        form_data = {
            'text': 'Измененный текст',
        }
        self.authorized_client.post(reverse('post_edit', kwargs={
            'username': self.user.username, 'post_id': self.post.id
        }
                                            ),
                                    data=form_data
                                    )
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, form_data['text'])

    def test_new_post_create_unauthorized_user(self):
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст создает неавторизованный пользователь',
            'group': self.group.id,
        }
        self.guest_client.post(
            reverse('new_post'), data=form_data,
        )
        self.assertEqual(Post.objects.count(), tasks_count)
