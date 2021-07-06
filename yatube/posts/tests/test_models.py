from django.test import TestCase

from ..models import Group, Post, User


class TaskModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(author=cls.user)
        cls.group = Group.objects.create()

    def test_object_name_is_title_field(self):
        post = TaskModelTest.post
        expected_object_name = post.text[15:]
        self.assertEqual(expected_object_name, str(post))

    def test_object_name_is_title_field_group(self):
        group = TaskModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
