from rest_framework import permissions
from .models import User


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Faqat admin va super admin uchun ruxsat
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN})

class IsLibrarian(permissions.BasePermission):
    """
    Faqat kutubxonaxhi (Admin va Super Admin) uchun ruxsat
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN})

class IsSelfOrAdmin(permissions.BasePermission):
    """
    Faqat o'z profilini ko'rish yoki adminlar uchun ruxsat
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        if request.user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
            return True
        return obj == request.user
    
class ReadOnlyOrLibrarian(permissions.BasePermission):
    """
    Faqat o'qish uchun ruxsat yoki kutubxonaxhi (Admin va Super Admin) uchun ruxsat
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        
        return bool(request.user and request.user.is_authenticated and request.user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN})