from django.db import transaction
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Share, Like, Comment
from .serializers import (PostSerializer,UserSerializer,ShareSerializer,LikeSerializer,CommentSerializer)
from .permissions import IsAuthorOrReadOnly


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().prefetch_related('comments', 'comments__author')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['author__username', 'title']
    filterset_fields = ['created_datetime']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        trending_posts = self.get_queryset().order_by('-like_count', '-created_datetime')
        page = self.paginate_queryset(trending_posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(trending_posts, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

    @action(detail=True, methods=['get'])
    def posts(self, request, username=None):
        user = self.get_object()
        user_posts = user.posts.all()
        page = self.paginate_queryset(user_posts)
        if page is not None:
            serializer = PostSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PostSerializer(user_posts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def shares(self, request, username=None):
        user = self.get_object()
        user_shares = user.shares.all()
        page = self.paginate_queryset(user_shares)
        if page is not None:
            serializer = ShareSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ShareSerializer(user_shares, many=True)
        return Response(serializer.data)


class UserCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class RepostAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        try:
            post_to_share = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if post_to_share.author == request.user:
            return Response({"error": "You cannot share your own post."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            share, created = Share.objects.get_or_create(
                user=request.user,
                original_post=post_to_share
            )
            if not created:
                return Response({"error": "You have already shared this post."}, status=status.HTTP_400_BAD_REQUEST)
            post_to_share.share_count += 1
            post_to_share.save(update_fields=['share_count'])
        return Response(ShareSerializer(share).data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        try:
            post_to_unshare = Post.objects.get(pk=pk)
            with transaction.atomic():
                share = Share.objects.get(user=request.user, original_post=post_to_unshare)
                share.delete()
                if post_to_unshare.share_count > 0:
                    post_to_unshare.share_count -= 1
                    post_to_unshare.save(update_fields=['share_count'])
                return Response(status=status.HTTP_204_NO_CONTENT)
        except (Post.DoesNotExist, Share.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)


class LikePostAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        try:
            post_to_like = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            like, created = Like.objects.get_or_create(
                user=request.user,
                post=post_to_like
            )
            if not created:
                return Response({"error": "You have already liked this post."}, status=status.HTTP_400_BAD_REQUEST)
            post_to_like.like_count += 1
            post_to_like.save(update_fields=['like_count'])

        return Response(LikeSerializer(like).data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        try:
            post_to_unlike = Post.objects.get(pk=pk)
            with transaction.atomic():
                like = Like.objects.get(user=request.user, post=post_to_unlike)
                like.delete()
                if post_to_unlike.like_count > 0:
                    post_to_unlike.like_count -= 1
                    post_to_unlike.save(update_fields=['like_count'])
                return Response(status=status.HTTP_204_NO_CONTENT)
        except (Post.DoesNotExist, Like.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['post_pk'])
    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['post_pk'])
        with transaction.atomic():
            serializer.save(author=self.request.user, post=post)
            post.comment_count += 1
            post.save(update_fields=['comment_count'])

    def perform_destroy(self, instance):
        post = instance.post
        with transaction.atomic():
            instance.delete()
            if post.comment_count > 0:
                post.comment_count -= 1
                post.save(update_fields=['comment_count'])