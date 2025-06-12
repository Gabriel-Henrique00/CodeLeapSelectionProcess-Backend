from rest_framework import serializers
from .models import Post
from django.contrib.auth.models import User
from .models import Post, Share

class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Post
        fields = ['id', 'author_username', 'created_datetime', 'title', 'content', 'share_count']
        read_only_fields = ['id', 'author_username', 'created_datetime', 'share_count']

class ShareSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    original_post = PostSerializer(read_only=True)

    class Meta:
        model = Share
        fields = ['id', 'user_username', 'created_datetime', 'original_post']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user