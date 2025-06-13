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
            Like.objects.create(user=cls.user2, post=post)
            post.like_count = 1
            post.save()


        cls.post1 = Post.objects.get(title="Test post 0")
        cls.post2 = Post.objects.create(author=cls.user2, title="User 2's Post", content="Content...")

        cls.like_on_post1 = Like.objects.get(user=cls.user2, post=cls.post1)
        cls.share_on_post1 = Share.objects.create(user=cls.user2, original_post=cls.post1)

        cls.post1.share_count = 1
        cls.post1.save()

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

    @tag('posts', 'trending')
    def test_trending_endpoint_orders_by_likes(self):
        """[Posts] 'Trending' endpoint returns posts ordered by likes."""
        self.post2.like_count = 2
        self.post2.save()

        response = self.client.get('/careers/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.post2.id)

    @tag('posts', 'trending', 'pagination')
    def test_trending_endpoint_is_paginated(self):
        """[Coverage] 'Trending' endpoint is paginated correctly."""
        response = self.client.get('/careers/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], Post.objects.count())
        self.assertEqual(len(response.data['results']), 10)


    @tag('interactions', 'like', 'create')
    def test_authenticated_user_can_like_a_post(self):
        """[Interactions] Authenticated user can like a post."""
        self.client.force_authenticate(user=self.user1)
        like_count_before = self.post2.like_count
        response = self.client.post(f'/careers/{self.post2.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post2.refresh_from_db()
        self.assertEqual(self.post2.like_count, like_count_before + 1)

    @tag('interactions', 'like', 'permissions')
    def test_unauthenticated_user_cannot_like_post(self):
        """[Coverage] Unauthenticated user cannot like a post (401)."""
        response = self.client.post(f'/careers/{self.post2.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @tag('interactions', 'like', 'delete')
    def test_user_can_unlike_a_post(self):
        """[Interactions] User can remove their like from a post."""
        self.client.force_authenticate(user=self.user2)
        like_count_before = self.post1.like_count
        response = self.client.delete(f'/careers/{self.post1.id}/like/')
        self.post1.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.post1.like_count, like_count_before - 1)
        Like.objects.create(user=self.user2, post=self.post1)
        self.post1.like_count = like_count_before
        self.post1.save()

    @tag('interactions', 'like', 'edge_case')
    def test_like_non_existent_post_returns_404(self):
        """[Coverage] Liking a non-existent post returns 404."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/careers/9999/like/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('interactions', 'like', 'edge_case')
    def test_unlike_post_user_has_not_liked_returns_404(self):
        """[Coverage] Unliking a post the user has not liked returns 404."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(f'/careers/{self.post2.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('interactions', 'like', 'edge_case')
    def test_user_cannot_like_a_post_twice(self):
        """[Coverage] User cannot like the same post twice."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f'/careers/{self.post1.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag('interactions', 'share', 'create')
    def test_authenticated_user_can_share_a_post(self):
        """[Coverage] Authenticated user can share a post."""
        self.client.force_authenticate(user=self.user1)
        share_count_before = self.post2.share_count
        response = self.client.post(f'/careers/{self.post2.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post2.refresh_from_db()
        self.assertEqual(self.post2.share_count, share_count_before + 1)
        Share.objects.filter(user=self.user1, original_post=self.post2).delete()
        self.post2.share_count = share_count_before
        self.post2.save()


    @tag('interactions', 'share', 'permissions')
    def test_unauthenticated_user_cannot_share_post(self):
        """[Coverage] Unauthenticated user cannot share a post (401)."""
        response = self.client.post(f'/careers/{self.post1.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @tag('interactions', 'share', 'delete')
    def test_user_can_unshare_a_post(self):
        """[Interactions] User can remove their share from a post."""
        self.client.force_authenticate(user=self.user2)
        share_count_before = self.post1.share_count
        response = self.client.delete(f'/careers/{self.post1.id}/repost/')
        self.post1.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.post1.share_count, share_count_before - 1)
        Share.objects.create(user=self.user2, original_post=self.post1)
        self.post1.share_count = share_count_before
        self.post1.save()

    @tag('interactions', 'share', 'edge_case')
    def test_unshare_post_user_has_not_shared_returns_404(self):
        """[Coverage] Unsharing a post the user has not shared returns 404."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(f'/careers/{self.post1.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('interactions', 'share', 'permissions')
    def test_user_cannot_share_own_post(self):
        """[Interactions] User cannot share their own post."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f'/careers/{self.post1.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag('interactions', 'share', 'edge_case')
    def test_share_non_existent_post_returns_404(self):
        """[Coverage] Sharing a non-existent post returns 404."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/careers/9999/repost/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('interactions', 'share', 'edge_case')
    def test_user_cannot_share_a_post_twice(self):
        """[Coverage] User cannot share the same post twice."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f'/careers/{self.post1.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    @tag('users', 'profile_actions')
    def test_list_posts_for_user(self):
        """[Coverage] List posts created by a user."""
        response = self.client.get(f'/careers/users/{self.user1.username}/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['results']), 10)

    @tag('users', 'profile_actions')
    def test_list_posts_shared_by_user(self):
        """[Users] List posts shared by a user."""
        response = self.client.get(f'/careers/users/{self.user2.username}/shares/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['original_post']['id'], self.post1.id)

    @tag('users', 'profile_actions', 'pagination')
    def test_user_shares_endpoint_is_paginated(self):
        """[Coverage] User shares endpoint is paginated."""
        user2_posts = []
        for i in range(12):
            user2_posts.append(Post.objects.create(author=self.user2, title=f"User2's post {i}"))
        for post in user2_posts:
            Share.objects.create(user=self.user1, original_post=post)

        response = self.client.get(f'/careers/users/{self.user1.username}/shares/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 12)
        self.assertEqual(len(response.data['results']), 10)

    @tag('models', 'coverage')
    def test_model_str_representations(self):
        """[Coverage] String representations of the models are correct."""
        self.assertEqual(str(self.post1), self.post1.title)
        self.assertEqual(str(self.like_on_post1), f'{self.user2.username} liked "{self.post1.title}"')
        self.assertEqual(str(self.share_on_post1), f'{self.user2.username} shared "{self.post1.title}"')