from rest_framework import viewsets, permissions
from .models import Post
from .serializers import PostSerializer
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
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