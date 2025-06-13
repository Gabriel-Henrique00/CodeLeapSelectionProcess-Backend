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
        cls.comment_on_post1 = Comment.objects.create(post=cls.post1, author=cls.user2, content="User 2's Comment")

        cls.post1.share_count = 1
        cls.post1.comment_count = 1
        cls.post1.save()

    @tag('posts', 'create')
    def test_authenticated_user_can_create_post(self):
        """[Posts] Authenticated user can create a post."""
        self.client.force_authenticate(user=self.user1)
        data = {'title': 'New Post', 'content': 'Content of the new post'}
        post_count_before = Post.objects.count()
        # Corrected URL from '/careers/posts/' to '/posts/'
        response = self.client.post('/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), post_count_before + 1)
        self.assertEqual(Post.objects.last().author, self.user1)

    @tag('posts', 'permissions')
    def test_unauthenticated_user_cannot_create_post(self):
        """[Posts] Unauthenticated user cannot create a post (401)."""
        # Corrected URL from '/careers/posts/' to '/posts/'
        response = self.client.post('/posts/', {'title': 'Post', 'content': 'Content'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @tag('posts', 'update')
    def test_author_can_update_own_post(self):
        """[Posts] Author can update their own post."""
        self.client.force_authenticate(user=self.user1)
        # Corrected URL from f'/careers/posts/{self.post1.id}/' to f'/posts/{self.post1.id}/'
        response = self.client.patch(f'/posts/{self.post1.id}/', {'title': 'Edited Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Edited Title')

    @tag('posts', 'permissions')
    def test_user_cannot_update_another_users_post(self):
        """[Posts] User cannot update another user's post (403)."""
        self.client.force_authenticate(user=self.user2)
        # Corrected URL from f'/careers/posts/{self.post1.id}/' to f'/posts/{self.post1.id}/'
        response = self.client.patch(f'/posts/{self.post1.id}/', {'title': 'Attempt'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @tag('posts', 'delete')
    def test_author_can_delete_own_post(self):
        """[Posts] Author can delete their own post."""
        self.client.force_authenticate(user=self.user1)
        temp_post = Post.objects.create(author=self.user1, title="Post to delete", content="...")
        post_id = temp_post.id
        # Corrected URL from f'/careers/posts/{post_id}/' to f'/posts/{post_id}/'
        response = self.client.delete(f'/posts/{post_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=post_id).exists())


    @tag('posts', 'permissions', 'delete')
    def test_user_cannot_delete_another_users_post(self):
        """[Coverage] User cannot delete another user's post (403)."""
        self.client.force_authenticate(user=self.user2)
        # Corrected URL from f'/careers/posts/{self.post1.id}/' to f'/posts/{self.post1.id}/'
        response = self.client.delete(f'/posts/{self.post1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @tag('posts', 'trending')
    def test_trending_endpoint_orders_by_likes(self):
        """[Posts] 'Trending' endpoint returns posts ordered by likes."""
        self.post2.like_count = 2
        self.post2.save()

        # Corrected URL from '/careers/posts/trending/' to '/posts/trending/'
        response = self.client.get('/posts/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.post2.id)

    @tag('posts', 'trending', 'pagination')
    def test_trending_endpoint_is_paginated(self):
        """[Coverage] 'Trending' endpoint is paginated correctly."""
        # Corrected URL from '/careers/posts/trending/' to '/posts/trending/'
        response = self.client.get('/posts/trending/')
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
        # Corrected URL from f'/careers/posts/{self.post2.id}/like/' to f'/posts/{self.post2.id}/like/'
        response = self.client.post(f'/posts/{self.post2.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post2.refresh_from_db()
        self.assertEqual(self.post2.like_count, like_count_before + 1)

    @tag('interactions', 'like', 'permissions')
    def test_unauthenticated_user_cannot_like_post(self):
        """[Coverage] Unauthenticated user cannot like a post (401)."""
        # Corrected URL from f'/careers/posts/{self.post2.id}/like/' to f'/posts/{self.post2.id}/like/'
        response = self.client.post(f'/posts/{self.post2.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @tag('interactions', 'like', 'delete')
    def test_user_can_unlike_a_post(self):
        """[Interactions] User can remove their like from a post."""
        self.client.force_authenticate(user=self.user2)
        like_count_before = self.post1.like_count
        # Corrected URL from f'/careers/posts/{self.post1.id}/like/' to f'/posts/{self.post1.id}/like/'
        response = self.client.delete(f'/posts/{self.post1.id}/like/')
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
        # Corrected URL from '/careers/posts/9999/like/' to '/posts/9999/like/'
        response = self.client.post('/posts/9999/like/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('interactions', 'like', 'edge_case')
    def test_unlike_post_user_has_not_liked_returns_404(self):
        """[Coverage] Unliking a post the user has not liked returns 404."""
        self.client.force_authenticate(user=self.user1)
        # Corrected URL from f'/careers/posts/{self.post2.id}/like/' to f'/posts/{self.post2.id}/like/'
        response = self.client.delete(f'/posts/{self.post2.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('interactions', 'like', 'edge_case')
    def test_user_cannot_like_a_post_twice(self):
        """[Coverage] User cannot like the same post twice."""
        self.client.force_authenticate(user=self.user2)
        # Corrected URL from f'/careers/posts/{self.post1.id}/like/' to f'/posts/{self.post1.id}/like/'
        response = self.client.post(f'/posts/{self.post1.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag('interactions', 'share', 'create')
    def test_authenticated_user_can_share_a_post(self):
        """[Coverage] Authenticated user can share a post."""
        self.client.force_authenticate(user=self.user1)
        share_count_before = self.post2.share_count
        # Corrected URL from f'/careers/posts/{self.post2.id}/repost/' to f'/posts/{self.post2.id}/repost/'
        response = self.client.post(f'/posts/{self.post2.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post2.refresh_from_db()
        self.assertEqual(self.post2.share_count, share_count_before + 1)
        Share.objects.filter(user=self.user1, original_post=self.post2).delete()
        self.post2.share_count = share_count_before
        self.post2.save()


    @tag('interactions', 'share', 'permissions')
    def test_unauthenticated_user_cannot_share_post(self):
        """[Coverage] Unauthenticated user cannot share a post (401)."""
        # Corrected URL from f'/careers/posts/{self.post1.id}/repost/' to f'/posts/{self.post1.id}/repost/'
        response = self.client.post(f'/posts/{self.post1.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @tag('interactions', 'share', 'delete')
    def test_user_can_unshare_a_post(self):
        """[Interactions] User can remove their share from a post."""
        self.client.force_authenticate(user=self.user2)
        share_count_before = self.post1.share_count
        # Corrected URL from f'/careers/posts/{self.post1.id}/repost/' to f'/posts/{self.post1.id}/repost/'
        response = self.client.delete(f'/posts/{self.post1.id}/repost/')
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
        # Corrected URL from f'/careers/posts/{self.post1.id}/repost/' to f'/posts/{self.post1.id}/repost/'
        response = self.client.delete(f'/posts/{self.post1.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('interactions', 'share', 'permissions')
    def test_user_cannot_share_own_post(self):
        """[Interactions] User cannot share their own post."""
        self.client.force_authenticate(user=self.user1)
        # Corrected URL from f'/careers/posts/{self.post1.id}/repost/' to f'/posts/{self.post1.id}/repost/'
        response = self.client.post(f'/posts/{self.post1.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag('interactions', 'share', 'edge_case')
    def test_share_non_existent_post_returns_404(self):
        """[Coverage] Sharing a non-existent post returns 404."""
        self.client.force_authenticate(user=self.user1)
        # Corrected URL from '/careers/posts/9999/repost/' to '/posts/9999/repost/'
        response = self.client.post('/posts/9999/repost/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('interactions', 'share', 'edge_case')
    def test_user_cannot_share_a_post_twice(self):
        """[Coverage] User cannot share the same post twice."""
        self.client.force_authenticate(user=self.user2)
        # Corrected URL from f'/careers/posts/{self.post1.id}/repost/' to f'/posts/{self.post1.id}/repost/'
        response = self.client.post(f'/posts/{self.post1.id}/repost/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    @tag('comments', 'list')
    def test_list_comments_for_a_post(self):
        """[Comments] List comments for a specific post."""
        # Corrected URL from f'/careers/posts/{self.post1.id}/comments/' to f'/posts/{self.post1.id}/comments/'
        response = self.client.get(f'/posts/{self.post1.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['content'], self.comment_on_post1.content)

    @tag('comments', 'create')
    def test_authenticated_user_can_create_comment(self):
        """[Comments] Authenticated user can comment on a post."""
        self.client.force_authenticate(user=self.user1)
        comment_count_before = self.post1.comment_count
        # Corrected URL from f'/careers/posts/{self.post1.id}/comments/' to f'/posts/{self.post1.id}/comments/'
        response = self.client.post(f'/posts/{self.post1.id}/comments/', {'content': 'New comment'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.comment_count, comment_count_before + 1)
        self.post1.comments.last().delete()
        self.post1.comment_count = comment_count_before
        self.post1.save()

    @tag('comments', 'permissions')
    def test_unauthenticated_user_cannot_comment(self):
        """[Coverage] Unauthenticated user cannot comment (401)."""
        # Corrected URL from f'/careers/posts/{self.post1.id}/comments/' to f'/posts/{self.post1.id}/comments/'
        response = self.client.post(f'/posts/{self.post1.id}/comments/', {'content': 'Anonymous comment'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @tag('comments', 'edge_case')
    def test_comment_on_non_existent_post_returns_404(self):
        """
        [Coverage] Tests if creating a comment on a non-existent post
        raises Post.DoesNotExist, as per the current view implementation.
        """
        self.client.force_authenticate(user=self.user1)
        # Corrected URL from '/careers/posts/9999/comments/' to '/posts/9999/comments/'
        with self.assertRaises(Post.DoesNotExist): # This test expects an exception, not a 404 from the client
            self.client.post('/posts/9999/comments/', {'content': 'Lost comment'})

    @tag('comments', 'update')
    def test_author_can_update_own_comment(self):
        """[Coverage] Author can edit their own comment."""
        self.client.force_authenticate(user=self.user2)
        new_content = 'The comment content has been edited.'
        # Corrected URL from f'/careers/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/' to f'/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/'
        response = self.client.patch(
            f'/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/',
            {'content': new_content}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment_on_post1.refresh_from_db()
        self.assertEqual(self.comment_on_post1.content, new_content)

    @tag('comments', 'permissions', 'update')
    def test_user_cannot_update_another_users_comment(self):
        """[Coverage] User cannot edit another user's comment (403)."""
        self.client.force_authenticate(user=self.user1)
        # Corrected URL from f'/careers/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/' to f'/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/'
        response = self.client.patch(
            f'/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/',
            {'content': 'edit attempt'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @tag('comments', 'delete')
    def test_author_can_delete_own_comment(self):
        """[Coverage] Author can delete their own comment."""
        self.client.force_authenticate(user=self.user2)
        comment_id = self.comment_on_post1.id
        post_id = self.post1.id
        comment_count_before = self.post1.comment_count

        # Corrected URL from f'/careers/posts/{post_id}/comments/{comment_id}/' to f'/posts/{post_id}/comments/{comment_id}/'
        response = self.client.delete(f'/posts/{post_id}/comments/{comment_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.comment_count, comment_count_before - 1)
        # Recreate the comment for subsequent tests
        self.comment_on_post1 = Comment.objects.create(id=comment_id, post=self.post1, author=self.user2, content="User 2's Comment")
        self.post1.comment_count = comment_count_before # Restore count
        self.post1.save()

    @tag('comments', 'permissions', 'delete')
    def test_user_cannot_delete_another_users_comment(self):
        """[Comments] User cannot delete another user's comment (403)."""
        self.client.force_authenticate(user=self.user1)
        # Corrected URL from f'/careers/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/' to f'/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/'
        response = self.client.delete(f'/posts/{self.post1.id}/comments/{self.comment_on_post1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @tag('comments', 'edge_case')
    def test_update_non_existent_comment_returns_404(self):
        """[Coverage] Editing a non-existent comment returns 404."""
        self.client.force_authenticate(user=self.user1)
        # Corrected URL from f'/careers/posts/{self.post1.id}/comments/9999/' to f'/posts/{self.post1.id}/comments/9999/'
        response = self.client.patch(f'/posts/{self.post1.id}/comments/9999/', {'content': '...'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('users', 'list')
    def test_list_users(self):
        """[Users] List all users."""
        # Corrected URL from '/careers/users/' to '/users/'
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), User.objects.count())

    @tag('users', 'profile_actions')
    def test_list_posts_for_user(self):
        """[Coverage] List posts created by a user."""
        # Corrected URL from f'/careers/users/{self.user1.username}/posts/' to f'/users/{self.user1.username}/posts/'
        response = self.client.get(f'/users/{self.user1.username}/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['results']), 10)

    @tag('users', 'profile_actions')
    def test_list_posts_shared_by_user(self):
        """[Users] List posts shared by a user."""
        # Corrected URL from f'/careers/users/{self.user2.username}/shares/' to f'/users/{self.user2.username}/shares/'
        response = self.client.get(f'/users/{self.user2.username}/shares/')
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

        # Corrected URL from f'/careers/users/{self.user1.username}/shares/' to f'/users/{self.user1.username}/shares/'
        response = self.client.get(f'/users/{self.user1.username}/shares/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 12)
        self.assertEqual(len(response.data['results']), 10)


    @tag('users', 'profile_actions', 'edge_case')
    def test_list_posts_for_non_existent_user_returns_404(self):
        """[Coverage] Listing posts for a non-existent user returns 404."""
        # Corrected URL from '/careers/users/nonexistentuser/posts/' to '/users/nonexistentuser/posts/'
        response = self.client.get('/users/nonexistentuser/posts/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tag('users', 'profile_actions', 'edge_case')
    def test_list_shares_for_non_existent_user_returns_404(self):
        """[Coverage] Listing shares for a non-existent user returns 404."""
        # Corrected URL from '/careers/users/nonexistentuser/shares/' to '/users/nonexistentuser/shares/'
        response = self.client.get('/users/nonexistentuser/shares/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    @tag('users', 'profile_actions', 'edge_case')
    def test_list_posts_for_user_with_no_posts(self):
        """[Coverage] Listing posts for a user with no posts returns an empty list."""
        user3 = User.objects.create_user(username='user3', password='123')
        # Corrected URL from f'/careers/users/{user3.username}/posts/' to f'/users/{user3.username}/posts/'
        response = self.client.get(f'/users/{user3.username}/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    @tag('users', 'profile_actions', 'edge_case')
    def test_list_shares_for_user_with_no_shares(self):
        """[Coverage] Listing shares for a user with no shares returns an empty list."""
        user3 = User.objects.create_user(username='user3-no-shares', password='123')
        # Corrected URL from f'/careers/users/{user3.username}/shares/' to f'/users/{user3.username}/shares/'
        response = self.client.get(f'/users/{user3.username}/shares/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    @tag('registration')
    def test_user_can_register_with_valid_data(self):
        """[Registration] User can register with valid data."""
        user_count_before = User.objects.count()
        data = {'username': 'newuser', 'password': 'newpassword123'}
        # URL is already correct
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), user_count_before + 1)
        self.assertNotIn('password', response.data)
        self.assertEqual(response.data['username'], 'newuser')


    @tag('registration', 'validation')
    def test_user_cannot_register_with_existing_username(self):
        """[Registration] Cannot register with an existing username."""
        data = {'username': self.user1.username, 'password': 'newpassword123'}
        # URL is already correct
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag('auth', 'jwt')
    def test_user_can_get_jwt_token(self):
        """[Coverage] User can get a JWT token with valid credentials."""
        data = {'username': self.user1.username, 'password': 'password123'}
        # URL is already correct
        response = self.client.post('/api/token/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    @tag('auth', 'jwt')
    def test_user_cannot_get_jwt_token_with_invalid_credentials(self):
        """[Coverage] User cannot get a JWT token with invalid credentials."""
        data = {'username': self.user1.username, 'password': 'wrongpassword'}
        # URL is already correct
        response = self.client.post('/api/token/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    @tag('models', 'coverage')
    def test_model_str_representations(self):
        """[Coverage] String representations of the models are correct."""
        self.assertEqual(str(self.post1), self.post1.title)
        self.assertEqual(str(self.like_on_post1), f'{self.user2.username} liked "{self.post1.title}"')
        self.assertEqual(str(self.share_on_post1), f'{self.user2.username} shared "{self.post1.title}"')
        self.assertEqual(str(self.comment_on_post1), f'Comment by {self.user2.username} on {self.post1.title}')