from django.db import transaction
from rest_framework import viewsets, permissions, generics, status
from django.contrib.auth.models import User
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from .models import Post, Share
from .serializers import PostSerializer, UserSerializer, ShareSerializer
from .permissions import IsAuthorOrReadOnly

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['author__username', 'title']
    filterset_fields = ['created_datetime']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


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