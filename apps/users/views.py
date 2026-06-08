from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.users.permissions import IsAdminOrSuperAdmin

from .models import User
from .serializers import (
    PhoneTokenObtainPairSerializer, UserAdminSerializer, UserProfileSerializer,
    UserSelfUpdateSerializer, UserRegistrationSerializer, UserShortSerializer,
    TelegramRegisterSerializer, TelegramLoginSerializer,
)
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers


# Login viewni o'rab olamiz va tag beramiz
@extend_schema(
    tags=['Auth'],
    responses={
        200: inline_serializer(
            name='LoginResponse',
            fields={
                'refresh': drf_serializers.CharField(),
                'access': drf_serializers.CharField(),
                'user': UserShortSerializer(),
            }
        )
    }
)
class LoginView(TokenObtainPairView):
    """
    Foydalanuvchi login qilishi va JWT token olishi uchun API.
    Username va Password yuboriladi.
    """

    serializer_class = PhoneTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


# Refresh viewni o'rab olamiz va tag beramiz
@extend_schema(tags=['Auth'])
class RefreshTokenView(TokenRefreshView):
    """
    Eski refresh tokenni berib yangi access token olish API.
    """
    permission_classes = [permissions.AllowAny]


# ──── TELEGRAM AUTH (Bot uchun parolsiz) ───────────────────

@extend_schema(tags=['Telegram Auth'])
class TelegramRegisterView(APIView):
    """
    Telegram bot orqali ro'yxatdan o'tish — parolsiz.
    telegram_id, phone_number, first_name, last_name yuboriladi.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TelegramRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.to_representation(user), status=status.HTTP_201_CREATED)


@extend_schema(tags=['Telegram Auth'])
class TelegramLoginView(APIView):
    """
    Telegram bot orqali login — faqat telegram_id yuboriladi.
    Agar user mavjud bo'lsa — JWT token qaytaradi (parolsiz).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TelegramLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

@extend_schema(tags=['Users'])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")

    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
            return self.queryset
        
        return self.queryset.filter(pk=user.pk)

    def get_serializer_class(self):
        user = getattr(self.request, "user", None)
        is_admin = bool(
            user
            and user.is_authenticated
            and user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN}
        )

        if self.action == "create":
            return UserRegistrationSerializer

        if self.action in ["update", "partial_update"]:
            if is_admin:
                return UserAdminSerializer
            return UserSelfUpdateSerializer

        if is_admin:
            return UserAdminSerializer

        return UserProfileSerializer

    def get_permissions(self):
        if self.action == 'create':
            # Yangi foydalanuvchi registratsiya qilishi uchun hamma ruxsat (AllowAny)
            return [permissions.AllowAny()]
        # Qolgan hamma narsa uchun login qilish shart
        if self.action in ['list', 'destroy']:
            # Faqat admin va super admin hamma userlarni ko'ra oladi va o'chira oladi
            return [IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]

    # Faqat adminlar hamma userni ko'ra oladi lekin har bir user o'z profilini ko'radi
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserProfileSerializer(request.user, context=self.get_serializer_context())
        return Response(serializer.data)