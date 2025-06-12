import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from faker import Faker

from api.models import Post, Like, Share, Comment


class Command(BaseCommand):
    help = 'Populates the database with sample data'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Cleaning old data...")
        Comment.objects.all().delete()
        Share.objects.all().delete()
        Like.objects.all().delete()
        Post.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        fake = Faker()

        self.stdout.write("Creating users...")
        users = []
        for _ in range(5):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='123'
            )
            users.append(user)

        self.stdout.write("Creating posts...")
        posts = []
        for _ in range(25):
            post = Post.objects.create(
                author=random.choice(users),
                title=fake.sentence(nb_words=6),
                content=' '.join(fake.paragraphs(nb=3))
            )
            posts.append(post)

        self.stdout.write("Creating interactions...")
        for post in posts:
            interacting_users = random.sample(users, random.randint(0, len(users)))

            for user in interacting_users:
                if random.random() < 0.5:
                    Like.objects.get_or_create(user=user, post=post)
                if random.random() < 0.2 and user != post.author:
                    Share.objects.get_or_create(user=user, original_post=post)
                if random.random() < 0.3:
                    Comment.objects.create(
                        post=post,
                        author=user,
                        content=fake.paragraph(nb_sentences=2)
                    )
        self.stdout.write("Updating counters...")
        for post in Post.objects.all():
            post.like_count = post.likes.count()
            post.share_count = post.shared_by.count()
            post.comment_count = post.comments.count()
            post.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated the database!'))