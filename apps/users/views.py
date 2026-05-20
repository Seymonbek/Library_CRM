from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.users.permissions import IsAdminOrSuperAdmin

from .models import User
from .serializers import PhoneTokenObtainPairSerializer, UserAdminSerializer, UserProfileSerializer, UserSelfUpdateSerializer, UserRegistrationSerializer, UserShortSerializer
from drf_spectacular.utils import extend_schema


# Login viewni o'rab olamiz va tag beramiz
@extend_schema(tags=['Auth'])
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