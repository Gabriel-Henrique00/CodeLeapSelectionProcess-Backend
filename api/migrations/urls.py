from rest_framework.routers import DefaultRouter
from api.views import PostViewSet

router = DefaultRouter()
router.register(r'', PostViewSet, basename='post')
urlpatterns = router.urls