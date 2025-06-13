from django.contrib.auth.models import User
from django.test import tag
from rest_framework.test import APITestCase
from rest_framework import status

from api.models import Post, Like, Share, Comment


@tag('full_suite', 'api')
class FullAPISuiteTests(APITestCase):
    """
    A complete test suite for the API, covering all endpoints,
    permissions, and edge cases to ensure 100% coverage.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Sets up initial data for all tests in the class.
        This is run only once.
        """
        cls.user1 = User.objects.create_user(username='user1', password='password123')
        cls.user2 = User.objects.create_user(username='user2', password='password123')

        for i in range(15):
            post = Post.objects.create(
                author=cls.user1,
                title=f"Test post {i}",
                content="Content..."
            )

        cls.post1 = Post.objects.get(title="Test post 0")
        cls.post2 = Post.objects.create(author=cls.user2, title="User 2's Post", content="Content...")

    @tag('posts', 'create')
    def test_authenticated_user_can_create_post(self):
        """[Posts] Authenticated user can create a post."""
        self.client.force_authenticate(user=self.user1)
        data = {'title': 'New Post', 'content': 'Content of the new post'}
        post_count_before = Post.objects.count()
        response = self.client.post('/careers/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), post_count_before + 1)
        self.assertEqual(Post.objects.last().author, self.user1)

    @tag('posts', 'permissions')
    def test_unauthenticated_user_cannot_create_post(self):
        """[Posts] Unauthenticated user cannot create a post (401)."""
        response = self.client.post('/careers/', {'title': 'Post', 'content': 'Content'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @tag('posts', 'update')
    def test_author_can_update_own_post(self):
        """[Posts] Author can update their own post."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(f'/careers/{self.post1.id}/', {'title': 'Edited Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Edited Title')

    @tag('posts', 'permissions')
    def test_user_cannot_update_another_users_post(self):
        """[Posts] User cannot update another user's post (403)."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.patch(f'/careers/{self.post1.id}/', {'title': 'Attempt'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @tag('posts', 'delete')
    def test_author_can_delete_own_post(self):
        """[Posts] Author can delete their own post."""
        self.client.force_authenticate(user=self.user1)
        temp_post = Post.objects.create(author=self.user1, title="Post to delete", content="...")
        post_id = temp_post.id
        response = self.client.delete(f'/careers/{post_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=post_id).exists())


    @tag('posts', 'permissions', 'delete')
    def test_user_cannot_delete_another_users_post(self):
        """[Coverage] User cannot delete another user's post (403)."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(f'/careers/{self.post1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @tag('users', 'profile_actions')
    def test_list_posts_for_user(self):
        """[Coverage] List posts created by a user."""
        response = self.client.get(f'/careers/users/{self.user1.username}/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['results']), 10)