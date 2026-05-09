from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import UserViewSet, RefreshTokenView, LoginView

router = SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),

    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),

] + router.urls