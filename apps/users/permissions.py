from rest_framework import permissions

class IsLibrarian(permissions.BasePermission):
    """
    Faqat kutubxonaxhi (Admin va Super Admin) uchun ruxsat
    """

    def has_permission(self, request, view):
        # Login qilgan bo'lishi shart
        if not request.user or not request.user.is_authenticated:
            return False

        # Roli Admin yoki Super Admin bo'lishi shart
        return request.user.role in ['admin', 'superadmin']

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Ma'lumotni faqat egasi yoki admin ko'ra oladi
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['admin', 'superadmin']:
            return True
        return obj.user == request.user