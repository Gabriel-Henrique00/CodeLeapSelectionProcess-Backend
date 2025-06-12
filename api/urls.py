from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    PostViewSet,UserViewSet,RepostAPIView,LikePostAPIView,CommentViewSet)
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'careers', PostViewSet, basename='post')
posts_router = routers.NestedDefaultRouter(router, r'careers', lookup='post')
posts_router.register(r'comments', CommentViewSet, basename='post-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(posts_router.urls)),
    path('careers/<int:pk>/repost/', RepostAPIView.as_view(), name='post-repost'),
    path('careers/<int:pk>/like/', LikePostAPIView.as_view(), name='post-like'),
]