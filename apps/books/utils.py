from apps.loans.models import SystemLogs


def perform_logging(serializer, instance, action_type, target_type, details=None):
    """
    Serializer'lar uchun umumiy log yozish funksiyasi.
    """
    request = serializer.context.get("request")

    # Agar details berilmagan bo'lsa, avtomatik yaratish
    if not details:
        details = f"Amal: {action_type.label}. Obyekt: {str(instance)}"

    SystemLogs.objects.create(
        admin=request.user if request and request.user.is_authenticated else None,
        action=action_type,
        target=instance.id,
        target_type=target_type,
        details=details
    )