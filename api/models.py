from django.db import models
from django.contrib.auth import get_user_model

class Post(models.Model):
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='posts'
    )
    created_datetime = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    share_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_datetime']


class Share(models.Model):
    """Representa a ação de um usuário compartilhando um post."""
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='shares'
    )
    original_post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='shared_by'
    )
    created_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'original_post')
        ordering = ['-created_datetime']

    def __str__(self):
        return f'{self.user.username} shared "{self.original_post.title}"'