from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer, UserShortSerializer
from drf_spectacular.utils import extend_schema


# Login viewni o'rab olamiz va tag beramiz
@extend_schema(tags=['Auth'])
class LoginView(TokenObtainPairView):
    pass

# Refresh viewni o'rab olamiz va tag beramiz
@extend_schema(tags=['Auth'])
class RefreshTokenView(TokenRefreshView):
    pass

@extend_schema(tags=['Users'])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            # Yangi foydalanuvchi registratsiya qilishi uchun hamma ruxsat (AllowAny)
            return [permissions.AllowAny()]
        # Qolgan hamma narsa uchun login qilish shart
        return [permissions.IsAuthenticated()]

    # Faqat adminlar hamma userni ko'ra oladi lekin har bir user o'z profilini ko'radi
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserShortSerializer(request.user)
        return Response(serializer.data)