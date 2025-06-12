from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, RepostAPIView, UserViewSet

router = DefaultRouter()
router.register(r'careers', PostViewSet, basename='post')
router.register(r'users', UserViewSet, basename='user')
urlpatterns = [
    path('careers/<int:pk>/repost/', RepostAPIView.as_view(), name='post-repost'),
]
urlpatterns += router.urls