from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import UserViewSet, RefreshTokenView, LoginView, TelegramRegisterView, TelegramLoginView

router = SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Web login (admin/super_admin — parol bilan)
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),

    # Telegram auth (bot foydalanuvchilari — parolsiz)
    path('telegram/register/', TelegramRegisterView.as_view(), name='telegram_register'),
    path('telegram/login/', TelegramLoginView.as_view(), name='telegram_login'),

] + router.urls
