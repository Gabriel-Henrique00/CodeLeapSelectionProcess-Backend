from rest_framework import viewsets
from .models import Post
from .serializers import PostSerializer
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['username', 'title']
    filterset_fields = ['created_datetime']
